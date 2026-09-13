"""Check the three places the hymnal states a repeat against one another.

The book says *sing this again* in three ways and relates none of them.  It
writes the lines out a second time, as 122 and 534 and 650 and 678 do.  It
prints a direction under the last stanza -- *Repeat the last line of each
stanza*, ``每節重唱最後一行``.  Or it marks the meter, ``重`` in the Chinese
edition and ``with repeat`` in the English, and leaves the shape to the music.

Only the first of those is in `data/` in a form anything can act on, which is
why a deck used to print *Repeat the last line of each stanza* on its title
slide and then show each stanza once.  ``repeat`` in the front matter is the
other two written down: which of the stanza's lines are sung again, and in
which stanzas.  See ``model.Repeat`` for what it holds and why it is not
localized.

This module is the gate that keeps the three from drifting apart.  A meter
that asks for a repeat must have one somewhere; so must a direction; a repeat
written down must not also be written out, or it would be sung twice over; and
where the English edition names a number of lines, the field has to hold that
many.  A repeat named on lines or stanzas the hymn has not is refused by the
model before this runs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .model import Hymn
from .notes import ORDERS_A_REPEAT, writes_the_repeat_out


# The mark each edition ends a meter with when the tune sings something twice.
# It says that there is a repeat and never which, which is the whole reason
# `repeat` exists.
MARKED = re.compile(r"重|with repeat")
# `Repeat the last two lines`, `Repeat the last 2 lines of each stanza`,
# `Repeat last line`.  The English half of a direction is read rather than the
# Chinese half because an English line is a printed line: the Chinese pages set
# their stanzas in two columns, so `第四節末兩行` on `zh/258` is two printed
# rows and four of these lines, which is exactly what `en/266` calls
# *the last four lines*.
# There is no word boundary after ``lines`` to anchor on: the two halves of a
# note run together in `data/`, so the English half ends against Han script and
# ``lines重複`` is one word to `re`.
NAMES_LINES = re.compile(
    r"(?i:repeat\b)[^.]*?\blast\s+(?:the\s+)?(\d+|one|two|three|four|five|six)?\s*lines?"
)
WRITTEN_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
}
# A *da capo* is not a tail of a stanza sung again but the whole verse sung
# after the chorus, and `repeat` cannot hold it: its lines are the stanza's own
# and they are sung where the stanza ends.  355 is the only hymn whose note
# asks for one -- `zh/377` prints `(回頭再唱正歌一遍)` and `en/387` prints *Fine*
# over the eighth line and *D.C. al Fine* over the last -- so it is named here
# rather than given a field that would say the wrong thing.
DA_CAPO = re.compile(r"回頭再唱|D\.C\.")
# The four hymns whose repeat the book writes into the lyrics somewhere other
# than the end of a stanza, where `notes.writes_the_repeat_out` looks.  Each
# was read off its page, and each is a shape no rule over the text could pick
# out, because the same shape occurs in words that simply repeat:
#
# * 122 sets `Let angels prostrate fall,` twice in the middle of every stanza,
#   and `en/135` prints it twice in stanzas 2, 3 and 4 as well as under the
#   music.
# * 534 sets `Or on this earthly ball, Or on this earthly ball.` on one line.
#   321's `Full salvation! Full salvation!` is that shape and is not a repeat,
#   which is why this is a list and not a rule.
# * 650 sings its third and fourth lines again with a fifth interposed.
# * 678 writes the repeat out as `1-chorus`, and it is the same four lines
#   `en/71` prints under hymn 57's music without writing them anywhere.
WRITES_IT_OUT = frozenset({122, 534, 650, 678})
# The hymns whose repeat nothing in `data/` asks for, because only the score
# does -- no ``重``, no ``with repeat``, no direction -- each read off its page.
#
# * 745 is one stanza and no chorus, and both `en/812` and `zh/802` mark *Fine*
#   after its third line and *D.C.* at its end: the opening three lines sung
#   again, which is a ``repeat`` of ``[1, 2, 3]`` and not 355's *da capo*, which
#   comes back after a chorus.  Its last two lines are printed twice with their
#   own music, so the tail rule sees a repeat written out; that is the page's
#   lyric, and the *da capo* sings none of it again.
SCORE_ASKS = frozenset({745})


@dataclass(frozen=True)
class Finding:
    """One thing the three statements of a repeat do not agree about."""

    number: int
    kind: str
    detail: str


def _marked(hymn: Hymn) -> list[str]:
    """Return the meters of this hymn that ask for a repeat."""

    if hymn.meter is None:
        return []
    texts = (
        [hymn.meter] if isinstance(hymn.meter, str)
        else list(hymn.meter.translations.values())
    )
    return [text for text in texts if MARKED.search(text)]


def _directions(hymn: Hymn) -> list[str]:
    """Return the notes that order a repeat, the *da capo* excepted."""

    result = []
    for note in hymn.note:
        text = "".join(note.translations.values())
        if ORDERS_A_REPEAT.search(text) and not DA_CAPO.search(text):
            result.append(text)
    return result


def named_lines(text: str) -> int | None:
    """Return how many lines an English direction says are sung again."""

    match = NAMES_LINES.search(text)
    if match is None:
        return None
    said = match.group(1)
    if said is None:
        return 1
    return WRITTEN_NUMBERS.get(said.lower()) or int(said)


def accounted_for(number: int, hymn: Hymn) -> bool:
    """Say whether the lyrics already hold the repeat the book asks for."""

    return number in WRITES_IT_OUT or writes_the_repeat_out(hymn)


def findings(hymns: list[tuple[int, Hymn]]) -> list[Finding]:
    """Return everything the three statements of a repeat disagree about."""

    result: list[Finding] = []
    for number, hymn in hymns:
        marked = _marked(hymn)
        directions = _directions(hymn)
        repeat = hymn.repeat
        written = accounted_for(number, hymn) and number not in SCORE_ASKS

        if repeat is None:
            if marked and not written:
                result.append(Finding(
                    number, "a repeat the meter asks for is not written down",
                    f"{marked[0]!r} asks for one, and nothing says which lines",
                ))
            elif directions and not written:
                result.append(Finding(
                    number, "a repeat a note orders is not written down",
                    f"{directions[0]!r} orders one, and nothing says which lines",
                ))
            continue

        if written:
            result.append(Finding(
                number, "a repeat is written down and written out",
                f"{repeat.to_dict()} would sing again what a stanza already repeats",
            ))
        if not marked and not directions and number not in SCORE_ASKS:
            result.append(Finding(
                number, "a repeat is written down that nothing asks for",
                f"{repeat.to_dict()}, but no meter is marked and no note orders one",
            ))
        for text in directions:
            said = named_lines(text)
            if said is not None and said != len(repeat.lines):
                result.append(Finding(
                    number, "a repeat does not sing as many lines as its note names",
                    f"{text!r} names {said}, and the field holds {len(repeat.lines)}",
                ))
    return result


def read(path: Path) -> tuple[int, Hymn]:
    """Read one numbered hymn."""

    return int(path.stem), Hymn.from_markdown(path.read_text(encoding="utf-8"))
