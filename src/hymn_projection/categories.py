"""Read `data/categories.tsv`, the book's subject index, and apply it.

The hymnal prints a subject over every hymn, but the two editions print
different amounts of it. The Chinese page carries the whole path --
`安慰與鼓勵－因着主的照顧` -- while the English page carries only its first
level, `Comfort and Encouragement`. The publisher's Chinese source, which
`data/` descends from, therefore has a category on every hymn and the English
source has none at all.

The rest of the English path is in the book. The subject index of the English
edition (pages v-xvi) is numbered exactly as the Chinese one (pages 七-十一)
is, and the two agree hymn for hymn. `data/categories.tsv` is that
correspondence, written down once and checked in.

The table stores the levels apart and the book's numbering with them, rather
than one string per language. Splitting `Praise and Worship—The Son, His
Person and Work (His Divinity)` back into three levels would mean parsing a
format we control, and the parse has to survive a level whose name contains a
comma or a scripture reference -- so the table joins instead, which is the
direction that cannot go wrong. The numbering is the book's order, which
nothing else in `data/` records: sorting the subjects by their lowest hymn
number puts the Father's Love before His Majesty, and the hymnal does not.

Applying the table is a preprocessing step over `data/`, not part of building
the site. It runs when the table changes, and what it writes is then the source
like any other line of `data/N.md`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from itertools import repeat
from pathlib import Path

from .environment import available_cpu_count
from .model import Hymn, LocalizedText


#: One column per level per language, and the level's number in the book.
#: Empty in the third of each group where a subject has only two levels.
HEADER = ("n1", "n2", "n3", "zh1", "zh2", "zh3", "en1", "en2", "en3")
#: How the two editions write a subject over a hymn, which is what `data/N.md`
#: carries and what the table therefore has to be able to reproduce exactly.
CHINESE_DASH = "——"
ENGLISH_DASH = "—"


@dataclass(frozen=True)
class Subject:
    """One row: a subject's place in the book's order, and both its names."""

    #: Its numbering, outermost first -- `(1, 2, 5)` is the book's `I. 2. (5)`.
    #: Two or three long, because no subject is a level-1 heading alone.
    number: tuple[int, ...]
    #: The Chinese name of each of those levels.
    zh: tuple[str, ...]
    #: The English name of the same levels.
    en: tuple[str, ...]

    @property
    def depth(self) -> int:
        """How many levels deep the subject is printed: 2 or 3."""

        return len(self.number)

    @property
    def chinese(self) -> str:
        """The subject as the Chinese page prints it over a hymn."""

        return _flatten(self.zh, CHINESE_DASH, "（{}）")

    @property
    def english(self) -> str:
        """The subject as the English subject index files it."""

        return _flatten(self.en, ENGLISH_DASH, " ({})")


def _flatten(names: Sequence[str], dash: str, third: str) -> str:
    head = dash.join(names[:2])
    return head + third.format(names[2]) if len(names) == 3 else head


def read_table(path: Path) -> list[Subject]:
    """Read the subject index, in the order the book prints it.

    Tab-separated because the names contain commas, quotation marks and
    parentheses and cannot contain a tab: a hand-edited row therefore needs no
    quoting and cannot be misread.
    """

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or tuple(field.strip() for field in lines[0].split("\t")) != HEADER:
        raise ValueError(f"{path} must begin with the header {chr(9).join(HEADER)}")
    subjects = []
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("\t")]
        if len(fields) != len(HEADER):
            raise ValueError(
                f"{path}: line {line_number} is not {len(HEADER)} tab-separated fields"
            )
        subjects.append(_subject(fields, path, line_number))
    _check_numbering(subjects, path)
    return subjects


def _subject(fields: Sequence[str], path: Path, line_number: int) -> Subject:
    """Turn one row's nine fields into a subject, or say what is wrong with it."""

    columns = tuple(zip(fields[:3], fields[3:6], fields[6:]))
    for level, (number, chinese, english) in enumerate(columns[:2], start=1):
        if not (number and chinese and english):
            raise ValueError(
                f"{path}: line {line_number} has no level {level}; "
                f"every subject is printed under a heading and a subheading"
            )
    third = columns[2]
    if any(third) and not all(third):
        raise ValueError(
            f"{path}: line {line_number} gives only part of its third level; "
            f"give {HEADER[2]}, {HEADER[5]} and {HEADER[8]} together or none of them"
        )
    depth = 3 if all(third) else 2
    numbers = []
    for number, *_ in columns[:depth]:
        if not number.isdecimal() or int(number) < 1:
            raise ValueError(
                f"{path}: line {line_number} numbers a level {number!r}, "
                f"which is not a position in the book"
            )
        numbers.append(int(number))
    return Subject(
        number=tuple(numbers),
        zh=tuple(chinese for _, chinese, _ in columns[:depth]),
        en=tuple(english for *_, english in columns[:depth]),
    )


def _check_numbering(subjects: Sequence[Subject], path: Path) -> None:
    """Insist the file is the book's outline, in order and numbered as printed.

    The numbering is not decoration: it is the only record of the order, so a
    row inserted without renumbering would silently file a subject in the wrong
    place. Every level therefore has to run 1, 2, 3... under its parent, and a
    heading has to keep one number throughout.
    """

    seen: dict[int, dict[tuple[int, ...], tuple[str, ...]]] = {1: {}, 2: {}}
    counts: dict[tuple[int, ...], int] = {}
    depths: dict[tuple[int, ...], int] = {}
    for line_number, subject in enumerate(subjects, start=2):
        place = f"{path}: line {line_number}"
        for level in (1, 2):
            key = subject.number[:level]
            names = subject.zh[:level] + subject.en[:level]
            headings = seen[level]
            if key not in headings:
                siblings = [k for k in headings if k[: level - 1] == key[: level - 1]]
                if key[-1] != len(siblings) + 1:
                    raise ValueError(
                        f"{place} numbers its level {level} {key[-1]}, "
                        f"which does not follow the {len(siblings)} before it"
                    )
                if names in headings.values():
                    raise ValueError(f"{place} repeats a level {level} heading")
                headings[key] = names
            elif headings[key] != names:
                raise ValueError(
                    f"{place} gives level {level} number {key[-1]} a second name"
                )
        parent = subject.number[:2]
        counts[parent] = counts.get(parent, 0) + 1
        # A level 2 is either one subject or a run of them; the book prints no
        # hymns under a heading that also has subheadings.
        if depths.setdefault(parent, subject.depth) != subject.depth or (
            subject.depth == 2 and counts[parent] != 1
        ):
            raise ValueError(f"{place} is a subject and a heading of subjects at once")
        if subject.depth == 3 and subject.number[2] != counts[parent]:
            raise ValueError(
                f"{place} numbers its level 3 {subject.number[2]}, "
                f"which does not follow the {counts[parent] - 1} before it"
            )


def read_mapping(path: Path) -> dict[str, str]:
    """Read the table as the Chinese-to-English correspondence hymns need."""

    mapping: dict[str, str] = {}
    for subject in read_table(path):
        if subject.chinese in mapping:
            raise ValueError(f"{path} files {subject.chinese!r} in two places")
        mapping[subject.chinese] = subject.english
    return mapping


def write_table(subjects: Iterable[Subject], path: Path) -> None:
    """Write the table, for regenerating it rather than editing it by hand."""

    rows = []
    for subject in subjects:
        pad = ("",) * (3 - subject.depth)
        fields = (
            tuple(str(number) for number in subject.number)
            + pad
            + subject.zh
            + pad
            + subject.en
            + pad
        )
        rows.append("\t".join(fields) + "\n")
    path.write_text("\t".join(HEADER) + "\n" + "".join(rows), encoding="utf-8")


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
