"""Project the collection as the book's metrical index of tunes.

The fifth one-way projection, and the third that is a page about the whole
collection.  It is the book's own three-level index -- meter, then tune, then
the hymns set to that tune -- which is what tells a congregation that hymn 46
and hymn 607 are the same tune, and that a text in ``6.5.6.5.D.`` can be sung
to any of the six.

**It needs no table.** Both levels are already fields on the hymn: ``meter``
from [D1 and D13](../../PLAN.md) and ``tune`` from ``tunes``.  Nothing is read
out of the back matter here, and there is no third copy of either fact to keep
true.

**Order.** The hymnal files a meter by its figures, read as a sequence: 4.8.4.6.
before 4.10.8.8.6. before 5.4.5.4.D., so ``10.`` sorts after ``9.`` and not
between ``1.`` and ``2.``.  Where the figures are the same it prints the plain
form first, then the one marked ``(A)`` or ``(I)``, then ``with Repeat``, then
``with Chorus``; and the doubled form and everything under it after all of
those.  ``Irregular Meter`` goes last, as the book's ``Irregular Meters`` does.
Sorting by that rule reproduces the 212 headings the printed index carries, in
sequence, with none out of place -- which is the check on it.

**Three ways this is more than the printed index, each stated on the page.**

The book's metrical index covers hymns 1--764.  Every hymn in the collection
now carries a meter, so this files all 848; the 84 supplement hymns have no
tune name -- the English edition's two tune indexes stop at 764 -- so they file
under their meter directly, which is still the fact a metrical index is
consulted for.

The English edition files 111 hymns under ``Irregular Meters``.  On eighteen of
them the Chinese page prints an actual count, and D13 made that count the
meter, so those eighteen file under their figures here and under the book's
refusal to count there.

And the heading carries both editions.  The printed index is English; a meter
is the one field whose two halves this collection names separately, so where
the Chinese page writes the qualifier in Chinese the heading says so.

**One thing added that is not in ``data/``.** The book annotates three
headings with the name English hymnody knows them by -- ``(Short Meter)``,
``(Common Meter)``, ``(Long Meter)``.  Those are a property of the figures, not
of any hymn, so they are written here rather than stored 62 times over.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .model import Hymn
from .slides import _localized_inline, _yaml_scalar, span
from .tuneindex import sort_key as tune_sort_key


#: Where a hymn's page is, relative to the index.
PAGE_DIRECTORY = "hymn"
#: What this page is called.  The Chinese edition prints no index of meters
#: either; the label is the site's, as the index of tunes' is.
TITLE = {"en": "Metrical Index", "zh": "格律目錄"}
#: What the hymnal calls the three meters English hymnody has names for.
NAMED = {
    "6.6.8.6.": "Short Meter",
    "8.6.8.6.": "Common Meter",
    "8.8.8.8.": "Long Meter",
}
#: The meter that states no lengths, and so cannot be sorted among those that
#: do.  The book prints it last, under `Irregular Meters`.
IRREGULAR = "Irregular Meter"
#: What the Chinese page writes in its place, without the qualifiers `和` and
#: `重` that three of its 93 hymns carry -- those belong to the hymn, not to
#: the heading.
IRREGULAR_ZH = "特"
#: A meter with the same figures as another is filed after it in this order.
QUALIFIERS = (
    ("", 0),
    (" (A)", 1),
    (" (I)", 1),
    (" with repeat", 2),
    (" with chorus", 3),
    (" with chorus and repeat", 4),
)
#: Figures, an optional `D.`, and whatever qualifies them.
NOTATION = re.compile(r"^((?:\d+\.)+)(D\.)?(.*)$")


def sort_key(meter: str) -> tuple[tuple[int, ...], int, int]:
    """Return the figures, the doubling and the qualifier the book files by."""

    if meter == IRREGULAR:
        # Beyond every sequence of figures, which is where the book prints it.
        return ((10**6,), 0, 0)
    match = NOTATION.match(meter)
    if match is None:
        raise ValueError(f"not a meter this index can file: {meter!r}")
    figures = tuple(int(number) for number in re.findall(r"\d+", match.group(1)))
    ranks = dict(QUALIFIERS)
    if match.group(3) not in ranks:
        raise ValueError(f"not a qualifier this index can file: {meter!r}")
    return (figures, 1 if match.group(2) else 0, ranks[match.group(3)])


def _identifier(meter: str) -> str:
    """Return the anchor a meter's section is reachable at."""

    return "meter-" + re.sub(r"[^a-z0-9]+", "-", meter.lower()).strip("-")


def english(meter: str | object) -> str:
    """Return the analysis `data/N.md` stores, whichever form it is in."""

    if isinstance(meter, str):
        return meter
    return meter.translations["en"]  # type: ignore[union-attr]


def _chinese(meter: str | object) -> str | None:
    """Return the Chinese half, where the two editions do not print alike."""

    if isinstance(meter, str):
        return None
    return meter.translations.get("zh")  # type: ignore[union-attr]


def _filed(
    entries: Sequence[tuple[int, Hymn]],
) -> tuple[dict[str, dict[str | None, list[int]]], dict[str, str | None]]:
    """Group the collection by meter, then by tune, both in printed order.

    A hymn with no tune -- every one of the 84 in the supplement, because the
    English edition's tune indexes stop at 764 -- files under ``None``, which
    sorts after the named tunes.
    """

    filed: dict[str, dict[str | None, list[int]]] = {}
    chinese: dict[str, str | None] = {}
    for number, hymn in sorted(entries):
        if hymn.meter is None:
            raise ValueError(f"hymn {number} has no meter to file it under")
        meter = english(hymn.meter)
        # Every English meter but `Irregular Meter` has one Chinese half across
        # the whole collection; that one has three, differing by a qualifier
        # that belongs to the hymn rather than to the heading.
        chinese.setdefault(meter, IRREGULAR_ZH if meter == IRREGULAR else _chinese(hymn.meter))
        names = hymn.tune if isinstance(hymn.tune, list) else [hymn.tune]
        for name in names:
            filed.setdefault(meter, {}).setdefault(name, []).append(number)
    return filed, chinese


def _heading(meter: str, chinese: str | None) -> str:
    """Return the meter as the page heads its section with it."""

    printed = span(meter, "en")
    named = NAMED.get(meter)
    if named is not None:
        printed += f" [({named})]{{.meter-named}}"
    if chinese is not None and chinese != meter:
        printed += " " + span(chinese, "zh")
    return printed


def _entry(name: str | None, hymns: Sequence[int]) -> str:
    """Return one tune as its name and the hymns set to it, each one a link."""

    numbers = ", ".join(
        f"[{number}]({PAGE_DIRECTORY}/{number}.html)" for number in hymns
    )
    if name is None:
        # Where a tune name would be, on the 51 meters some supplement hymn
        # files under. One word rather than the sentence the note above
        # already gives it: this stands 51 times in a column of names.
        shown = _localized_inline({"en": "supplement", "zh": "補篇"})
        return f"[{shown}]{{.tune-name .meter-untuned}} [{numbers}]{{.tune-hymns}}"
    return f"[{span(name, 'en')}]{{.tune-name}} [{numbers}]{{.tune-hymns}}"


def to_markdown(entries: Sequence[tuple[int, Hymn]]) -> str:
    """Render the collection as the metrical index the English edition prints."""

    filed, chinese = _filed(entries)
    meters = sorted(filed, key=sort_key)
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
                    "Every hymn under the meter its page prints over it, and under "
                    "the tune the English edition sets it to -- so a text in one "
                    "meter can be sung to any tune filed with it. The hymnal prints "
                    "this index for hymns 1 to 764; this one covers all 848, and the "
                    "84 supplement hymns file under their meter with no tune, "
                    "because the English edition's tune indexes stop at 764. The "
                    "English edition files 111 hymns as Irregular Meter; on eighteen "
                    "of them the Chinese page prints a count, and the count is what "
                    "they are filed under here."
                ),
                "zh": (
                    "各首詩歌按其詩頁所印的格律排列，並列出英文版所配的曲調——"
                    "同一格律的詩歌，可以互換曲調歌唱。"
                    "詩集所印的格律目錄只列第 1 至 764 首；此處列全 848 首，"
                    "補篇 84 首因英文版曲調目錄止於第 764 首，故只列格律，不列曲調。"
                    "英文版將 111 首列為特（無定格律），"
                    "其中十八首中文詩頁印有格律，此處即按該格律排列。"
                ),
            }
        ),
        ":::",
        "",
    ]

    # A strip of the figure each run of meters opens with, as the index of
    # tunes has a strip of letters: the meters are 247 and the leading figures
    # are thirteen, and the first meter of each run is what it jumps to.
    first: dict[int, str] = {}
    for meter in meters:
        if meter == IRREGULAR:
            continue
        first.setdefault(sort_key(meter)[0][0], meter)
    jumps = [
        f"[{figure}](#{_identifier(first[figure])})" for figure in sorted(first)
    ]
    jumps.append(f"[{span(IRREGULAR_ZH, 'zh')}](#{_identifier(IRREGULAR)})")
    lines += ["::: {.tune-contents}", " ".join(jumps), ":::", ""]

    for meter in meters:
        lines += [
            f"## {_heading(meter, chinese[meter])} {{#{_identifier(meter)}}}",
            "",
        ]
        tunes = filed[meter]
        # Named tunes in the hymnal's own order; the supplement's untuned
        # hymns after all of them.
        for name in sorted(
            tunes, key=lambda tune: (1, []) if tune is None else (0, tune_sort_key(tune))
        ):
            lines += ["::: {.tune-entry}", _entry(name, tunes[name]), ":::", ""]
    return "\n".join(lines)
