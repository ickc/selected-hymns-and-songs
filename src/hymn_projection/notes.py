"""Check what the hymnal says about a hymn against the hymn.

The book prints two kinds of prose beside its hymns, and `data/` keeps them
apart by where it puts them.

A **direction** governs how the hymn is sung -- which lines to repeat, which
stanza leaves the chorus out, which stanzas the other edition does not have.
The page sets it apart from the stanza, in parentheses under the last line, so
`data/` carries it in the front matter under ``note``.

A **gloss** is a word about a word: what ``Beulah`` means, that ``基督`` may be
sung as ``耶穌``.  The page anchors it -- with an asterisk in the line, or by
quoting the word and naming its stanza -- and prints it at the foot, so `data/`
keeps it in the lyric line as an inline footnote, ``^[...]``.

Both kinds say something checkable, and this checks it.  A gloss quotes a word,
and the word has to be in the line the gloss hangs off; a note about the other
edition names stanzas, and the stanzas have to be the ones the hymn has; a note
telling a singer to repeat the last line cannot be printed on a hymn that has
already written the repeat out.  Every one of those was wrong somewhere in
`data/` before this existed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .model import Hymn
from .slides import GLOSS


# What a direction says and a gloss never does.  A gloss found saying one of
# these is a direction in the wrong place: it governs the stanza, not the word
# it happens to sit beside, and belongs in the front matter.
DIRECTION = re.compile(
    r"重唱|重複|唱兩遍|不唱|回頭再唱"
    r"|(?i:repeat\b|sung twice\b)"
)
# A direction to sing something again, as against one not to: 734's
# `Do not repeat chorus after the last verse` is the second, and a hymn told
# that may perfectly well have its repeats written out -- 734's has.
ORDERS_A_REPEAT = re.compile(r"(?<!不)重唱|重複|唱兩遍|回頭再唱|(?i:(?<!not )repeat\b)")
# The word a gloss is about, which the hymnal quotes.  Both editions use the
# curly double quote; the corner brackets `data/` once had here are not the
# hymnal's, and are what this catches if they come back.
QUOTED = re.compile(r"[“”]([^“”]+)[“”]")
# What ends a lyric line rather than saying anything about it. A repeat is
# looked for with this folded away; see `writes_the_repeat_out`.
TRAILING = "，。、；：！？,;:.!? "
# `第四節`, `第二詞`: which stanza the hymnal is talking about.  It writes the
# number in Chinese, and never past the tenth stanza.
NUMBERED = re.compile(r"第([一二三四五六七八九十]+)[節詞]")
CHINESE_DIGITS = "一二三四五六七八九"
# `英詩無第二節`, `英詩僅有一、二、五等三節`: what the Chinese edition says the
# English one is missing, and what it says the English one has.
WITHOUT = re.compile(r"英詩無第([一二三四五六七八九十、]+)[節詞]")
ONLY = re.compile(r"英詩僅有([一二三四五六七八九十、]+)等")
# `第二節不唱“和”歌`, `Do not repeat chorus after the last verse`: a stanza
# the chorus is not sung after, which `chorus-omitted` writes down.  Only the
# Chinese half names the stanza; both halves say that there is one.
OMITS_CHORUS = re.compile(
    r"第([一二三四五六七八九十、]+)節不唱“和”[歌詩]|(?i:do not repeat (?:the )?chorus)"
)
# `The Chinese version has 4 stanzas`: the same statement the other way round.
COUNTED = re.compile(r"[Tt]he Chinese version has (\d+) stanzas")


def chinese_number(text: str) -> int | None:
    """Read a stanza number the way the hymnal writes it."""

    if text == "十":
        return 10
    if len(text) == 2 and text[0] == "十":
        return 10 + CHINESE_DIGITS.index(text[1]) + 1
    if len(text) == 1 and text in CHINESE_DIGITS:
        return CHINESE_DIGITS.index(text) + 1
    return None


def chinese_numbers(text: str) -> list[int]:
    """Read the list of stanza numbers in `一、二、五`."""

    found = [chinese_number(part) for part in text.split("、")]
    return [number for number in found if number is not None]


@dataclass(frozen=True)
class Finding:
    """One thing a hymn's own prose says that the hymn does not bear out."""

    number: int
    kind: str
    detail: str


def _stanzas(hymn: Hymn) -> list[tuple[int, set[str]]]:
    """Return each numbered stanza and the languages it is written in."""

    return [
        (
            stanza.name,
            {
                language
                for line in stanza.lines
                for language in line.translations
            },
        )
        for stanza in hymn.stanzas
        if isinstance(stanza.name, int)
    ]


def _gloss_findings(number: int, hymn: Hymn) -> list[Finding]:
    """Check each gloss against the line and the stanza it is anchored in."""

    findings: list[Finding] = []
    for stanza in hymn.stanzas:
        for line in stanza.lines:
            for text in line.translations.values():
                for gloss in GLOSS.findall(text):
                    if DIRECTION.search(gloss):
                        findings.append(Finding(
                            number, "a direction is written as a gloss",
                            f"{gloss!r} governs the singing, not the word it "
                            "sits beside; it belongs in `note`",
                        ))
                    quoted = QUOTED.findall(gloss)
                    bare = GLOSS.sub("", text)
                    for word in quoted[:1]:
                        # The hymnal capitalizes the word it quotes even where
                        # the line does not: 768 glosses `“Truth”` on `truth`.
                        if word.casefold() not in bare.casefold():
                            findings.append(Finding(
                                number, "a gloss quotes a word its line does not hold",
                                f"{word!r} is not in {bare!r}",
                            ))
                    named = NUMBERED.search(gloss)
                    if named is not None:
                        said = chinese_number(named.group(1))
                        if said != stanza.name:
                            findings.append(Finding(
                                number, "a gloss names another stanza than its own",
                                f"{gloss!r} is anchored in stanza {stanza.name}",
                            ))
    return findings


def _note_findings(number: int, hymn: Hymn) -> list[Finding]:
    """Check each front-matter note against the stanzas it describes."""

    findings: list[Finding] = []
    stanzas = _stanzas(hymn)
    english = {name for name, languages in stanzas if "en" in languages}
    chinese = {name for name, languages in stanzas if "zh" in languages}
    for note in hymn.note:
        text = "".join(note.translations.values())
        for match in WITHOUT.finditer(text):
            missing = set(chinese_numbers(match.group(1)))
            if missing & english:
                findings.append(Finding(
                    number, "a note names an English stanza the hymn has",
                    f"{text!r}, but English has {sorted(english)}",
                ))
        for match in ONLY.finditer(text):
            said = set(chinese_numbers(match.group(1)))
            if said != english:
                findings.append(Finding(
                    number, "a note names the wrong English stanzas",
                    f"{text!r}, but English has {sorted(english)}",
                ))
        match = COUNTED.search(text)
        if match is not None and int(match.group(1)) != len(chinese):
            findings.append(Finding(
                number, "a note counts the wrong number of Chinese stanzas",
                f"{text!r}, but Chinese has {len(chinese)}",
            ))
        if ORDERS_A_REPEAT.search(text) and writes_the_repeat_out(hymn):
            findings.append(Finding(
                number, "a repeat is both directed and written out",
                f"{text!r}, but a stanza already ends with the line twice",
            ))
    findings.extend(_omission_findings(number, hymn))
    return findings


def _omission_findings(number: int, hymn: Hymn) -> list[Finding]:
    """Hold a direction to leave the chorus out against `chorus-omitted`."""

    directions = []
    named: set[int] = set()
    for note in hymn.note:
        text = "".join(note.translations.values())
        for match in OMITS_CHORUS.finditer(text):
            directions.append(text)
            if match.group(1):
                named.update(chinese_numbers(match.group(1)))
    omitted = set(hymn.chorus_omitted or ())
    if directions and not omitted:
        return [Finding(
            number, "a chorus a note leaves out is not written down",
            f"{directions[0]!r}, and chorus-omitted names no stanza",
        )]
    if omitted and not directions:
        return [Finding(
            number, "a chorus is left out that no note leaves out",
            f"chorus-omitted names {sorted(omitted)}, and no note says so",
        )]
    if named and named != omitted:
        return [Finding(
            number, "a chorus is left out of another stanza than its note names",
            f"{directions[0]!r} names {sorted(named)}, "
            f"and chorus-omitted {sorted(omitted)}",
        )]
    return []


def writes_the_repeat_out(hymn: Hymn) -> bool:
    """Say whether any stanza already ends with its closing lines sung again.

    Compared with the closing punctuation folded away, because the hymnal
    varies it between the two copies: 82 writes every stanza's last line twice
    and ends the first with a comma and the second with an exclamation mark, in
    both editions. Matching the strings exactly finds that repeat in three of
    its eight stanza-halves and misses five. Over the collection the fold takes
    the count from 31 hymns to 47.

    A tail, and adjacent, which is what this module's question needs: a note
    saying *repeat the last line* is contradicted by a stanza that already ends
    with its last line twice, and by nothing else. `repeats.WRITES_IT_OUT`
    names the four hymns whose repeat the book writes somewhere other than the
    tail, which is a different question and cannot be asked of the text alone.
    """

    for stanza in hymn.stanzas:
        for language in ("en", "zh"):
            lines = [
                line.translations[language].rstrip(TRAILING)
                for line in stanza.lines
                if language in line.translations
            ]
            for length in range(len(lines) // 2, 0, -1):
                if lines[-length:] == lines[-2 * length:-length]:
                    return True
    return False


def findings(hymns: list[tuple[int, Hymn]]) -> list[Finding]:
    """Return everything the collection's own prose gets wrong about itself."""

    result: list[Finding] = []
    for number, hymn in hymns:
        result.extend(_gloss_findings(number, hymn))
        result.extend(_note_findings(number, hymn))
    return result


def read(path: Path) -> tuple[int, Hymn]:
    """Read one numbered hymn."""

    return int(path.stem), Hymn.from_markdown(path.read_text())
