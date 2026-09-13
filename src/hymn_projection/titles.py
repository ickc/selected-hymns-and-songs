"""Give each hymn the name the hymnal's subject index files it under.

The hymnal prints no title over a hymn: a page carries the subject, the meter,
the number and the credits, and nothing else. Its own back-matter index is
headed *Index of First Lines and Choruses* -- "first lines are in lower case
type; choruses in small caps" -- which is the book saying, in as many words,
that a hymn is known by the line it opens with and by the chorus it is sung to.

The one place the book names each hymn once is the **subject index**, and that
is what this table is: 764 entries in the main index, 45 more in the
supplement's own, all in one lower-case face with nothing to mark which are
titles and which are opening lines. Counted against the line each hymn opens
with, 49% are that line, 19% are it cut short to fit the column, and 32% are
another name altogether -- the tune (`Abba`, `Higher ground`, `Spirit song`),
the chorus (`Up from the grave He arose`), or the name the hymn is simply known
by (`How great Thou art`, `Leaning on the Everlasting Arms`).

Two things the table does not have, because the book does not. It is
**English**: no Chinese index names a hymn -- the 主題目錄 lists bare numbers
and the 首句索引 lists eight-character first lines -- so a hymn keeps its
Chinese first line beside its English name, which is what ``slides.title``
merges. And it stops short of the **scripture portions**, 734-764, where the
index prints a verse reference rather than a name.

Applying it is a preprocessing step over ``data/``, not part of building the
site, exactly as ``categories`` is: it runs when the table changes, and what it
writes is then the source like any other line of ``data/N.md``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from itertools import repeat
from pathlib import Path

from .environment import available_cpu_count
from .model import Hymn, LocalizedText


HEADER = ("number", "en")


def read_titles(path: Path) -> dict[int, str]:
    """Read the number-to-name table the subject indexes were read into."""

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or tuple(field.strip() for field in lines[0].split("\t")) != HEADER:
        raise ValueError(f"{path} must begin with the header {chr(9).join(HEADER)}")
    titles: dict[int, str] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("\t")]
        if len(fields) != 2 or not all(fields):
            raise ValueError(f"{path}: line {line_number} is not two non-empty fields")
        number, english = fields
        if not number.isdecimal():
            raise ValueError(f"{path}: line {line_number} is not numbered by a hymn")
        if int(number) in titles:
            raise ValueError(f"{path}: line {line_number} names hymn {number} twice")
        titles[int(number)] = english
    if sorted(titles) != list(titles):
        raise ValueError(f"{path} must be in hymn order")
    return titles


def write_titles(titles: Mapping[int, str], path: Path) -> None:
    """Write the table, for regenerating it rather than editing it by hand."""

    body = "".join(f"{number}\t{titles[number]}\n" for number in sorted(titles))
    path.write_text("\t".join(HEADER) + "\n" + body, encoding="utf-8")


def named(hymn: Hymn, english: str | None) -> Hymn:
    """Return the hymn with its English name set, or removed where it has none.

    Only the English half is ever written. Nothing here invents a Chinese one:
    no Chinese index names a hymn, and ``slides.title`` puts the Chinese first
    line beside this.
    """

    if english is None:
        return replace(hymn, title=None)
    return replace(hymn, title=LocalizedText({"en": english}))


def _retitle(path: Path, titles: Mapping[int, str]) -> tuple[Path, str, str]:
    """Return one hymn's file and its text before and after."""

    source = path.read_text(encoding="utf-8")
    try:
        hymn = Hymn.from_markdown(source)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return path, source, named(hymn, titles.get(int(path.stem))).to_markdown()


def rewrites(
    files: Iterable[Path], titles: Mapping[int, str], jobs: int | None = None
) -> list[tuple[Path, str]]:
    """Return the files whose text the table changes, with their new text.

    Every row has to name a hymn that exists, so a row cannot go stale
    unnoticed; a hymn the table skips has its title removed rather than left
    behind, which is what makes a second run over the first run's output a
    no-op even after a row is deleted.
    """

    paths = list(files)
    if not paths:
        raise ValueError("no hymns to name")
    numbers = {int(path.stem) for path in paths}
    unknown = sorted(set(titles) - numbers)
    if unknown:
        raise ValueError(
            f"{len(unknown)} row(s) name a hymn that is not there, "
            f"beginning with {unknown[0]}"
        )
    workers = min(jobs or available_cpu_count(), len(paths))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_retitle, paths, repeat(titles)))
    return [(path, text) for path, source, text in results if text != source]


def apply(
    files: Iterable[Path], titles: Mapping[int, str], jobs: int | None = None
) -> list[Path]:
    """Write each hymn's name into its file; return the files that changed."""

    changed = rewrites(files, titles, jobs)
    for path, text in changed:
        path.write_text(text, encoding="utf-8")
    return [path for path, _ in changed]
