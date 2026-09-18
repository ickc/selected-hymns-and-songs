#!/usr/bin/env python3
"""Read the Chinese edition's text layer for 你 against 祢, hymn by hymn.

The book distinguishes 祢, the reverential second person, from plain 你, and
`data/` carried 你 everywhere -- 4,546 times in 557 files -- because the
transcription it was seeded from does.  Which one a line prints turns on who is
addressed, so no substitution settles it; the page has to be read.

The page can be read twice.  The scans in `scan/zh/` are the authority and are
in this repository, but they are images.  The private extraction project also
carries the scan's own OCR text layer, and that OCR reads the printed 祢 as 妳
-- a wrong character, but a *consistently* wrong one, and therefore a witness:
a layer 妳 is a printed 祢 and a layer 你 is a printed 你.  This tool aligns
each hymn's Chinese lines against that layer and says, for every pronoun in
`data/`, whether the two agree, which way they differ, or that the layer cannot
say.  ``--apply`` writes the corrections it is sure of.

What the layer is not is an authority.  It is a reading like any other -- D17
already found it wrong about 爲 and 裏 more often than not -- so fifteen of its
verdicts were checked against the page images before any of them was applied,
its refusals are read off the images one by one, and its disagreements with the
English half of the line (``Thou`` against a plain 你) are listed for the same
treatment.  Every row it writes carries the page and the band to crop, because
that reading is the point of the exercise and the layer is only what makes it
finite.

Usage::

    python scripts/reverence_witness.py --layer ../../private/selected-hymns-and-songs-pdf

The layer lives outside this repository, which is why this is an extraction
whose *result* is committed rather than a check CI can run.  What CI runs is
`check-reverence`, which asserts the things that can be asserted here.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hymn_projection.converter import numbered_markdown_files  # noqa: E402
from hymn_projection.model import Hymn  # noqa: E402
from hymn_projection.scans import read_editions  # noqa: E402
from hymn_projection.slides import GLOSS  # noqa: E402


# The four shapes of *nǐ*.  `data/` spells the reverential one 祢 and the
# feminine one 妳, eight times, where the hymnal addresses a woman or the
# Church; the layer spells the reverential one 妳 and has no 祢 anywhere.
# Folding all four is what lets an alignment see through the very disagreement
# it is being asked about.
PRONOUNS = "你妳祢袮"
# What a layer character says the page prints.  The layer's 妳 is the page's 祢
# -- the OCR has no 祢 in it at all -- and 袮 is the variant neither uses.
REVERENTIAL = "妳祢袮"
# The form `data/` writes when the page prints the reverential pronoun.  The
# scan cannot separate 祢 from its 衣-radical variant 袮 at 1062x1676, and the
# repository had already settled on 祢 -- in `punctuation.py`'s account of
# `zh/49` and in the search fold's tests -- before this pass began.
REVERENT = "祢"
# The feminine 妳, which is in `data/` and right there: Psalm 45's daughter in
# hymn 109 and the Church in 105.  The layer spells the reverential pronoun the
# same way, so those lines would otherwise be corrected into a wrong word.
FEMININE = "妳"
# The English edition's reverential second person.  Its presence on the other
# half of the line is an independent statement that God is addressed; its
# absence is not, because the collection's later material addresses God as
# *you*.  So this witness is read in one direction only.
THOU = re.compile(r"\b(?:Thou|Thee|Thy|Thine|Thyself)\b")
# The OCR text is set in these two fonts.  Everything else on a Chinese page is
# the music: the numbered notation, the page furniture, the composer's name.
# Keeping only the OCR lines is what makes the alignment tractable, because the
# notation interleaves digits with the lyrics all the way down the page.
OCR_FONTS = ("HiddenHorzOCR", "HiddenVertOCR")
# Two OCR lines within this many points of each other are on one printed line.
# The layer sets a lyric in fragments -- `當我思念，我主，妳創造大工`, then
# `我心立` -- and their baselines agree to about a point.
SAME_LINE = 4.0
# A Chinese character is about this wide in the text layer's points; the OCR
# gives a box per line rather than per character, so a character's own
# position is interpolated along it.
CHARACTER_WIDTH = 9.0
# The page images are 1062x1676 for a page 376 points wide, so a point of the
# text layer is this many pixels.  It is wanted only to say where to crop.
PIXELS_PER_POINT = 2.824


def _is_han(character: str) -> bool:
    """Say whether a character is one the Chinese edition sets as a word."""

    return unicodedata.name(character, "").startswith("CJK ")


def _fold(character: str) -> str:
    """Return the character with the pronoun distinction removed."""

    return "你" if character in PRONOUNS else character


@dataclass(frozen=True)
class Character:
    """One Han character of the text layer, and where it is printed."""

    text: str
    page: int
    x: float
    y: float


@dataclass(frozen=True)
class Occurrence:
    """One pronoun in `data/`, and what the page's text layer says about it."""

    number: int
    stanza: str
    line: int
    offset: int
    #: What `data/` writes, and what the layer read there.
    written: str
    seen: str | None
    zh: str
    en: str
    #: The page to crop, and the pixel row to crop around -- from the layer's
    #: own position when it read the character, and from the nearest character
    #: it did read on the same line when it did not.
    page: int | None
    top: int | None

    @property
    def verdict(self) -> str:
        """Say what is to be done about this occurrence.

        ``correct`` and ``overcorrect`` are the two ways `data/` and the page
        differ, kept apart because they are not equally likely: the first is
        the defect this pass is for, and the second would be this pass having
        gone too far.
        """

        if self.seen is None:
            return "unresolved"
        if self.written == self.seen or (
            self.written in REVERENTIAL and self.seen in REVERENTIAL
        ):
            return "agree"
        if self.written == "你":
            return "correct"
        return "overcorrect"

    @property
    def conflict(self) -> bool:
        """Say whether the English half contradicts a plain reading.

        Only this direction is a conflict: the English half saying ``Thou``
        where the page prints a plain 你.  The other direction -- a modern
        *you* against a printed 祢 -- happens hundreds of times and means
        nothing, the two editions not having been written in one century.
        """

        return self.seen == "你" and bool(THOU.search(self.en))


def layer_characters(directory: Path, pages: list[int]) -> list[Character]:
    """Return the Han characters of a hymn's pages, in reading order.

    Reading order is approximate on purpose: the lyrics of a hymn are printed
    between the staves, so a page reads down in bands, and sorting the OCR
    lines by baseline and then by x recovers that.  Where it does not, the
    alignment below absorbs it as a move rather than a wrong verdict, because
    a character only counts when its neighbours matched too.
    """

    lines: list[tuple[int, float, float, str]] = []
    for page in pages:
        text = (directory / f"{page:03d}.json").read_text(encoding="utf-8")
        for sheet in json.loads(text)["pages"]:
            for block in sheet["blocks"]:
                for line in block.get("lines", ()):
                    if line["font"]["name"] not in OCR_FONTS:
                        continue
                    box = line["bbox"]
                    lines.append((page, box["y"], box["x"], line["text"]))
    ordered = sorted(lines, key=lambda line: (line[0], round(line[1] / SAME_LINE), line[2]))

    characters: list[Character] = []
    for page, y, x, text in ordered:
        for step, character in enumerate(text):
            if _is_han(character):
                characters.append(
                    Character(character, page, x + step * CHARACTER_WIDTH, y)
                )
    return characters


def hymn_characters(hymn: Hymn) -> list[tuple[str, str, int, int]]:
    """Return every Han character of the Chinese lines with where it sits.

    The offsets are into the line as `data/` writes it, so that a correction
    can be made at one of them.  A gloss is skipped: it is the hymnal's prose
    about a word rather than a word of the hymn, and the page sets it under the
    staves instead of in the line, where an alignment would look for it.
    """

    characters: list[tuple[str, str, int, int]] = []
    for stanza in hymn.stanzas:
        for index, line in enumerate(stanza.lines):
            text = line.translations.get("zh", "")
            glosses = [match.span() for match in GLOSS.finditer(text)]
            for offset, character in enumerate(text):
                if not _is_han(character):
                    continue
                if any(start <= offset < end for start, end in glosses):
                    continue
                characters.append((character, str(stanza.name), index, offset))
    return characters


def _halves(hymn: Hymn) -> dict[tuple[str, int], tuple[str, str]]:
    """Return each line's two halves, keyed by its stanza and its index."""

    return {
        (str(stanza.name), index): (
            line.translations.get("zh", ""), line.translations.get("en", ""),
        )
        for stanza in hymn.stanzas
        for index, line in enumerate(stanza.lines)
    }


def _nearest(
    characters: list[tuple[str, str, int, int]],
    read: dict[int, Character],
    index: int,
) -> Character | None:
    """Return where the layer read the character nearest to an unread one.

    An unresolved pronoun has no position of its own -- the layer did not read
    it -- so what is offered instead is the band its line is printed in, taken
    from the nearest character of the *same* line the layer did read.  Falling
    back to another line would name a band the character is not in, which is
    worse than naming none.
    """

    _, stanza, line, _ = characters[index]
    best: Character | None = None
    nearest: int | None = None
    for other, found in read.items():
        if characters[other][1] != stanza or characters[other][2] != line:
            continue
        distance = abs(other - index)
        if nearest is None or distance < nearest:
            best, nearest = found, distance
    return best


def witness(number: int, hymn: Hymn, layer: list[Character]) -> list[Occurrence]:
    """Say what the page's text layer reads at every pronoun of one hymn."""

    characters = hymn_characters(hymn)
    matcher = SequenceMatcher(
        None,
        [_fold(character) for character, *_ in characters],
        [_fold(character.text) for character in layer],
        autojunk=False,
    )
    read: dict[int, Character] = {}
    for start, other, size in matcher.get_matching_blocks():
        for step in range(size):
            read[start + step] = layer[other + step]

    halves = _halves(hymn)
    occurrences: list[Occurrence] = []
    for index, (character, stanza, line, offset) in enumerate(characters):
        if character not in PRONOUNS:
            continue
        found = read.get(index)
        if found is not None and found.text not in PRONOUNS:
            found = None
        place = found or _nearest(characters, read, index)
        zh, en = halves[(stanza, line)]
        occurrences.append(Occurrence(
            number, stanza, line, offset, character,
            found.text if found else None, zh, en,
            place.page if place else None,
            round(place.y * PIXELS_PER_POINT) if place else None,
        ))
    return occurrences


def corrected(hymn: Hymn, occurrences: list[Occurrence]) -> str:
    """Return the hymn's Markdown with every correction the layer is sure of.

    Nothing the layer refused is touched, and neither is a 妳: the hymnal's
    feminine pronoun reads the same to the OCR as its reverential one, so the
    eight lines that address a woman or the Church are left to be read.
    """

    wanted = {
        (occurrence.stanza, occurrence.line, occurrence.offset)
        for occurrence in occurrences
        if occurrence.verdict == "correct"
    }
    if not wanted:
        return hymn.to_markdown()
    for stanza in hymn.stanzas:
        for index, line in enumerate(stanza.lines):
            text = line.translations.get("zh")
            if text is None:
                continue
            offsets = sorted(
                offset for (name, other, offset) in wanted
                if name == str(stanza.name) and other == index
            )
            for offset in offsets:
                if text[offset] != "你":
                    raise ValueError(f"offset {offset} of {text!r} is not 你")
                text = f"{text[:offset]}{REVERENT}{text[offset + 1:]}"
            line.translations["zh"] = text
    return hymn.to_markdown()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=Path("data"))
    parser.add_argument("--scan", type=Path, default=Path("scan"))
    parser.add_argument("--layer", type=Path, required=True,
                        help="the private extraction project's directory")
    parser.add_argument("--out", type=Path,
                        help="write every occurrence to this TSV")
    parser.add_argument("--apply", action="store_true",
                        help="write the corrections the layer is sure of")
    arguments = parser.parse_args()

    edition = read_editions(arguments.scan)["zh"]
    directory = arguments.layer / "zh"

    occurrences: list[Occurrence] = []
    written = 0
    for path in numbered_markdown_files(arguments.data):
        number = int(path.stem)
        source = path.read_text(encoding="utf-8")
        hymn = Hymn.from_markdown(source)
        if not any(character in PRONOUNS
                   for stanza in hymn.stanzas
                   for line in stanza.lines
                   for character in line.translations.get("zh", "")):
            continue
        found = witness(number, hymn, layer_characters(directory, edition.pages(number)))
        occurrences.extend(found)
        if arguments.apply:
            text = corrected(hymn, found)
            if text != source:
                path.write_text(text, encoding="utf-8")
                written += 1

    if arguments.out:
        with arguments.out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow((
                "hymn", "stanza", "line", "offset", "written", "seen",
                "verdict", "conflict", "page", "top", "zh", "en",
            ))
            for occurrence in occurrences:
                writer.writerow((
                    occurrence.number, occurrence.stanza, occurrence.line,
                    occurrence.offset, occurrence.written, occurrence.seen or "",
                    occurrence.verdict, "thou" if occurrence.conflict else "",
                    occurrence.page if occurrence.page is not None else "",
                    occurrence.top if occurrence.top is not None else "",
                    occurrence.zh, occurrence.en,
                ))

    counts: dict[str, int] = {}
    for occurrence in occurrences:
        counts[occurrence.verdict] = counts.get(occurrence.verdict, 0) + 1
    hymns = {occurrence.number for occurrence in occurrences}
    unresolved = {occurrence.number for occurrence in occurrences
                  if occurrence.verdict == "unresolved"}
    unplaced = sum(1 for occurrence in occurrences
                   if occurrence.verdict == "unresolved" and occurrence.page is None)
    conflicts = sum(1 for occurrence in occurrences if occurrence.conflict)

    print(f"{len(occurrences)} pronouns in {len(hymns)} hymns")
    for verdict in ("agree", "correct", "overcorrect", "unresolved"):
        print(f"{counts.get(verdict, 0):>6}  {verdict}")
    print(f"{len(unresolved):>6}  hymns with an unresolved pronoun")
    print(f"{unplaced:>6}  unresolved with no band to crop")
    print(f"{conflicts:>6}  printed plain against an English Thou")
    if arguments.apply:
        print(f"{written:>6}  hymns rewritten")


if __name__ == "__main__":
    main()
