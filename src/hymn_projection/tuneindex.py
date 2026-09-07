"""Project the collection as the book's alphabetical index of tunes.

The fourth one-way projection, and the second that is a page about the whole
collection rather than about one hymn. It puts back the relation ``tunes``
reads out of the back matter: every tune the English edition names, and the
hymns set to it.

**Order.** The hymnal files a tune by its name word by word, expands a leading
``St.`` to ``Saint`` -- so ``St. Thomas`` sits between ``Sagina`` and
``Sandon`` -- and lets a comma or an apostrophe sort before a letter, which
puts ``Behold What Manner of Love`` before ``Behold, What Love``. Sorting the
625 names by that rule reproduces the printed sequence exactly but for two
entries, where the book's own index disagrees with itself.

**Scope, which the page states.** Tunes are the English edition's: the Chinese
edition names none, and neither index reaches past hymn 764, so the supplement
and the 39 Chinese-only hymns are not here. One hymn, 146, is printed to two
tunes and appears under both.

The metrical index -- the same relation grouped by meter -- is the other half
of the book's back matter, and is ``meterindex``. It was blocked on the meter
until D13 settled the 30 hymns of the 764 that did not agree with the book
about theirs; see ``PLAN.md``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .model import Hymn
from .slides import _localized_inline, _yaml_scalar, span


#: Where a hymn's page is, relative to the index.
PAGE_DIRECTORY = "hymn"
#: What this page is called. The Chinese edition prints no index of tunes; the
#: label is the site's, and the note below says as much.
TITLE = {"en": "Index of Tunes", "zh": "曲調目錄"}
#: The abbreviation the hymnal files under the word it stands for.
SAINT = re.compile(r"^St\.")
#: A name opening on an apostrophe -- `'Tis So Sweet` -- is filed by its word.
LEADING = re.compile(r"^'")


def sort_key(name: str) -> list[str]:
    """Return the words the hymnal files a tune name by."""

    return LEADING.sub("", SAINT.sub("Saint", name)).lower().split()


def _initial(name: str) -> str:
    """Return the letter of the alphabet a tune is filed under."""

    return sort_key(name)[0][0].upper()


def _identifier(letter: str) -> str:
    return f"tune-{letter.lower()}"


def _entry(name: str, hymns: Sequence[int]) -> str:
    """Return one tune as its name and the hymns set to it, each one a link."""

    numbers = ", ".join(
        f"[{number}]({PAGE_DIRECTORY}/{number}.html)" for number in hymns
    )
    return f"[{span(name, 'en')}]{{.tune-name}} [{numbers}]{{.tune-hymns}}"


def _filed(entries: Sequence[tuple[int, Hymn]]) -> dict[str, list[int]]:
    """Invert the collection: every tune, and the hymns set to it in number order."""

    filed: dict[str, list[int]] = {}
    for number, hymn in sorted(entries):
        if hymn.tune is None:
            continue
        names = hymn.tune if isinstance(hymn.tune, list) else [hymn.tune]
        for name in names:
            filed.setdefault(name, []).append(number)
    return filed


def to_markdown(entries: Sequence[tuple[int, Hymn]]) -> str:
    """Render the collection as the index of tunes the English edition prints."""

    filed = _filed(entries)
    names = sorted(filed, key=sort_key)
    lines = [
        "---",
        f"title: {_yaml_scalar(_localized_inline(TITLE))}",
        "lang: en",
        "format: html",
        "---",
        "",
        "::: {.tune-note}",
        _localized_inline(
            {
                "en": (
                    "The tune each hymn is set to, which no page of the hymnal prints "
                    "over the hymn: it is named only in the back matter, and named "
                    "there twice, once by tune and once by meter. Tunes belong to the "
                    "English edition -- the Chinese edition names none -- and reach "
                    "hymn 764, so the supplement is not here. Hymn 146 is printed to "
                    "two tunes and appears under both."
                ),
                "zh": (
                    "各首詩歌所配的曲調。詩頁本身並不印出曲調名稱，"
                    "只見於書末的兩個索引：一按曲調排列，一按格律排列。"
                    "曲調僅屬英文版，中文版並無曲調名稱，且只列至第 764 首，"
                    "故不含補篇。第 146 首配有兩個曲調，兩處皆列。"
                ),
            }
        ),
        ":::",
        "",
    ]

    letters = sorted({_initial(name) for name in names})
    lines += [
        "::: {.tune-contents}",
        " ".join(f"[{letter}](#{_identifier(letter)})" for letter in letters),
        ":::",
        "",
    ]

    written = ""
    for name in names:
        letter = _initial(name)
        if letter != written:
            written = letter
            lines += [f"## {letter} {{#{_identifier(letter)}}}", ""]
        lines += ["::: {.tune-entry}", _entry(name, filed[name]), ":::", ""]
    return "\n".join(lines)
