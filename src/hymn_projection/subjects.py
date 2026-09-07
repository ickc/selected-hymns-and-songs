"""Project the collection as the book's subject index.

The third one-way projection, beside ``slides`` and ``pages``, and the only one
that is a page about all 848 hymns rather than about one. It puts back the
outline the hymnal is arranged by: eighteen headings, their subheadings, and
under the deepest of them the hymns filed there.

Two things it takes from the table rather than from the hymns, because the
hymns cannot say them. The **order** is the book's, which nothing in
``data/N.md`` records -- a hymn knows its subject but not where that subject
comes in the index. The **levels** are the table's columns, so a name that
contains a dash or a parenthesis needs no unpicking here.

Each hymn is its number and what it is called, which is the book's own name
for it where the book has one -- ``titles`` reads those out of these very
indexes -- and the line it opens with where it has none. Both languages: the
name is English, because no Chinese index names a hymn, so the Chinese half is
always the first line.

Two things it is honestly less than the book, and the page says both. The
hymnal orders the hymns under a subject by that name; this orders them by
number, which is what the collection can be ordered by without reading the
index again. And the hymnal cross-lists a few hymns under a second subject,
which a single-valued category cannot hold, so each hymn appears once -- under
the subject its own page prints.

**The strip of section headings carries the hymn numbers each covers**, which
is the one thing the book prints in a third place. Both editions open with a
table of contents -- ``en/002``, ``zh/002`` -- that is the eighteen sections
and nothing else, each against the hymns filed under it. Those ranges are not
stored: they are computed from the hymns, and the computation was checked
against both printed pages. See ``DEVELOPER.md`` for what that check found.
"""

from __future__ import annotations

from collections.abc import Sequence

from .categories import Subject
from .model import Hymn
from .slides import _localized_inline, _yaml_scalar, title


#: Where a hymn's page is, relative to the index.
PAGE_DIRECTORY = "hymn"
#: What the two editions call this page.
TITLE = {"en": "Subject Index", "zh": "主題目錄"}
#: How the book numbers each level: Roman, plain, parenthesized. The English
#: edition prints `I. PRAISE AND WORSHIP`, `1. THE TRINITY`, `(8) His Sonship`;
#: the Chinese one prints the same numbers in its own numerals.
NUMERALS = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
            (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
            (5, "V"), (4, "IV"), (1, "I"))


def _roman(number: int) -> str:
    """Return the Roman numeral the English index heads a section with."""

    digits = []
    for value, numeral in NUMERALS:
        count, number = divmod(number, value)
        digits.append(numeral * count)
    return "".join(digits)


def _label(number: tuple[int, ...]) -> str:
    """Return the printed label of the level this numbering ends at."""

    level, last = len(number), number[-1]
    return {1: f"{_roman(last)}.", 2: f"{last}.", 3: f"({last})"}[level]


def _identifier(number: tuple[int, ...]) -> str:
    """Return a heading's anchor, which is its numbering and cannot collide.

    Two subjects under one heading are named the same often enough -- the
    Father's Love and the Son's -- that a heading identifier made of the words
    would not be unique.
    """

    return "subject-" + "-".join(str(part) for part in number)


def _heading(subject: Subject, level: int) -> str:
    """Return the Markdown heading for one level of a subject."""

    number = subject.number[:level]
    names = {"en": subject.en[level - 1], "zh": subject.zh[level - 1]}
    return (
        f"{'#' * (level + 1)} {_label(number)} {_localized_inline(names)} "
        f"{{#{_identifier(number)}}}"
    )


#: How the table of contents joins two runs of hymn numbers. Both editions
#: print a full stop there -- `220-280. 779-789` -- which reads as a decimal
#: point beside figures, so the page uses a comma and an en dash instead. The
#: numbers themselves are the book's.
RANGE_SEPARATOR = ", "


def _ranges(numbers: Sequence[int]) -> str:
    """Return a run of hymn numbers as the contents page states them.

    A section is not one run: the 84-hymn supplement was filed into the same
    eighteen sections, so most of them are printed as a main-body range and a
    supplement range. This collapses whatever runs there are rather than
    assuming two, and a section that is one hymn states that hymn alone.
    """

    runs: list[tuple[int, int]] = []
    for number in sorted(numbers):
        if runs and number == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], number)
        else:
            runs.append((number, number))
    return RANGE_SEPARATOR.join(
        str(first) if first == last else f"{first}\u2013{last}" for first, last in runs
    )


def _entry(number: int, hymn: Hymn) -> str:
    """Return one hymn as its number and its name, linked to its page.

    All of it is the link, not just the number: a number alone is a small thing
    to hit with a thumb, and the line is what a reader is actually looking for.
    """

    return (
        f"[[{number}]{{.subject-number}} {_localized_inline(title(hymn))}]"
        f"({PAGE_DIRECTORY}/{number}.html)"
    )


def _filed(
    subjects: Sequence[Subject], entries: Sequence[tuple[int, Hymn]]
) -> dict[str, list[tuple[int, Hymn]]]:
    """Group the hymns under the subject each one's own page prints."""

    filed: dict[str, list[tuple[int, Hymn]]] = {subject.chinese: [] for subject in subjects}
    for number, hymn in entries:
        chinese = hymn.category.translations.get("zh")
        if chinese not in filed:
            raise ValueError(
                f"hymn {number} is filed under {chinese!r}, which the subject index does not list"
            )
        filed[chinese].append((number, hymn))
    return filed


def to_markdown(subjects: Sequence[Subject], entries: Sequence[tuple[int, Hymn]]) -> str:
    """Render the whole collection as the index the hymnal is arranged by."""

    filed = _filed(subjects, entries)
    lines = [
        "---",
        f"title: {_yaml_scalar(_localized_inline(TITLE))}",
        # The page is a document, not a projection of one hymn: it names the
        # format the two editions' names sit inside, as `index.md` does.
        "lang: en",
        "format: html",
        "---",
        "",
        "::: {.subject-note}",
        _localized_inline(
            {
                "en": (
                    "Every hymn under the one subject its own page prints, in number "
                    "order. Each is named as the hymnal's own subject index names it, "
                    "in English; the Chinese beside it is the line the hymn opens with, "
                    "because no Chinese index names a hymn. The hymnal orders them by "
                    "name rather than by number, and cross-lists a few under a second "
                    "subject."
                ),
                "zh": (
                    "本目錄按詩歌編號排列，各首詩歌只列於其詩頁所印的主題之下。"
                    "英文題名錄自詩本的主題目錄；中文並無題名索引，故列出首句。"
                    "詩本則按題名排列，並將少數詩歌兼列於第二個主題之下。"
                ),
            }
        ),
        ":::",
        "",
    ]

    # What each section covers, which is what the contents page states beside
    # its name. Taken from the hymns rather than from the table, so it cannot
    # disagree with the entries printed below it.
    covered: dict[int, list[int]] = {}
    for subject in subjects:
        for number, _ in filed[subject.chinese]:
            covered.setdefault(subject.number[0], []).append(number)

    seen: set[int] = set()
    contents = []
    for subject in subjects:
        if subject.number[0] not in seen:
            seen.add(subject.number[0])
            names = {"en": subject.en[0], "zh": subject.zh[0]}
            section = subject.number[:1]
            hymns = covered.get(subject.number[0])
            entry = (
                f"[{_label(section)} {_localized_inline(names)}]"
                f"(#{_identifier(section)})"
            )
            if hymns:
                entry += f" [{_ranges(hymns)}]{{.subject-range}}"
            # The name and its numbers are one item of the strip, so a wrap
            # cannot come between them.
            contents.append(f"[{entry}]{{.subject-entry}}")
    lines += ["::: {.subject-contents}", " ".join(contents), ":::", ""]

    # The headings a subject sits under are printed once, not once per subject:
    # this walks the outline and emits a level only where it has changed.
    written: tuple[int, ...] = ()
    for subject in subjects:
        for level in range(1, subject.depth + 1):
            if written[:level] != subject.number[:level]:
                lines += [_heading(subject, level), ""]
                written = subject.number[:level]
        hymns = filed[subject.chinese]
        if hymns:
            lines += [
                "::: {.subject-hymns}",
                "\n\n".join(_entry(number, hymn) for number, hymn in hymns),
                ":::",
                "",
            ]
    return "\n".join(lines)
