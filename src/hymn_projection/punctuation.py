"""Check that every lyric line is written with the marks the hymnal sets.

Punctuation is not sung, so nothing that counts syllables can see it: it
survived the re-lineations, the meter report and every check built since.  It
is also not one convention but two, because the book sets each edition in its
own typography, and `data/` transcribes both into one file.

Three rules, and each one is a statement about the page.

**The alphabet.** A Chinese lyric line holds Han characters and the marks the
Chinese edition sets; an English lyric line holds Latin letters and the marks
the English edition sets.  Anything else is a transcription slip, and the whole
of what `data/` had wrong falls out of this one rule: a halfwidth ``,`` among
fifteen thousand ``，``, a presentation-form ``﹔`` among three thousand ``；``,
an apostrophe typed straight in the hymns that were entered last.

**Do not normalise the English toward ASCII.** The obvious move -- store
``'tis`` and let Pandoc curl it -- gets this collection wrong, and the codec
already refuses it: ``PANDOC_MARKDOWN`` is ``markdown-smart``, so what is in
`data/` is what the page prints.  ``smart`` would read a leading ``'`` as an
*opening* quote and set ``'tis`` as ``‘tis``, where the page prints ``’tis``:
the mark is an elision, not a quotation.  The normalisation runs the other way,
toward the typographic form, which is what the collection already mostly has.

**The line boundary.** A closing mark stays with the line it closes and an
opening mark goes with the line it opens.  The re-lineations were done under
this rule and nothing until now stated it; a line beginning ``”`` is a break
put in the wrong place, and `data/` had three.

**The pairing.** Chinese quotation marks pair within the hymn -- ``“”`` and
``「」`` both.  English ones need only never close what was not opened, because
English sets a quotation running over several stanzas by opening each of them
and closing only the last, and 345 does exactly that.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .model import Hymn
from .slides import GLOSS


# The marks the Chinese edition sets.  The em dash is here singly because the
# pages print one dash and `data/` writes it doubled, ``——``, as Chinese
# typography asks; the doubling is a matter for the alphabet, not for this set.
# The ellipsis is here for one line: 418 ends `不知如何方能重新…`, and
# `zh/439` prints the three dots.  Chinese usually sets an ellipsis as six,
# `……`, but the collection has no second one to be consistent with, and the
# page is what `data/` transcribes.
CHINESE_MARKS = "，。、；：！？“”「」（）—…"
# The marks the English edition sets.  Straight ``'`` and ``"`` are absent on
# purpose, and so is ``‘``: every one of the thirty-five this collection had
# was an elision -- ``‘Tis``, ``‘Neath``, ``‘gainst`` -- and the hymnal quotes
# nothing inside a quotation, so an opening single quote here is a wrong mark.
# The en dash is here for one line: 797 sets `Thy way – Thy chosen way,` and
# `en/847` prints it, spaced, in the modern face the collection's later
# material is typeset in.  Everywhere else the English dash is an unspaced
# em dash, `en/16` included, where `data/` had an en dash and the page an em.
ENGLISH_MARKS = " ,.;:!?-—–()[]“”’"
# One space may stand in a Chinese line, where the page sets the line in two
# columns and `data/` writes it as one.  A run of them is column padding, which
# is a property of the printed page's width and not of the text.
CHINESE_SPACE = " "

# A line may not begin with a mark that closes something, nor end with one that
# opens something: the mark belongs to the line on the other side of the break.
BEGINS_CLOSING = "”」』）)，。、；：！？,;:.!?"
ENDS_OPENING = "“「『（("

# Marks that pair off within a hymn, and the edition each belongs to.
PAIRS = {"zh": (("“", "”"), ("「", "」"))}


@dataclass(frozen=True)
class Finding:
    """One place where a lyric line is not written the way the page prints."""

    number: int
    kind: str
    detail: str


def _name(character: str) -> str:
    """Describe a character the way a bug report needs it."""

    return f"U+{ord(character):04X} {unicodedata.name(character, '?')}"


def _is_han(character: str) -> bool:
    """Say whether a character is one the Chinese edition sets as a word."""

    return unicodedata.name(character, "").startswith("CJK ")


def _lines(hymn: Hymn) -> list[tuple[object, str, str]]:
    """Return every lyric line with its stanza and edition, glosses removed.

    A gloss is the hymnal's prose about a word, not a word of the hymn, and it
    is written in Markdown -- so its brackets and its caret would fail the
    alphabet rule for reasons that have nothing to do with the printed line.
    """

    return [
        (stanza.name, language, GLOSS.sub("", text))
        for stanza in hymn.stanzas
        for line in stanza.lines
        for language, text in line.translations.items()
    ]


def _alphabet_findings(number: int, hymn: Hymn) -> list[Finding]:
    """Check that each line is spelled with the marks its edition sets."""

    findings: list[Finding] = []
    for stanza, language, text in _lines(hymn):
        marks = CHINESE_MARKS + CHINESE_SPACE if language == "zh" else ENGLISH_MARKS
        for character in text:
            if character in marks:
                continue
            if language == "zh" and _is_han(character):
                continue
            if language == "en" and character.isascii() and character.isalpha():
                continue
            findings.append(Finding(
                number, "a mark the edition does not set",
                f"{stanza} {language}: {_name(character)} in {text!r}",
            ))
        if language == "zh" and re.search(r"  +|　", text):
            findings.append(Finding(
                number, "a line padded to a column width",
                f"{stanza} zh: {text!r}",
            ))
        if language == "zh" and re.search(r"(?<!—)—(?!—)", text):
            findings.append(Finding(
                number, "a dash written singly",
                f"{stanza} zh: the Chinese edition sets it doubled, in {text!r}",
            ))
    return findings


def _boundary_findings(number: int, hymn: Hymn) -> list[Finding]:
    """Check that no line begins with a closing mark or ends with an opening one."""

    findings: list[Finding] = []
    for stanza, language, text in _lines(hymn):
        if text[:1] and text[0] in BEGINS_CLOSING:
            findings.append(Finding(
                number, "a line begins with a closing mark",
                f"{stanza} {language}: {_name(text[0])} in {text!r}",
            ))
        if text[-1:] and text[-1] in ENDS_OPENING:
            findings.append(Finding(
                number, "a line ends with an opening mark",
                f"{stanza} {language}: {_name(text[-1])} in {text!r}",
            ))
    return findings


def _pairing_findings(number: int, hymn: Hymn) -> list[Finding]:
    """Check that quotation marks pair off over the hymn."""

    findings: list[Finding] = []
    texts: dict[str, list[str]] = {}
    for _, language, text in _lines(hymn):
        texts.setdefault(language, []).append(text)

    for language, lines in texts.items():
        whole = "\n".join(lines)
        for opening, closing in PAIRS.get(language, ()):
            if whole.count(opening) != whole.count(closing):
                findings.append(Finding(
                    number, "a quotation the hymn does not close",
                    f"{language}: {whole.count(opening)} {opening} "
                    f"against {whole.count(closing)} {closing}",
                ))
        depth = 0
        for character in whole:
            depth += character == "“"
            depth -= character == "”"
            if depth < 0:
                findings.append(Finding(
                    number, "a quotation closed before it was opened",
                    f"{language}: a ” with no “ before it",
                ))
                break
    return findings


def findings(hymns: list[tuple[int, Hymn]]) -> list[Finding]:
    """Return every lyric line not written with the marks the hymnal sets."""

    result: list[Finding] = []
    for number, hymn in hymns:
        result.extend(_alphabet_findings(number, hymn))
        result.extend(_boundary_findings(number, hymn))
        result.extend(_pairing_findings(number, hymn))
    return result


def read(path: Path) -> tuple[int, Hymn]:
    """Read one numbered hymn."""

    return int(path.stem), Hymn.from_markdown(path.read_text())
