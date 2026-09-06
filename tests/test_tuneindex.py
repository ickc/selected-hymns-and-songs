"""Tests for the index of tunes, a projection of the whole collection."""

from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.tuneindex import sort_key, to_markdown


def hymn(tune: str | list[str] | None) -> Hymn:
    front = "" if tune is None else f"tune: {tune}\n"
    return Hymn.from_markdown(f"---\ncategory: 讚美和敬拜——三一神\n{front}---\n\n# 1\n\nSing\n唱\n")


class OrderTest(TestCase):
    """How the hymnal files a tune name, which is not plain alphabetical."""

    def test_a_saint_is_filed_under_the_word_the_abbreviation_stands_for(self) -> None:
        # The book puts `St. Thomas` between `Sagina` and `Sandon`.
        names = ["Sandon", "St. Thomas", "Sagina"]

        self.assertEqual(sorted(names, key=sort_key), ["Sagina", "St. Thomas", "Sandon"])

    def test_a_name_is_filed_word_by_word_not_letter_by_letter(self) -> None:
        names = ["Abba", "A Friend", "All for Jesus", "Alford"]

        self.assertEqual(
            sorted(names, key=sort_key), ["A Friend", "Abba", "Alford", "All for Jesus"]
        )

    def test_a_comma_sorts_before_the_next_letter_as_the_book_files_it(self) -> None:
        names = ["Behold, What Love", "Behold What Manner of Love"]

        self.assertEqual(
            sorted(names, key=sort_key),
            ["Behold What Manner of Love", "Behold, What Love"],
        )

    def test_a_name_opening_on_an_apostrophe_is_filed_by_its_word(self) -> None:
        names = ["Tidings", "'Tis So Sweet", "Till We Meet"]

        self.assertEqual(
            sorted(names, key=sort_key), ["Tidings", "Till We Meet", "'Tis So Sweet"]
        )


class IndexTest(TestCase):
    """What the page says, which is every tune and the hymns set to it."""

    def test_each_tune_lists_the_hymns_set_to_it_in_number_order(self) -> None:
        markdown = to_markdown([(146, hymn("Azmon")), (60, hymn("Azmon"))])

        self.assertIn(
            "[[Azmon]{lang=en}]{.tune-name} "
            "[[60](hymn/60.html), [146](hymn/146.html)]{.tune-hymns}",
            markdown,
        )

    def test_a_hymn_printed_to_two_tunes_appears_under_both(self) -> None:
        markdown = to_markdown([(146, hymn(["Azmon", "Lyngham"]))])

        self.assertIn("Azmon]{lang=en}]{.tune-name} [[146]", markdown)
        self.assertIn("Lyngham]{lang=en}]{.tune-name} [[146]", markdown)

    def test_a_hymn_the_english_edition_does_not_carry_is_left_out(self) -> None:
        # The supplement and the 39 Chinese-only hymns have no tune, and the
        # index of tunes is not the place to say so.
        markdown = to_markdown([(146, hymn("Azmon")), (800, hymn(None))])

        self.assertEqual(markdown.count(".tune-entry"), 1)
        self.assertNotIn("800", markdown)

    def test_the_letters_lead_to_the_sections_they_head(self) -> None:
        markdown = to_markdown([(1, hymn("Beecher")), (2, hymn("Azmon"))])

        self.assertIn("[A](#tune-a) [B](#tune-b)", markdown)
        self.assertIn("## A {#tune-a}", markdown)
        self.assertIn("## B {#tune-b}", markdown)
