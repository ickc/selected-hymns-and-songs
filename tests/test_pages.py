"""Tests for the page projection: the hymn beside the scan it was read off."""

from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.pages import Collection, page_title, to_markdown
from hymn_projection.scans import Edition


def collection(**editions: Edition) -> Collection:
    return Collection(
        editions={
            "en": editions.get("en", Edition("en", {1: (16, 16)})),
            "zh": editions.get("zh", Edition("zh", {1: (8, 8)})),
        },
        source_url="https://example.invalid/blob/main/data",
        highest=848,
    )


def hymn(stanza: dict[object, list[dict[str, str]]], **fields: object) -> Hymn:
    return Hymn.from_dict({"category": {"zh": "分類"}, "stanza": stanza, **fields})


def page(value: Hymn, number: int = 1, **editions: Edition) -> str:
    return to_markdown(value, number, collection(**editions))


class StructureTest(TestCase):
    """A page keeps the hymnal's own shape, which the deck deliberately does not."""

    def test_a_stanza_is_not_divided_for_a_page(self) -> None:
        lines = [{"en": f"Line {index}"} for index in range(1, 9)]
        # The deck halves an eight-line stanza to fit a screen. Nothing here is
        # a screen, and the scan beside it prints the stanza whole.
        markdown = page(hymn({1: lines}))

        self.assertIn("## 1 {#s1}", markdown)
        self.assertNotIn("(1/2)", markdown)
        self.assertEqual(markdown.count("::: {.lyrics}"), 1)
        self.assertEqual(markdown.count("Line 8"), 1)

    def test_a_chorus_appears_once_however_often_it_is_sung(self) -> None:
        value = hymn(
            {
                1: [{"en": "One"}],
                "1-chorus": [{"en": "Again"}],
                2: [{"en": "Two"}],
            }
        )

        markdown = page(value)

        # The deck repeats it after each stanza; a page against one printed
        # copy of it would then show three.
        self.assertEqual(markdown.count("Again"), 1)
        self.assertIn("{#c1-chorus}", markdown)

    def test_a_chorus_is_named_only_where_a_hymn_has_more_than_one(self) -> None:
        one = page(hymn({1: [{"en": "One"}], "1-chorus": [{"en": "A"}]}))
        self.assertNotIn("`1-chorus`", one)

        several = page(
            hymn(
                {
                    1: [{"en": "One"}],
                    "1-chorus": [{"en": "A"}],
                    2: [{"en": "Two"}],
                    "2-chorus": [{"en": "B"}],
                }
            )
        )
        self.assertIn("`1-chorus`", several)

    def test_the_meter_a_deck_drops_is_printed_here(self) -> None:
        value = hymn({1: [{"en": "One"}]}, meter={"en": "8.6.8.6.", "zh": "8.6.8.6."})

        self.assertIn("8.6.8.6.", page(value))

    def test_a_singing_instruction_leaves_the_lyric_line(self) -> None:
        value = hymn({1: [{"en": "Sing^[Repeat the last two lines]"}]})

        markdown = page(value)

        self.assertIn("[Sing]{lang=en}", markdown)
        self.assertIn("singing-note", markdown)


class ResolutionTest(TestCase):
    """Which chorus a stanza takes, on the hymns where it had to be worked out."""

    def test_a_repeated_chorus_needs_no_note(self) -> None:
        value = hymn(
            {1: [{"en": "One"}], "1-chorus": [{"en": "A"}], 2: [{"en": "Two"}]}
        )

        self.assertNotIn("hymn-resolution", page(value))

    def test_a_chorus_that_changes_partway_says_where(self) -> None:
        # English keeps singing `1-chorus` under a new Chinese one, which is
        # the collection's own doing and the reason the rule exists.
        value = hymn(
            {
                1: [{"en": "One", "zh": "一"}],
                "1-chorus": [{"en": "A", "zh": "甲"}],
                2: [{"en": "Two", "zh": "二"}],
                "2-chorus": [{"zh": "乙"}],
                3: [{"en": "Three", "zh": "三"}],
            }
        )

        markdown = page(value)

        self.assertIn("Sung after stanzas 1–3 in English, 1 in Chinese", markdown)
        self.assertIn("Sung after stanzas 2–3 in Chinese", markdown)


class ScanTest(TestCase):
    """The pages of the two editions, and what to say when there are none."""

    def test_every_page_of_the_interval_is_shown(self) -> None:
        markdown = page(hymn({1: [{"en": "One"}]}), en=Edition("en", {1: (25, 26)}))

        self.assertIn("../scan/en/25.png", markdown)
        self.assertIn("../scan/en/26.png", markdown)

    def test_a_hymn_absent_from_an_edition_says_so(self) -> None:
        markdown = page(hymn({1: [{"zh": "一"}]}), en=Edition("en", {}))

        self.assertIn("hymn-absent", markdown)
        self.assertIn("not in the English edition", markdown)
        self.assertNotIn("../scan/en/", markdown)


class ChromeTest(TestCase):
    """What the page links to, and what it calls itself."""

    def test_the_source_link_points_at_the_file_a_typo_is_fixed_in(self) -> None:
        markdown = page(hymn({1: [{"en": "One"}]}), number=42)

        # data/42.md, never the generated Markdown this page was rendered from.
        self.assertIn("https://example.invalid/blob/main/data/42.md", markdown)
        self.assertIn("(../slide/42.html)", markdown)

    def test_the_ends_of_the_collection_link_only_inwards(self) -> None:
        first = page(hymn({1: [{"en": "One"}]}), number=1)
        self.assertNotIn("hymn-link-previous", first)
        self.assertIn("(2.html)", first)

        last = page(hymn({1: [{"en": "One"}]}), number=848)
        self.assertIn("(847.html)", last)
        self.assertNotIn("hymn-link-next", last)

    def test_the_page_is_not_indexed_beside_its_deck(self) -> None:
        # One entry per slide is the search index this site wants; the same
        # words again under a different URL is not a second match.
        self.assertIn("search: false", page(hymn({1: [{"en": "One"}]})))

    def test_the_tab_is_named_by_number_and_first_line(self) -> None:
        value = hymn({1: [{"en": "Come^[twice], all ye", "zh": "來罷"}]})

        self.assertEqual(page_title(value, 7), "7 Come, all ye 來罷")
