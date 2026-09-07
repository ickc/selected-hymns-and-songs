"""Tests for the metrical index, a projection of the whole collection."""

from unittest import TestCase

from hymn_projection.meterindex import sort_key, to_markdown
from hymn_projection.model import Hymn


def hymn(meter: str, tune: str | list[str] | None = "Azmon") -> Hymn:
    """One hymn carrying a meter and, unless it is a supplement one, a tune."""

    front = "" if tune is None else f"tune: {tune}\n"
    return Hymn.from_markdown(
        f"---\ncategory: 讚美和敬拜——三一神\nmeter: {meter}\n{front}---\n\n# 1\n\nSing\n唱\n"
    )


def bilingual(english: str, chinese: str, tune: str | None = "Azmon") -> Hymn:
    """One hymn whose two editions write the same meter differently."""

    front = "" if tune is None else f"tune: {tune}\n"
    return Hymn.from_markdown(
        f"---\ncategory: 讚美和敬拜——三一神\nmeter:\n  en: {english}\n  zh: {chinese}\n"
        f"{front}---\n\n# 1\n\nSing\n唱\n"
    )


class OrderTest(TestCase):
    """How the hymnal files a meter, which is neither numeric nor alphabetical."""

    def test_the_figures_are_read_as_a_sequence_not_as_a_number(self) -> None:
        # `10.` comes after `9.`, where sorting the text would put it after `1.`.
        meters = ["10.10.10.10.", "9.8.9.8.", "1.2.3.4."]

        self.assertEqual(
            sorted(meters, key=sort_key), ["1.2.3.4.", "9.8.9.8.", "10.10.10.10."]
        )

    def test_a_shorter_run_of_figures_comes_before_the_run_that_extends_it(self) -> None:
        meters = ["10.10.9.6. with chorus", "10.10."]

        self.assertEqual(
            sorted(meters, key=sort_key), ["10.10.", "10.10.9.6. with chorus"]
        )

    def test_the_same_figures_are_filed_plain_then_marked_then_qualified(self) -> None:
        # The order the printed index runs 8.7.8.7. in, doubled forms after all
        # of the undoubled ones.
        meters = [
            "8.7.8.7.D. with chorus",
            "8.7.8.7. with chorus",
            "8.7.8.7.D.",
            "8.7.8.7.",
            "8.7.8.7. (I)",
            "8.7.8.7.D. with repeat",
        ]

        self.assertEqual(
            sorted(meters, key=sort_key),
            [
                "8.7.8.7.",
                "8.7.8.7. (I)",
                "8.7.8.7. with chorus",
                "8.7.8.7.D.",
                "8.7.8.7.D. with repeat",
                "8.7.8.7.D. with chorus",
            ],
        )

    def test_the_meter_that_states_no_lengths_is_filed_last(self) -> None:
        meters = ["Irregular Meter", "16.16.9.9.", "4.8.4.6."]

        self.assertEqual(
            sorted(meters, key=sort_key), ["4.8.4.6.", "16.16.9.9.", "Irregular Meter"]
        )

    def test_a_notation_the_index_cannot_file_is_an_error_not_a_guess(self) -> None:
        with self.assertRaises(ValueError):
            sort_key("Long Meter")
        with self.assertRaises(ValueError):
            sort_key("8.8.8.8. with descant")


class IndexTest(TestCase):
    """What the page says: every hymn, under its meter and under its tune."""

    def test_each_tune_lists_the_hymns_set_to_it_in_number_order(self) -> None:
        markdown = to_markdown([(46, hymn("6.5.6.5.D.", "Evelyns")), (607, hymn("6.5.6.5.D.", "Evelyns"))])

        self.assertIn(
            "[[Evelyns]{lang=en}]{.tune-name} "
            "[[46](hymn/46.html), [607](hymn/607.html)]{.tune-hymns}",
            markdown,
        )

    def test_one_meter_heads_the_tunes_filed_under_it(self) -> None:
        markdown = to_markdown(
            [(46, hymn("6.5.6.5.D.", "Evelyns")), (605, hymn("6.5.6.5.D.", "Longstaff"))]
        )

        self.assertEqual(markdown.count("## "), 1)
        self.assertIn("## [6.5.6.5.D.]{lang=en} {#meter-6-5-6-5-d}", markdown)
        self.assertEqual(markdown.count(".tune-entry"), 2)

    def test_a_hymn_printed_to_two_tunes_appears_under_both(self) -> None:
        markdown = to_markdown([(146, hymn("8.6.8.6.", ["Azmon", "Lyngham"]))])

        self.assertIn("Azmon]{lang=en}]{.tune-name} [[146]", markdown)
        self.assertIn("Lyngham]{lang=en}]{.tune-name} [[146]", markdown)

    def test_a_supplement_hymn_files_under_its_meter_with_no_tune(self) -> None:
        # The printed index stops at 764 because the tune indexes do. A meter
        # is the whole point of the page, and every hymn has one.
        markdown = to_markdown([(800, hymn("8.6.8.6.", None))])

        self.assertIn("## [8.6.8.6.]{lang=en} [(Common Meter)]{.meter-named}", markdown)
        self.assertIn(
            "[[supplement]{lang=en} [補篇]{lang=zh-Hant}]{.tune-name .meter-untuned} "
            "[[800](hymn/800.html)]{.tune-hymns}",
            markdown,
        )

    def test_the_supplement_is_listed_after_the_tunes_that_are_named(self) -> None:
        markdown = to_markdown(
            [(60, hymn("8.6.8.6.", "Azmon")), (800, hymn("8.6.8.6.", None))]
        )

        self.assertLess(markdown.index("Azmon"), markdown.index(".meter-untuned"))

    def test_a_heading_carries_the_chinese_half_where_there_is_one(self) -> None:
        markdown = to_markdown([(7, bilingual("8.7.8.7. with chorus", "8.7.8.7. 和"))])

        self.assertIn(
            "## [8.7.8.7. with chorus]{lang=en} [8.7.8.7. 和]{lang=zh-Hant} "
            "{#meter-8-7-8-7-with-chorus}",
            markdown,
        )

    def test_a_meter_both_editions_print_alike_heads_its_section_once(self) -> None:
        markdown = to_markdown([(1, hymn("8.7.8.7.D."))])

        self.assertIn("## [8.7.8.7.D.]{lang=en} {#meter-8-7-8-7-d}", markdown)
        self.assertNotIn("lang=zh-Hant]", markdown.split("\n## ")[1].split("\n")[0])

    def test_the_irregular_heading_drops_the_qualifier_that_is_the_hymns(self) -> None:
        # 特, 特.和 and 特.重 are one heading: the chorus and the repeat belong
        # to the hymn, not to the refusal to count it.
        markdown = to_markdown(
            [(830, bilingual("Irregular Meter", "特.和")), (840, bilingual("Irregular Meter", "特"))]
        )

        self.assertEqual(markdown.count("## "), 1)
        self.assertIn(
            "## [Irregular Meter]{lang=en} [特]{lang=zh-Hant} {#meter-irregular-meter}",
            markdown,
        )

    def test_the_figures_lead_to_the_first_meter_that_opens_with_them(self) -> None:
        markdown = to_markdown(
            [
                (1, hymn("8.6.8.6.")),
                (2, hymn("8.8.8.8.")),
                (3, hymn("9.8.9.8.")),
                (4, bilingual("Irregular Meter", "特")),
            ]
        )

        self.assertIn(
            "[8](#meter-8-6-8-6) [9](#meter-9-8-9-8) "
            "[[特]{lang=zh-Hant}](#meter-irregular-meter)",
            markdown,
        )

    def test_a_hymn_with_no_meter_is_an_error_rather_than_a_silent_omission(self) -> None:
        nameless = Hymn.from_markdown(
            "---\ncategory: 讚美和敬拜——三一神\n---\n\n# 1\n\nSing\n唱\n"
        )

        with self.assertRaises(ValueError):
            to_markdown([(1, nameless)])
