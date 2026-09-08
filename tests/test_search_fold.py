"""Tests for the variant fold the search box applies.

`site/search-fold.html` is JavaScript, so the behaviour of the fold is not
reachable from here. What is reachable is the table it folds by, and the table
is the part that goes wrong: it points at whichever of two shapes of a
character `data/` carries, and `data/`'s orthography is still being corrected.
D17 rewrote it once already, and D18 leaves a sweep of the lyrics open. These
read the table out of the file and check it against `data/` itself, so a pair
that stops being true of the collection fails here rather than quietly
searching for a character that is no longer there.
"""

import json
import re
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ROOT / "site" / "search-fold.html"
DATA = ROOT / "data"


def read_variants() -> dict[str, str]:
    """Return the table the include folds by, keyed by the form `data/` lacks."""

    source = INCLUDE.read_text(encoding="utf-8")
    match = re.search(r"var VARIANTS = (\{.*?\});", source, re.DOTALL)
    if not match:
        raise ValueError(f"{INCLUDE} no longer declares a VARIANTS table")
    return json.loads(match.group(1))


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

    def test_the_reading_of_you_is_left_out(self) -> None:
        # 你/祢 is not a choice of glyph but of who is addressed, and the book
        # makes it both ways. See D17 and D18.
        self.assertNotIn("你", self.variants)
        self.assertNotIn("祢", self.variants.values())


class CollectionTest(TestCase):
    """The table against the text it is meant to be searched over."""

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
