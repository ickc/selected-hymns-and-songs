"""Where each hymn is printed in the two scanned editions.

``scan/{en,zh}.csv`` are copied unedited from the project that infers them, so
this reads their contract rather than a shape convenient here: one row per
*segment*, front matter and post-hymn matter included, both page bounds
inclusive and one-based, and an absent hymn written as two empty fields.

Only the hymns are wanted, and only their pages.  Everything else this module
does is refusing to guess: a half-empty row, a backwards interval and a missing
segment are all errors rather than a hymn quietly published without its page.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import os
from pathlib import Path
import shutil

from .model import LANGUAGE_ORDER


# The two editions the hymnal was scanned as, in the order a page shows them.
SCAN_LANGUAGES = tuple(sorted(LANGUAGE_ORDER, key=LANGUAGE_ORDER.__getitem__))
# Segment 0 is the front matter and the last segment is the post-hymn matter.
# Neither is a hymn, and neither has an image carried in `scan/`.
FRONT_MATTER = 0
COLUMNS = ("segment", "start_page", "end_page")


@dataclass(frozen=True)
class Edition:
    """One language edition: the pages each hymn in it is printed on."""

    language: str
    #: Hymn number to its inclusive page range, absent hymns omitted entirely.
    hymns: dict[int, tuple[int, int]]

    def pages(self, number: int) -> list[int]:
        """Return the pages hymn ``number`` occupies, empty when it is absent.

        The range is inclusive at both ends and consecutive hymns may share a
        page, so a page returned here can carry a neighbouring hymn too.  It is
        shown whole rather than cropped: what is around a hymn on its page is
        part of reading the page.
        """

        bounds = self.hymns.get(number)
        return [] if bounds is None else list(range(bounds[0], bounds[1] + 1))


def read_edition(path: Path, language: str) -> Edition:
    """Read one segmentation CSV as the hymns of a language edition."""

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError(f"{path}: columns must be {', '.join(COLUMNS)}")
        rows = list(reader)

    hymns: dict[int, tuple[int, int]] = {}
    for index, row in enumerate(rows):
        try:
            segment = int(row["segment"])
        except (TypeError, ValueError):
            raise ValueError(f"{path}: segment {row['segment']!r} is not a number")
        # The file describes every segment in order, so its own row numbering
        # is the check: a gap or a reordering would silently move every hymn
        # after it onto the wrong pages.
        if segment != index:
            raise ValueError(f"{path}: expected segment {index}, found {segment}")
        start, end = row["start_page"], row["end_page"]
        if bool(start) != bool(end):
            raise ValueError(f"{path}: segment {segment} has one page bound of two")
        # The last segment is the post-hymn matter; segment 0 the front matter.
        if not start or segment in (FRONT_MATTER, len(rows) - 1):
            continue
        first, last = int(start), int(end)
        if first < 1 or last < first:
            raise ValueError(f"{path}: segment {segment} spans {first} to {last}")
        hymns[segment] = (first, last)

    if not hymns:
        raise ValueError(f"{path}: no hymn is present in this edition")
    return Edition(language, hymns)


def read_editions(directory: Path) -> dict[str, Edition]:
    """Read both editions from a ``scan/`` directory."""

    return {
        language: read_edition(directory / f"{language}.csv", language)
        for language in SCAN_LANGUAGES
    }


def missing_images(editions: dict[str, Edition], directory: Path) -> list[Path]:
    """Return the page images the editions reference and the directory lacks.

    The images are copied in from another project rather than generated here,
    so the two can disagree.  A hymn rendered against a missing image would
    show a broken picture on the one page whose whole purpose is that image.
    """

    absent: list[Path] = []
    for language, edition in editions.items():
        for number in sorted(edition.hymns):
            for page in edition.pages(number):
                path = directory / language / f"{page}.png"
                if not path.exists():
                    absent.append(path)
    return sorted(set(absent))


def stage(scans: Path, output: Path) -> int:
    """Link every scanned page into ``output/scan``, returning how many.

    The scans are 45 MB of PNG and sit outside the Quarto project on purpose.
    Inside it, each of the parallel workers in ``build_site`` would be handed
    its own copy of all of them to render eight hymns against, and every render
    and preview reload would walk 1,776 images looking for input.

    Nothing about them needs Quarto: they are published exactly as they are
    checked in. So they are linked into the rendered site afterwards instead,
    which is one filesystem operation each and no copying at all where the
    repository and its output share a filesystem.
    """

    staged = 0
    for language in SCAN_LANGUAGES:
        source = scans / language
        if not source.is_dir():
            raise RuntimeError(f"no scanned pages in {source}")
        destination = output / "scan" / language
        destination.mkdir(parents=True, exist_ok=True)
        for path in source.glob("*.png"):
            target = destination / path.name
            if target.exists():
                target.unlink()
            try:
                os.link(path, target)
            except OSError:
                # A separate filesystem for the output, or one without hard
                # links. Copying is slower and correct.
                shutil.copy2(path, target)
            staged += 1
    return staged
