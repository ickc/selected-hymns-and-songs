"""Give each hymn's category its English half from `data/categories.tsv`.

The hymnal prints a subject over every hymn, but the two editions print
different amounts of it. The Chinese page carries the whole path --
`安慰與鼓勵－因着主的照顧` -- while the English page carries only its first
level, `Comfort and Encouragement`. The publisher's Chinese source, which
`data/` descends from, therefore has a category on every hymn and the English
source has none at all.

The rest of the English path is in the book. The subject index of the English
edition (pages v-xvi) is numbered exactly as the Chinese one (pages 七-十一)
is, and the two agree hymn for hymn. `data/categories.tsv` is that
correspondence, written down once and checked in; this module is what reads it
and puts it on the hymns.

It is a preprocessing step over `data/`, not part of building the site. It runs
when the mapping changes, and what it writes is then the source like any other
line of `data/N.md`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from itertools import repeat
from pathlib import Path

from .environment import available_cpu_count
from .model import Hymn, LocalizedText


HEADER = ("zh", "en")


def read_mapping(path: Path) -> dict[str, str]:
    """Read the Chinese-to-English category table.

    Tab-separated because both halves contain commas, quotation marks and
    parentheses and neither can contain a tab: a hand-edited row therefore
    needs no quoting and cannot be misread.
    """

    mapping: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or tuple(lines[0].split("\t")) != HEADER:
        raise ValueError(f"{path} must begin with the header {HEADER[0]}\t{HEADER[1]}")
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("\t")]
        if len(fields) != 2 or not all(fields):
            raise ValueError(f"{path}: line {number} is not two non-empty fields")
        chinese, english = fields
        if chinese in mapping:
            raise ValueError(f"{path}: line {number} repeats {chinese!r}")
        mapping[chinese] = english
    return mapping


def write_mapping(rows: Iterable[tuple[str, str]], path: Path) -> None:
    """Write the table, for regenerating it rather than editing it by hand."""

    body = "".join(f"{chinese}\t{english}\n" for chinese, english in rows)
    path.write_text("\t".join(HEADER) + "\n" + body, encoding="utf-8")


def localized(hymn: Hymn, english: str) -> Hymn:
    """Return the hymn with the English half of its category set.

    The Chinese half is left exactly as it was. `data/N.md` is the authority on
    what the Chinese page says; the table only ever supplies the English.
    """

    chinese = hymn.category.translations["zh"]
    return replace(hymn, category=LocalizedText({"en": english, "zh": chinese}))


def _translate(path: Path, mapping: Mapping[str, str]) -> tuple[Path, str, str, str]:
    """Return one hymn's file, its Chinese category, and its text before and after."""

    source = path.read_text(encoding="utf-8")
    try:
        hymn = Hymn.from_markdown(source)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    chinese = hymn.category.translations.get("zh")
    if chinese is None:
        raise ValueError(f"{path}: category has no Chinese half to translate")
    english = mapping.get(chinese)
    text = source if english is None else localized(hymn, english).to_markdown()
    return path, chinese, source, text


def rewrites(
    files: Iterable[Path], mapping: Mapping[str, str], jobs: int | None = None
) -> list[tuple[Path, str]]:
    """Return the files whose text the table changes, with their new text.

    Every category in `data/` must be in the table and every row of the table
    must be used, so neither can go stale unnoticed: an untranslated hymn would
    show a category in one language on a page a reader asked to see in the
    other, and a row nothing matches is a typo or a category since renamed.
    """

    paths = list(files)
    if not paths:
        raise ValueError("no hymns to translate")
    workers = min(jobs or available_cpu_count(), len(paths))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_translate, paths, repeat(mapping)))

    seen = {chinese for _, chinese, _, _ in results}
    untranslated = sorted(seen - set(mapping))
    if untranslated:
        raise ValueError(
            f"{len(untranslated)} category(s) are not in the table, "
            f"beginning with {untranslated[0]!r}"
        )
    unused = sorted(set(mapping) - seen)
    if unused:
        raise ValueError(
            f"{len(unused)} row(s) of the table match no hymn, "
            f"beginning with {unused[0]!r}"
        )
    return [(path, text) for path, _, source, text in results if text != source]


def apply(
    files: Iterable[Path], mapping: Mapping[str, str], jobs: int | None = None
) -> list[Path]:
    """Write the English category into each hymn; return the files that changed.

    Idempotent: the text is written from the parsed hymn, so a second run over
    the first run's own output produces the same bytes and writes nothing.
    """

    changed = rewrites(files, mapping, jobs)
    for path, text in changed:
        path.write_text(text, encoding="utf-8")
    return [path for path, _ in changed]
