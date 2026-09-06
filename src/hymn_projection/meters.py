"""Check each hymn's Chinese lyrics against the meter printed over them.

A meter is a syllable count: `8.6.8.6.` means four lines of eight, six, eight
and six syllables, and `.D.` doubles that to eight lines. Chinese is written
one syllable to the character, so the meter is a statement about the lyrics
that can simply be counted -- which makes it a check on both halves of the
hymn at once. Where the count disagrees with the meter, either the meter is
wrong or a character has gone missing from the text, and the hymnal's page
settles which.

The check is over the Chinese only. English syllable counts cannot be had by
counting anything, and the two editions sing the same tune, so the Chinese
count carries the meter for both.

The two editions do not write a meter the same way, and the difference is not
a mistake in either. Where a hymn's chorus is sung to the second half of a
doubled tune, the English page writes `8.7.8.7.D.` and the Chinese page writes
`8.7.8.7.和` -- the same eight sung lines, counted as one doubled verse on one
page and as a verse and a chorus on the other. So a doubled meter is measured
against the verse and the chorus it takes together whenever the verse alone is
too short for it.

What a meter does not describe, and which is therefore not counted: the repeat
a `重` asks for, which prints a line twice without counting it twice.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from os.path import commonprefix
from pathlib import Path

from .model import Hymn, Stanza


# The CJK ranges the hymnal's Chinese is written in. Punctuation is not sung
# and so is not counted.
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

# The numeric head of a meter: `8.6.8.6.`, optionally doubled by `D.`. What
# may follow it -- ` with chorus和`, ` (A)` -- is notation, not a count.
NUMBERS = re.compile(r"^\.?((?:\d+\.)+)(D\.)?")


def syllables(line: str) -> int:
    """Return how many syllables a Chinese lyric line is sung on."""

    return len(HAN.findall(line))


def printed(meter: str) -> list[int] | None:
    """Return the line lengths a meter states, or None if it states none."""

    match = NUMBERS.match(meter)
    if not match:
        return None
    counts = [int(number) for number in match.group(1).split(".") if number]
    return counts * 2 if match.group(2) else counts


def notation(counts: list[int]) -> str:
    """Write a run of line lengths the way the hymnal writes it.

    Eight lines that repeat after the fourth are the book's `D.`, and it never
    doubles anything else -- all 196 doubled meters in the collection state
    four lengths.
    """

    if len(counts) == 8 and counts[:4] == counts[4:]:
        return ".".join(str(count) for count in counts[:4]) + ".D."
    return ".".join(str(count) for count in counts) + "."


def _counts(stanza: Stanza) -> list[int]:
    return [
        syllables(line.translations["zh"])
        for line in stanza.lines
        if "zh" in line.translations
    ]


def stanza_counts(hymn: Hymn) -> list[tuple[int | str, list[int]]]:
    """Return the Chinese syllable count of each verse line, chorus aside."""

    return [
        (stanza.name, _counts(stanza))
        for stanza in hymn.stanzas
        if not isinstance(stanza.name, str)
    ]


def sung_counts(hymn: Hymn) -> list[tuple[int | str, list[int]]]:
    """Return each verse's line lengths with those of the chorus it takes.

    A congregation sings the chorus after the verse, and a doubled meter counts
    the two together. Which chorus a verse takes is the projection's rule: the
    most recent one at or before it.
    """

    choruses = {
        int(stanza.name.split("-")[0]): _counts(stanza)
        for stanza in hymn.stanzas
        if isinstance(stanza.name, str)
    }
    sung = []
    for name, counts in stanza_counts(hymn):
        taken = [choruses[at] for at in sorted(choruses) if at <= name]
        sung.append((name, counts + (taken[-1] if taken else [])))
    return sung


def implied(hymn: Hymn) -> str | None:
    """Return the meter the Chinese lyrics imply, or None if they imply none.

    They imply none when the verses do not agree with each other on their line
    lengths. That is not the same as the hymnal's `Irregular Meter` / `特`,
    which it also prints over hymns whose verses do agree but whose lengths
    make no conventional meter; only the page says which hymns those are.
    """

    shapes = {tuple(counts) for _, counts in stanza_counts(hymn)}
    if len(shapes) != 1:
        return None
    return notation(list(shapes.pop()))


@dataclass
class Disagreement:
    """One hymn whose Chinese lyrics do not scan as its meter says."""

    number: int
    meter: str | None
    expected: list[int] | None
    stanzas: list[tuple[int | str, list[int]]]
    implied: str | None

    @property
    def kind(self) -> str:
        """Name the shape of the disagreement, which is what decides its fix."""

        if self.meter is None:
            return "no meter"
        off = [counts for _, counts in self.stanzas if counts != self.expected]
        # One verse a syllable adrift while the rest scan is the shape a
        # dropped character makes; a meter that is simply wrong is wrong in
        # every verse at once.
        if len(off) == 1 and len(off[0]) == len(self.expected or []):
            distance = sum(
                abs(a - b) for a, b in zip(off[0], self.expected or [], strict=True)
            )
            if distance == 1:
                return "one verse, one syllable out"
        if self.implied is None:
            return "verses disagree with each other"
        return "every verse says the same other meter"


def disagreements(hymns: Iterable[tuple[int, Hymn]]) -> list[Disagreement]:
    """Return every hymn whose lyrics and meter do not agree, in number order."""

    found = []
    for number, hymn in hymns:
        counts = stanza_counts(hymn)
        text = _meter_text(hymn)
        if text is not None and printed(text) is None:
            # `Irregular Meter` / `特` states no lengths, so there is nothing
            # to count it against. The hymnal says as much and that is that.
            continue
        expected = printed(text or "")
        if expected is not None and _scans(hymn, counts, expected):
            continue
        found.append(
            Disagreement(number, _meter_text(hymn), expected, counts, implied(hymn))
        )
    return found


def _scans(
    hymn: Hymn, counts: list[tuple[int | str, list[int]]], expected: list[int]
) -> bool:
    """Say whether every verse is as long as the meter says, chorus included."""

    if all(c == expected for _, c in counts):
        return True
    return all(c == expected for _, c in sung_counts(hymn))


def _meter_text(hymn: Hymn) -> str | None:
    """Return the meter as `data/N.md` writes it, for reporting."""

    if hymn.meter is None:
        return None
    if isinstance(hymn.meter, str):
        return hymn.meter
    translations = list(hymn.meter.translations.values())
    shared = commonprefix(translations)
    return shared + "".join(text[len(shared):] for text in translations)


def read(path: Path) -> tuple[int, Hymn]:
    """Read one numbered hymn file."""

    return int(path.stem), Hymn.from_markdown(path.read_text(encoding="utf-8"))
