"""Tests for the variant fold the search box applies.

`site/search-fold.html` is JavaScript, so the behaviour of the fold is not
reachable from here. What is reachable are the two tables it folds by, and one
of them is the part that goes wrong.

`VARIANTS` points at whichever of two shapes of a character `data/` carries,
and `data/`'s orthography is still being corrected: D17 rewrote it once
already, and D18 leaves a sweep of the lyrics open. So these read it out of the
file and check it against `data/` itself, and a pair that stops being true of
the collection fails here rather than quietly searching for a character that is
no longer there.

`PRONOUNS` is checked only for its shape. It says the four ways of writing *ni*
are one word as far as finding a line goes, which is a statement about readers
rather than about the book, and no count in `data/` can confirm or refute it.
"""

import json
import re
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ROOT / "site" / "search-fold.html"
DATA = ROOT / "data"


def read_table(name: str) -> dict[str, str]:
    """Return one of the two tables the include folds by."""

    source = INCLUDE.read_text(encoding="utf-8")
    match = re.search(rf"var {name} = (\{{.*?\}});", source, re.DOTALL)
    if not match:
        raise ValueError(f"{INCLUDE} no longer declares a {name} table")
    return json.loads(match.group(1))


def read_variants() -> dict[str, str]:
    """Return the orthographic pairs, keyed by the form `data/` lacks."""

    return read_table("VARIANTS")


def read_pronouns() -> dict[str, str]:
    """Return the readings of *ni*, which are folded but not an orthography."""

    return read_table("PRONOUNS")


class TableTest(TestCase):
    """The shape of the table, which the regular expression in the file assumes."""

    def setUp(self) -> None:
        self.variants = read_variants()

    def test_the_table_is_there_and_is_not_empty(self) -> None:
        self.assertTrue(self.variants)

    def test_every_pair_is_one_character_against_another(self) -> None:
        # The fold is a character class, so a pair of two characters would be
        # silently dropped from it rather than fail.
        for variant, book in self.variants.items():
            self.assertEqual(len(variant), 1, variant)
            self.assertEqual(len(book), 1, book)
            self.assertNotEqual(variant, book)

    def test_no_pair_folds_into_another_pair(self) -> None:
        # One `replace` is the whole fold: nothing it writes can be something
        # it would have rewritten.
        self.assertFalse(set(self.variants.values()) & set(self.variants))

    def test_the_readings_of_you_are_not_among_the_orthographic_pairs(self) -> None:
        # They are folded, but by the other table: which of them a line takes
        # is a reading of who is addressed, so it says nothing about how the
        # book was set and is not checked against `data/`. See D17 and D18.
        for character in ("你", "妳", "祢", "袮"):
            self.assertNotIn(character, self.variants)
            self.assertNotIn(character, self.variants.values())


class PronounTest(TestCase):
    """The four shapes of *ni*, which the search folds and `data/` may not."""

    def setUp(self) -> None:
        self.pronouns = read_pronouns()
        self.variants = read_variants()

    def test_every_reading_folds_to_the_undifferentiated_one(self) -> None:
        # 你 is the one that carries no claim about the hearer, which is what a
        # searcher who does not remember the line's pronoun should land on.
        self.assertEqual(set(self.pronouns.values()), {"你"})

    def test_the_feminine_and_the_divine_are_both_folded(self) -> None:
        # 妳 is in `data/` and correct there -- Psalm 45's daughter in hymn 109,
        # the Church in 105. 祢 is not in `data/` yet and will be; 袮 is its
        # other shape and may never be, which is exactly why it is folded.
        for character in ("妳", "祢", "袮"):
            self.assertIn(character, self.pronouns)

    def test_the_two_tables_do_not_overlap(self) -> None:
        # One `replace` covers both, so a character in both tables would make
        # the result depend on which table was merged last.
        self.assertFalse(set(self.pronouns) & set(self.variants))
        self.assertFalse(set(self.pronouns) & set(self.variants.values()))


class CollectionTest(TestCase):
    """The orthographic table against the text it is meant to be searched over.

    Only that table. `PRONOUNS` is a leniency rather than a claim about how the
    book was set, so `data/` has nothing to say about it -- and once D17's pass
    over 你/祢 lands, checking it here would fail for the wrong reason.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.variants = read_variants()
        cls.text = "".join(
            path.read_text(encoding="utf-8") for path in sorted(DATA.glob("*.md"))
        )

    def test_each_pair_folds_towards_the_form_the_hymns_carry(self) -> None:
        # The point of the fold is that a query lands on what is indexed, so
        # the arrow has to point at whichever shape `data/` settled on -- which
        # is the book's older one seven times and the modern one once, 夠 for
        # the book's own minority 彀.
        for variant, book in self.variants.items():
            with self.subTest(pair=f"{variant}→{book}"):
                self.assertGreater(self.text.count(book), self.text.count(variant))

    def test_the_hymns_are_not_still_in_two_minds_about_a_pair(self) -> None:
        # A handful of the folded-away form is expected and documented: 458's
        # 著 is *zhu*, 556's 借 is *borrow*, and 814 and 817 keep the 彀 their
        # pages print. A sweep that left a hundred behind would be a different
        # thing, and would mean `data/` had drifted rather than been corrected.
        for variant in self.variants:
            with self.subTest(variant=variant):
                self.assertLess(self.text.count(variant), 10)
