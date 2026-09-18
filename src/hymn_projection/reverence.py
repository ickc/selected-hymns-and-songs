"""Read `data/reverence.tsv`, the pronouns read off the page, and apply it.

The Chinese edition distinguishes 祢, the reverential second person, from
plain 你, and reserves it for God.  `data/` descends from a transcription that
did not: it wrote 你 4,546 times and 祢 not once.  Which one a line prints
turns on who is addressed, line by line, so nothing about the text settles it
-- D17 could correct 着 for 著 and 爲 for 為 by substitution and could not touch
this.  The pages had to be read.

Most of them were read by machine.  The scan's own OCR, which only the private
extraction project holds, misreads the printed 祢 as 妳 and gets plain 你
right, so aligning each hymn against it says which of the two is printed at
3,826 of the 4,554 pronouns -- and `scripts/reverence_witness.py` is that
alignment.  It is not in this repository's reach and its verdicts are not in
this table: they are simply in `data/`, the way D17's and D19's corrections
are.

**This table is the rest.**  Every row is a pronoun a person read off
`scan/zh/N.png`, because the layer would not say: 728 the OCR did not read at
all, and the ones where it read a plain 你 against an English half that says
*Thou* -- which is not a contradiction, the English addressing the believer as
*thee* about as often as it addresses God, but is worth looking at twice.  The
row records what the page prints and which page it was read on, so the reading
is in the repository rather than in a commit message, and `check-reverence`
holds `data/` to it.

The check also asserts two things about the whole of `data/`, which is where
the machine-read majority is held to account:

**A line spells its pronouns the same way everywhere it is printed.**  The
hymnal repeats lines -- between stanzas, into a chorus, across the two halves
of a repeat -- and a partial reading leaves one copy corrected and the other
not.  That is exactly how hymn 830 was caught, its last stanza printing
我求祢快來 twice and `data/` having corrected one of them.  Closing
punctuation is folded away because the hymnal varies it between the copies.

**妳 is the feminine pronoun and belongs to two hymns.**  105 addresses the
Church and 109 versifies Psalm 45's daughter.  The OCR spells the reverential
pronoun the same way, so an automatic pass over its verdicts could quietly
turn those eight into a wrong word; naming them is what makes that loud.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .model import Hymn
from .slides import GLOSS


#: The columns of `data/reverence.tsv`.
HEADER = ("hymn", "stanza", "line", "offset", "pronoun", "page", "zh")
#: The four shapes of *nǐ*.  `data/` writes three of them: 你 for anyone, 祢
#: for God, 妳 for a woman or the Church.  袮 is the 衣-radical variant of 祢,
#: which the search folds and `data/` does not use.
PRONOUNS = "你妳祢袮"
#: What `data/` may write, which is the three the hymnal sets.
WRITTEN = "你祢妳"
#: The reverential pronoun, and the feminine one.
REVERENT = "祢"
FEMININE = "妳"
#: The two hymns the feminine pronoun belongs to, and what it addresses there.
HERS = {105: "the Church", 109: "Psalm 45's daughter"}
#: The English edition's reverential second person.  It is a witness in one
#: direction only: where it appears, the line addresses someone the English
#: sets apart, which may be God or may be the believer, so a plain 你 under it
#: is worth reading off the page rather than wrong.  Its absence says nothing
#: at all, the collection's later material addressing God as *you*.
THOU = re.compile(r"\b(?:Thou|Thee|Thy|Thine|Thyself)\b")
#: Folded away when two printings of a line are compared: the hymnal ends the
#: first copy of a repeated line with a comma and the second with a full stop
#: or an exclamation mark, in both editions.
TRAILING = "，。、；：！？”"


@dataclass(frozen=True)
class Reading:
    """One pronoun read off a page image, and where both of them are."""

    #: Where it is in `data/`: the hymn, the stanza's name, the line's index
    #: within that stanza, and the character's offset within that line.
    number: int
    stanza: str
    line: int
    offset: int
    #: What the page prints there, and the page it was read on.
    pronoun: str
    page: int
    #: The line as `data/` writes it, so that the row can be read by a person
    #: and so that applying it can refuse a line that has since been changed.
    text: str

    @property
    def key(self) -> tuple[int, str, int, int]:
        """Return what makes this reading one reading."""

        return (self.number, self.stanza, self.line, self.offset)


@dataclass(frozen=True)
class Finding:
    """One thing `data/` gets wrong about the hymnal's two pronouns."""

    number: int
    kind: str
    detail: str


def fold(text: str) -> str:
    """Return a line with the pronoun distinction and the line's end removed."""

    for pronoun in PRONOUNS:
        text = text.replace(pronoun, "你")
    return text.rstrip(TRAILING)


def read_ledger(path: Path) -> list[Reading]:
    """Read the table, refusing anything it cannot mean."""

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != HEADER:
            raise ValueError(f"{path}: columns must be {', '.join(HEADER)}")
        rows = list(reader)

    readings: list[Reading] = []
    for index, row in enumerate(rows, start=2):
        try:
            reading = Reading(
                int(row["hymn"]), row["stanza"], int(row["line"]),
                int(row["offset"]), row["pronoun"], int(row["page"]), row["zh"],
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f"{path}:{index}: {error}") from error
        if reading.pronoun not in WRITTEN:
            raise ValueError(
                f"{path}:{index}: {reading.pronoun!r} is not one of {WRITTEN}"
            )
        if reading.offset >= len(reading.text) or reading.text[reading.offset] not in PRONOUNS:
            raise ValueError(
                f"{path}:{index}: offset {reading.offset} of {reading.text!r} "
                "is not a pronoun"
            )
        readings.append(reading)

    seen: dict[tuple[int, str, int, int], int] = {}
    for index, reading in enumerate(readings, start=2):
        if reading.key in seen:
            raise ValueError(
                f"{path}:{index}: hymn {reading.number} {reading.stanza}"
                f"/{reading.line}+{reading.offset} is already read "
                f"on line {seen[reading.key]}"
            )
        seen[reading.key] = index
    return readings


def _lines(hymn: Hymn) -> list[tuple[str, int, str, str]]:
    """Return every line's stanza, index and two halves, glosses removed.

    A gloss is the hymnal's prose about a word rather than a word of the hymn,
    and the page sets it under the staves rather than in the line.  It holds no
    pronoun in this collection, and dropping it keeps the offsets of what
    precedes it, which is what a reading is written against.
    """

    return [
        (str(stanza.name), index,
         GLOSS.sub("", line.translations.get("zh", "")),
         line.translations.get("en", ""))
        for stanza in hymn.stanzas
        for index, line in enumerate(stanza.lines)
    ]


def rewrite(number: int, hymn: Hymn, readings: Sequence[Reading]) -> str:
    """Return the hymn's Markdown with every reading of it written in."""

    wanted = {reading.key: reading for reading in readings
              if reading.number == number}
    if not wanted:
        return hymn.to_markdown()
    for stanza in hymn.stanzas:
        for index, line in enumerate(stanza.lines):
            text = line.translations.get("zh")
            if text is None:
                continue
            for offset in sorted(
                key[3] for key in wanted if key[1] == str(stanza.name) and key[2] == index
            ):
                reading = wanted[(number, str(stanza.name), index, offset)]
                if fold(text) != fold(reading.text):
                    raise ValueError(
                        f"hymn {number} {reading.stanza}/{reading.line} is "
                        f"{text!r}, and the table read {reading.text!r}"
                    )
                if text[offset] not in PRONOUNS:
                    raise ValueError(
                        f"hymn {number} {reading.stanza}/{reading.line} has no "
                        f"pronoun at offset {offset}: {text!r}"
                    )
                text = f"{text[:offset]}{reading.pronoun}{text[offset + 1:]}"
            line.translations["zh"] = text
    return hymn.to_markdown()


def rewrites(
    files: Iterable[Path], readings: Sequence[Reading]
) -> list[tuple[Path, str]]:
    """Return the files the table changes, with their new text.

    Every reading must land on a hymn: a row for a hymn `data/` does not have,
    or for a line it no longer writes the way it was read, is a row that has
    gone stale against the very thing it was supposed to hold in place.
    """

    paths = list(files)
    numbers = {int(path.stem) for path in paths}
    missing = sorted({reading.number for reading in readings} - numbers)
    if missing:
        raise ValueError(
            f"{len(missing)} row(s) read a hymn that is not here, "
            f"beginning with {missing[0]}"
        )

    changed: list[tuple[Path, str]] = []
    for path in paths:
        number = int(path.stem)
        source = path.read_text(encoding="utf-8")
        text = rewrite(number, Hymn.from_markdown(source), readings)
        if text != source:
            changed.append((path, text))
    return changed


def apply(files: Iterable[Path], readings: Sequence[Reading]) -> list[Path]:
    """Write every reading into `data/`; return the files that changed."""

    changed = rewrites(files, readings)
    for path, text in changed:
        path.write_text(text, encoding="utf-8")
    return [path for path, _ in changed]


def _consistency_findings(hymns: list[tuple[int, Hymn]]) -> list[Finding]:
    """Check that one printed line spells its pronouns one way."""

    spellings: dict[str, dict[str, list[int]]] = {}
    for number, hymn in hymns:
        for _, _, zh, _ in _lines(hymn):
            if not any(character in PRONOUNS for character in zh):
                continue
            written = "".join(c for c in zh if c in PRONOUNS)
            spellings.setdefault(fold(zh), {}).setdefault(written, []).append(number)

    findings: list[Finding] = []
    for line, written in sorted(spellings.items()):
        if len(written) == 1:
            continue
        where = ", ".join(
            f"{spelling} in {sorted(set(numbers))}"
            for spelling, numbers in sorted(written.items())
        )
        number = min(min(numbers) for numbers in written.values())
        findings.append(Finding(
            number, "one line spelled two ways", f"{line!r}: {where}",
        ))
    return findings


def _thou_findings(
    hymns: list[tuple[int, Hymn]], readings: Sequence[Reading]
) -> list[Finding]:
    """Check that a plain 你 under an English ``Thou`` was read off the page."""

    read = {reading.key for reading in readings}
    findings: list[Finding] = []
    for number, hymn in hymns:
        for stanza, index, zh, en in _lines(hymn):
            if not THOU.search(en):
                continue
            for offset, character in enumerate(zh):
                if character != "你" or (number, stanza, index, offset) in read:
                    continue
                findings.append(Finding(
                    number, "a plain 你 where the English says Thou",
                    f"{stanza}/{index}+{offset}: {zh!r} against {en!r}",
                ))
    return findings


def _feminine_findings(hymns: list[tuple[int, Hymn]]) -> list[Finding]:
    """Check that 妳 is only where the hymnal addresses a woman."""

    findings = []
    for number, hymn in hymns:
        if number in HERS:
            continue
        for stanza, index, zh, _ in _lines(hymn):
            if FEMININE in zh:
                findings.append(Finding(
                    number, "the feminine 妳 outside the two hymns it belongs to",
                    f"{stanza}/{index}: {zh!r}",
                ))
    return findings


def findings(
    hymns: list[tuple[int, Hymn]], readings: Sequence[Reading]
) -> list[Finding]:
    """Return everything `data/` gets wrong about the hymnal's two pronouns."""

    result = _consistency_findings(hymns)
    result.extend(_thou_findings(hymns, readings))
    result.extend(_feminine_findings(hymns))
    return result


def read(path: Path) -> tuple[int, Hymn]:
    """Read one numbered hymn."""

    return int(path.stem), Hymn.from_markdown(path.read_text(encoding="utf-8"))
