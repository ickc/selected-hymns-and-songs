"""Tests for checking the hymnal's prose about a hymn against the hymn."""

from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.notes import chinese_number, findings


def hymn(*stanzas: list[str], note: list[str] | None = None) -> Hymn:
    """Build a hymn whose stanzas are given as their lyric lines."""

    front = "".join(f"- {value}\n" for value in note or [])
    front = f"note:\n{front}" if front else ""
    body = "".join(
        f"\n# {index}\n\n" + "".join(f"{line}\n" for line in lines)
        for index, lines in enumerate(stanzas, start=1)
    )
    return Hymn.from_markdown(f"---\ncategory: 甲——乙\n{front}---\n{body}")


def kinds(value: Hymn) -> list[str]:
    return [finding.kind for finding in findings([(1, value)])]


class NumberTest(TestCase):
    """Reading a stanza number the way the hymnal writes it."""

    def test_the_single_digits(self) -> None:
        self.assertEqual(chinese_number("一"), 1)
        self.assertEqual(chinese_number("五"), 5)
        self.assertEqual(chinese_number("九"), 9)

    def test_ten_and_past_it(self) -> None:
        self.assertEqual(chinese_number("十"), 10)
        self.assertEqual(chinese_number("十二"), 12)

    def test_what_is_not_a_number(self) -> None:
        self.assertIsNone(chinese_number("節"))


class GlossTest(TestCase):
    """A gloss is a word about a word, and has to be about the word it names."""

    def test_a_gloss_whose_word_is_in_its_line_is_let_be(self) -> None:
        value = hymn(["明亮晨星^[第一節的“明亮晨星”指主基督]的光華，"])

        self.assertEqual(kinds(value), [])

    def test_a_gloss_quoting_a_word_its_line_does_not_hold(self) -> None:
        value = hymn(["明亮晨星^[第一節的“晨曦”指主基督]的光華，"])

        self.assertEqual(
            kinds(value), ["a gloss quotes a word its line does not hold"]
        )

    def test_the_quoted_word_may_be_capitalized_as_the_hymnal_does(self) -> None:
        # 768 glosses `“Truth”` on a line that prints `truth`.
        value = hymn(["In spirit and in truth^[“Truth” in the first stanza refers to Christ]!"])

        self.assertEqual(kinds(value), [])

    def test_a_gloss_naming_another_stanza_than_its_own(self) -> None:
        value = hymn(["一"], ["明亮晨星^[第一節的“明亮晨星”指主基督]的光華，"])

        self.assertEqual(
            kinds(value), ["a gloss names another stanza than its own"]
        )

    def test_a_direction_written_as_a_gloss_belongs_in_the_front_matter(self) -> None:
        # What `data/` held on 242, 355, 393, 734, 813 and 830 before the two
        # kinds were told apart.
        value = hymn(["興起建造敎會！^[第四節末兩行重唱一遍]"])

        self.assertIn("a direction is written as a gloss", kinds(value))


class NoteTest(TestCase):
    """A note about the other edition has to agree with the stanzas."""

    def test_a_note_naming_a_missing_english_stanza_that_is_missing(self) -> None:
        value = hymn(["One", "一"], ["二"], note=["英詩無第二節"])

        self.assertEqual(kinds(value), [])

    def test_a_note_naming_a_missing_english_stanza_the_hymn_has(self) -> None:
        value = hymn(["One", "一"], ["Two", "二"], note=["英詩無第二節"])

        self.assertEqual(
            kinds(value), ["a note names an English stanza the hymn has"]
        )

    def test_a_note_listing_the_english_stanzas_that_lists_them_right(self) -> None:
        value = hymn(
            ["One", "一"], ["二"], ["Three", "三"], note=["英詩僅有一、三等二節"]
        )

        self.assertEqual(kinds(value), [])

    def test_a_note_listing_the_wrong_english_stanzas(self) -> None:
        value = hymn(
            ["One", "一"], ["二"], ["Three", "三"], note=["英詩僅有一、二等二節"]
        )

        self.assertEqual(kinds(value), ["a note names the wrong English stanzas"])

    def test_a_note_counting_the_chinese_stanzas_right(self) -> None:
        value = hymn(["One", "一"], ["Two", "二"],
                     note=["The Chinese version has 2 stanzas"])

        self.assertEqual(kinds(value), [])

    def test_a_note_counting_the_wrong_number_of_chinese_stanzas(self) -> None:
        value = hymn(["One", "一"], ["Two", "二"],
                     note=["The Chinese version has 4 stanzas"])

        self.assertEqual(
            kinds(value), ["a note counts the wrong number of Chinese stanzas"]
        )

    def test_a_repeat_both_directed_and_written_out(self) -> None:
        # 274 carried a direction neither page prints over lyrics that print
        # the repeat; this is that shape.
        value = hymn(["一", "二", "二"], note=["重唱每節最後一行"])

        self.assertEqual(
            kinds(value), ["a repeat is both directed and written out"]
        )

    def test_a_direction_not_to_repeat_may_stand_over_a_written_repeat(self) -> None:
        # 734's chorus is written out under every stanza and the note says to
        # leave it off after the last, which is not a contradiction.
        value = hymn(["一", "二", "二"], note=["第三節不唱“和”詩"])

        self.assertEqual(kinds(value), [])
