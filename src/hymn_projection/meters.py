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
a mistake in either. The Chinese page marks a doubled tune `雙` where the
English writes `D.`, a repeat `重` where it writes `with repeat`, a chorus
`和` where it writes `with chorus`, and an irregular meter `特` where it writes
`Irregular Meter`. Where a hymn's chorus is sung to the second half of a
doubled tune, the English page writes `8.7.8.7.D.` and the Chinese page writes
`8.7.8.7.和` -- the same eight sung lines, counted as one doubled verse on one
page and as a verse and a chorus on the other. So a doubled meter is measured
against the verse and the chorus it takes together whenever the verse alone is
too short for it.

The two pages can also state different *lengths*, and that too is neither page
being wrong. A meter describes the tune, and a translation may sit a syllable
differently on it: 45's English page prints `13. 13. 13. 14. with chorus`
while its Chinese page prints `8.5.8.5.雙.和`, and only the second describes
the Chinese lyrics. So a hymn may carry two meters, and the one counted here
is always the Chinese page's.

What a meter does not describe, and which is therefore not counted: the repeat
a `重` asks for, which prints a line twice without counting it twice.

A verse and a meter are two readings of one run of syllables, so they can
differ in two ways that want quite different work. They can hold different
syllables, which is a finding about the text and the only kind a page can
settle in our favour. Or they can hold the same syllables and cut them in
different places, which is often no finding at all: a meter names the lines of
the *tune*, a page prints the lines of the *stanza*, and where the tune's lines
are short the page prints two to a row. The hymnal does this both ways -- 617's
page states `7.6.7.6.雙` over rows of thirteen characters and 137's states
`13.13.13.13.` over the same shape -- so the report names the two apart rather
than calling both a disagreement.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import accumulate
from pathlib import Path

from .model import Hymn, Repeat, Stanza


# The CJK ranges the hymnal's Chinese is written in. Punctuation is not sung
# and so is not counted.
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

# A Pandoc inline note. `data/N.md` carries the hymnal's own directions in
# these -- 830's `^[重唱「求你快回來」兩次。]`, 355's
# `^[第四節末四行重唱一遍]` -- and they are printed beside the verse rather
# than sung in it. Twelve hymns carry one, and eleven of those verses were
# the longest disagreements the report had.
NOTE = re.compile(r"\^\[[^\]]*\]")

# The speaker a responsive chorus names before its line. Four hymns are set
# that way -- 491, 532, 533 and 761 -- and the label is announced, not sung,
# so it belongs to no note and to no count.
SPEAKER = re.compile(r"^（(?:姊妹|弟兄|全體)）")

# The `重` a Chinese meter may end with, and the `with repeat` its English
# half writes instead: sing the last line, or the last phrase, twice. The
# lengths before it are stated once, so a verse that writes the repeat out is
# longer than its meter without being wrong.
REPEAT = re.compile(r"重|with repeat")

# The numeric head of a meter: `8.6.8.6.`, optionally doubled -- `D.` on the
# English page, `雙` on the Chinese one. What may follow it -- ` with chorus`,
# `和`, ` (A)` -- is notation, not a count.
NUMBERS = re.compile(r"^\.?((?:\d+\.)+)(D\.|雙\.?)?")


def syllables(line: str) -> int:
    """Return how many syllables a Chinese lyric line is sung on."""

    return len(HAN.findall(SPEAKER.sub("", NOTE.sub("", line))))


def printed(meter: str) -> list[int] | None:
    """Return the line lengths a meter states, or None if it states none."""

    match = NUMBERS.match(meter)
    if not match:
        return None
    counts = [int(number) for number in match.group(1).split(".") if number]
    return counts * 2 if match.group(2) else counts


def repeats(
    meter: str, counts: list[int] | None, repeat: Repeat | None = None
) -> list[list[int]]:
    """Return every run of lines a verse of this meter may be sung on.

    Its lengths as printed, and -- where the meter asks for a repeat -- those
    lengths with the repeat sung after them.

    ``重`` says that there is a repeat and never which, so where nothing else
    says either, every tail is admitted and the verses choose: 82 repeats its
    last line, 627 its last two, 529 its last two as one line apiece. Where the
    hymn carries a ``repeat``, that is which, and only that run is offered --
    the mark has been read, and a verse measured against every tail is barely
    measured at all.

    The printed lengths stay admissible either way, because a repeat is not
    sung in every stanza of every hymn: 242's is sung in the fourth alone.
    """

    if counts is None:
        return []
    if not REPEAT.search(meter):
        return [counts]
    if repeat is not None and max(repeat.lines) <= len(counts):
        return [counts, counts + [counts[line - 1] for line in repeat.lines]]
    return [counts] + [counts + counts[-tail:] for tail in range(1, len(counts) + 1)]


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


def _sung_in_chinese(stanza: Stanza) -> bool:
    """Say whether this stanza is one the Chinese edition sings at all.

    Some hymns print more stanzas in English than in Chinese -- 840 prints one
    Chinese verse under five English ones, and says so on its English page.
    A stanza with no Chinese line is not a verse that lost its syllables; it
    is a verse the Chinese edition does not have, and counting it as zero made
    three hymns look like the worst disagreements in the collection.
    """

    return any("zh" in line.translations for line in stanza.lines)


def stanza_counts(hymn: Hymn) -> list[tuple[int | str, list[int]]]:
    """Return the Chinese syllable count of each verse line, chorus aside."""

    return [
        (stanza.name, _counts(stanza))
        for stanza in hymn.stanzas
        if not isinstance(stanza.name, str) and _sung_in_chinese(stanza)
    ]


def shape(hymn: Hymn) -> list[tuple[int | str, list[int]]]:
    """Return every stanza's line lengths, choruses included, in printed order.

    The count a hymn can always be given, whatever the hymnal says over it.
    Nothing writes this into `data/N.md`: a meter is what the book prints, and
    a second, derived one beside it would be a second thing to keep true. It is
    computed where it is used, which is here and in `pixi run meter-report
    --shape`.
    """

    return [
        (stanza.name, _counts(stanza))
        for stanza in hymn.stanzas
        if _sung_in_chinese(stanza)
    ]


def chorus_counts(hymn: Hymn) -> list[tuple[str, list[int]]]:
    """Return the line lengths of each chorus the hymn prints."""

    return [
        (stanza.name, _counts(stanza))
        for stanza in hymn.stanzas
        if isinstance(stanza.name, str) and _sung_in_chinese(stanza)
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
        if isinstance(stanza.name, str) and _sung_in_chinese(stanza)
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


def breaks(counts: list[int]) -> set[int]:
    """Return where a run of line lengths puts its line breaks.

    A verse is one run of syllables cut into lines, so the count of every line
    is the same thing as the set of places the run is cut. Written that way,
    two readings of one verse can be compared on the two questions that have
    different answers: whether they hold the same syllables, and whether they
    cut them in the same places.
    """

    return set(accumulate(counts))


#: The disagreement in which a syllable is actually unaccounted for. Every
#: other kind below has the whole verse present and differs only on where its
#: lines end, which is a question about the page's layout, not its text.
MISCOUNTED = "syllables are missing or added"

#: The classic shape of a dropped character: one verse adrift by one while
#: its siblings scan.
DROPPED = "one verse, one syllable out"

#: The lines hold what the meter asks for, cut somewhere else entirely --
#: which cannot be sung, so one of the two is wrong about this verse.
MOVED = "a line break is in a different place"

#: The two remaining kinds are the hymnal disagreeing with itself, not with
#: us. A meter names the lines of the *tune*; a page prints the lines of the
#: *stanza*, and where the tune's lines are short it prints two to a row. The
#: book does both -- 617's page states `7.6.7.6.雙` over rows of thirteen
#: characters and 137's states `13.13.13.13.` over the same shape -- so
#: neither reading is an error and every syllable is present either way.
JOINED = "the meter counts a break the lines do not print"
SPLIT = "the lines print a break the meter does not count"

#: Worst first: a missing syllable is a defect in the text, a moved break is a
#: defect in one of the two readings of it, and a join or a split is neither.
SEVERITY = (MISCOUNTED, DROPPED, MOVED, SPLIT, JOINED)


def compare(expected: list[int], counts: list[int]) -> str | None:
    """Name how one verse's lines differ from the lines asked of it."""

    if counts == expected:
        return None
    if sum(counts) != sum(expected):
        return MISCOUNTED
    asked, printed_here = breaks(expected), breaks(counts)
    if asked < printed_here:
        return SPLIT
    if printed_here < asked:
        return JOINED
    return MOVED


@dataclass
class Disagreement:
    """One hymn whose Chinese lyrics do not scan as its meter says."""

    number: int
    meter: str | None
    expected: list[int] | None
    stanzas: list[tuple[int | str, list[int]]]
    implied: str | None
    runs: list[list[int]] = field(default_factory=list)

    def held_to(self, counts: list[int]) -> list[int] | None:
        """Return the run of lengths this one verse is fairly held against.

        Where the meter asks for a repeat it offers several runs, and a verse
        that writes the repeat out is not a verse with syllables to spare. So
        a verse is measured against whichever admissible run holds as many
        syllables as it does, and only against the hymn's own reference when
        none of them do.
        """

        for run in self.runs:
            if sum(run) == sum(counts):
                return run
        return self.reference

    @property
    def reference(self) -> list[int] | None:
        """Return the line lengths the verses are held against.

        The meter, when it states any. When it does not -- `Irregular Meter`
        over verses that disagree with each other -- the verses are held
        against the shape most of them share, because the hymn is then its own
        only witness and the majority is the best reading of it available.
        """

        if self.expected:
            return self.expected
        shapes = [tuple(counts) for _, counts in self.stanzas]
        if not shapes:
            return None
        return list(max(set(shapes), key=shapes.count))

    @property
    def kinds(self) -> list[str]:
        """Name every way this hymn's verses miss the lines asked of them."""

        reference = self.reference
        if reference is None:
            return []
        found = {
            compare(self.held_to(counts) or reference, counts)
            for _, counts in self.stanzas
        }
        found.discard(None)
        if MISCOUNTED in found and self._is_one_dropped_character():
            found = (found - {MISCOUNTED}) | {DROPPED}
        return [name for name in SEVERITY if name in found]

    @property
    def kind(self) -> str:
        """Name the worst of them, which is what decides how to fix the hymn."""

        if self.meter is None:
            return "no meter"
        found = self.kinds
        return found[0] if found else MISCOUNTED

    def _is_one_dropped_character(self) -> bool:
        reference = self.reference or []
        off = [counts for _, counts in self.stanzas if counts != reference]
        if len(off) != 1 or len(off[0]) != len(reference):
            return False
        return sum(abs(a - b) for a, b in zip(off[0], reference, strict=True)) == 1


def disagreements(hymns: Iterable[tuple[int, Hymn]]) -> list[Disagreement]:
    """Return every hymn whose lyrics and meter do not agree, in number order."""

    found = []
    for number, hymn in hymns:
        counts = stanza_counts(hymn)
        text = _meter_text(hymn)
        expected = printed(text or "")
        runs: list[list[int]] = []
        if text is None:
            pass  # A hymn with no meter at all is a finding in itself.
        elif expected is None:
            # `Irregular Meter` / `特` states no lengths, so there is nothing
            # to count the verses against -- but they can still be counted
            # against each other, which is the whole check on the 93 hymns the
            # hymnal declines to give a meter.
            if implied(hymn) is not None:
                continue
        else:
            runs = sung = repeats(text, expected, hymn.repeat)
            if _scans(hymn, counts, sung):
                continue
            # A repeat gives the verses several runs they might be sung on.
            # The one they are held to is the one they come closest to.
            expected = min(sung, key=lambda run: _distance(counts, run))
            if _is_half_of(counts, expected):
                # Every verse is exactly the first half of a doubled meter, so
                # what does not scan is the chorus that completes it. Report
                # the two together, or the finding reads as six bad verses
                # where there is one bad chorus.
                counts = sung_counts(hymn)
        found.append(
            Disagreement(
                number, _meter_text(hymn), expected, counts, implied(hymn), runs
            )
        )
    return found


def _is_half_of(
    counts: list[tuple[int | str, list[int]]], expected: list[int]
) -> bool:
    """Say whether every verse is the first half of a doubled meter."""

    if len(expected) % 2 or expected[: len(expected) // 2] != expected[len(expected) // 2 :]:
        return False
    half = sum(expected) // 2
    # "The first half" by what it holds, not by where it breaks: 635's verse
    # is two lines of thirteen where the meter says four of 8.5, and it is
    # still the half its chorus completes.
    return bool(counts) and all(sum(c) == half for _, c in counts)


def _distance(
    counts: list[tuple[int | str, list[int]]], run: list[int]
) -> tuple[int, int]:
    """Say how far a hymn's verses are from one run of line lengths."""

    off = [c for _, c in counts if c != run]
    return len(off), sum(abs(sum(c) - sum(run)) for c in off)


@dataclass
class ChorusDisagreement:
    """One hymn whose choruses do not scan alike."""

    number: int
    choruses: list[tuple[str, list[int]]]


def chorus_disagreements(
    hymns: Iterable[tuple[int, Hymn]],
) -> list[ChorusDisagreement]:
    """Return every hymn whose choruses differ in length, in number order.

    A hymn that writes a chorus out under each stanza sings all of them to the
    same strain, so their line lengths have to agree even though the words do
    not. The meter says nothing about this -- it describes the verse -- so
    nothing else in the collection can catch a syllable lost from a chorus.
    """

    found = []
    for number, hymn in hymns:
        choruses = chorus_counts(hymn)
        if len({tuple(counts) for _, counts in choruses}) > 1:
            found.append(ChorusDisagreement(number, choruses))
    return found


def _scans(
    hymn: Hymn, counts: list[tuple[int | str, list[int]]], runs: list[list[int]]
) -> bool:
    """Say whether every verse is as long as the meter says, chorus included.

    A meter that asks for a repeat offers several runs, and each verse takes
    whichever one it is printed on. 274's first verse writes its repeat out
    beneath the music and its other two leave it to the singer, and the page
    is right all three times -- so a verse is asked to match some run, not all
    of them the same one.
    """

    if all(any(c == run for run in runs) for _, c in counts):
        return True
    return all(any(c == run for run in runs) for _, c in sung_counts(hymn))


def _meter_text(hymn: Hymn) -> str | None:
    """Return the meter the Chinese edition prints, which is what is counted.

    A localized meter holds two statements, and they are not always the same
    statement: 45's English page prints `13. 13. 13. 14. with chorus` over
    lines its Chinese page counts as `8.5.8.5.雙.和`. Both describe the same
    tune; only the second describes the Chinese lyrics, and the Chinese lyrics
    are what this module counts. So the Chinese half is read when there is
    one, and the single meter when the hymn states only one.

    This used to read the English half, on the belief that both stated the
    same lengths and differed only in the qualifier. That was true of `data/`
    because the transcription had made it true -- every localized meter
    carried the English figures on both sides -- and forty of the hymns the
    report could not settle were that collapse and nothing else.
    """

    if hymn.meter is None:
        return None
    if isinstance(hymn.meter, str):
        return hymn.meter
    translations = hymn.meter.translations
    return translations.get("zh") or next(iter(translations.values()))


def read(path: Path) -> tuple[int, Hymn]:
    """Read one numbered hymn file."""

    return int(path.stem), Hymn.from_markdown(path.read_text(encoding="utf-8"))
