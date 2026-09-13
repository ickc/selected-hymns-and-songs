"""Give each hymn the tune the English edition sets it to.

The tune is not printed over the hymn. A page carries the subject, the meter,
the number and the credits; where a hymn has two settings it says *First tune*
and *Second tune* over the staves and still does not name either. The name is
in the back matter, and it is there **twice**:

- *Alphabetical Index of Tunes*, ``en/895``-``en/898``: tune, then the hymns
  set to it.
- *Metrical Index of Tunes*, ``en/899``-``en/904``: meter, then tune, then the
  same hymns.

Two printings of one relation is what makes this table trustworthy. Each index
was read on its own and the two were then required to agree exactly, hymn for
hymn and letter for letter. They did, on 632 hymns outright; the 132 where the
scan of one page disagreed with the scan of the other were settled by reading
the printed page, and every one of them turned out to be the scan misreading a
name both indexes in fact print alike. What comes out is 765 pairs covering
hymns 1 to 764 with no hymn missing and none past the English edition's end --
a shape neither index states and neither could have been rigged to produce.

Only hymn 146 carries two tunes, in the order the indexes number them:
``Azmon (1)`` and ``Lyngham (2)``, which is the ``First tune`` and ``Second
tune`` its page prints. The field is therefore a name or an ordered list of
them, and never localized: the Chinese edition names no tune at all.

Applying it is a preprocessing step over ``data/``, not part of building the
site, exactly as ``categories`` and ``titles`` are.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from itertools import repeat
from pathlib import Path

from .environment import available_cpu_count
from .model import Hymn


HEADER = ("hymn", "tune")


def read_tunes(path: Path) -> dict[int, list[str]]:
    """Read the hymn-to-tune table, keeping the order a hymn's tunes are in.

    One row per pair rather than one per hymn, because that is the shape both
    printed indexes have and the shape a hand edit cannot get wrong: adding a
    second tune to a hymn is adding a line under it.
    """

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or tuple(field.strip() for field in lines[0].split("\t")) != HEADER:
        raise ValueError(f"{path} must begin with the header {chr(9).join(HEADER)}")
    tunes: dict[int, list[str]] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("\t")]
        if len(fields) != 2 or not all(fields):
            raise ValueError(f"{path}: line {line_number} is not two non-empty fields")
        number, tune = fields
        if not number.isdecimal():
            raise ValueError(f"{path}: line {line_number} is not numbered by a hymn")
        names = tunes.setdefault(int(number), [])
        if tune in names:
            raise ValueError(
                f"{path}: line {line_number} sets hymn {number} to {tune!r} twice"
            )
        names.append(tune)
    if sorted(tunes) != list(tunes):
        raise ValueError(f"{path} must be in hymn order")
    return tunes


def write_tunes(tunes: Mapping[int, Sequence[str]], path: Path) -> None:
    """Write the table, for regenerating it rather than editing it by hand."""

    body = "".join(
        f"{number}\t{tune}\n" for number in sorted(tunes) for tune in tunes[number]
    )
    path.write_text("\t".join(HEADER) + "\n" + body, encoding="utf-8")


def played(hymn: Hymn, names: Sequence[str] | None) -> Hymn:
    """Return the hymn set to these tunes, or to none where it has none.

    A single tune is stored as the name itself rather than a list of one: 763
    of the 764 hymns have exactly one, and the list is for the hymn that is
    genuinely printed twice.
    """

    if not names:
        return replace(hymn, tune=None)
    return replace(hymn, tune=names[0] if len(names) == 1 else list(names))


def _retune(path: Path, tunes: Mapping[int, Sequence[str]]) -> tuple[Path, str, str]:
    """Return one hymn's file and its text before and after."""

    source = path.read_text(encoding="utf-8")
    try:
        hymn = Hymn.from_markdown(source)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return path, source, played(hymn, tunes.get(int(path.stem))).to_markdown()


def rewrites(
    files: Iterable[Path], tunes: Mapping[int, Sequence[str]], jobs: int | None = None
) -> list[tuple[Path, str]]:
    """Return the files whose text the table changes, with their new text.

    Every row has to name a hymn that exists, so a row cannot go stale
    unnoticed; a hymn the table skips has its tune removed rather than left
    behind, which is what makes a second run over the first run's output a
    no-op even after a row is deleted.
    """

    paths = list(files)
    if not paths:
        raise ValueError("no hymns to set")
    numbers = {int(path.stem) for path in paths}
    unknown = sorted(set(tunes) - numbers)
    if unknown:
        raise ValueError(
            f"{len(unknown)} row(s) name a hymn that is not there, "
            f"beginning with {unknown[0]}"
        )
    workers = min(jobs or available_cpu_count(), len(paths))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_retune, paths, repeat(tunes)))
    return [(path, text) for path, source, text in results if text != source]


def apply(
    files: Iterable[Path], tunes: Mapping[int, Sequence[str]], jobs: int | None = None
) -> list[Path]:
    """Write each hymn's tune into its file; return the files that changed."""

    changed = rewrites(files, tunes, jobs)
    for path, text in changed:
        path.write_text(text, encoding="utf-8")
    return [path for path, _ in changed]
