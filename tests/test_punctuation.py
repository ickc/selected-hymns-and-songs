"""Tests for checking a lyric line against the marks its edition sets."""

from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.punctuation import findings


def hymn(*lines: str) -> Hymn:
    """Build a one-stanza hymn from its lyric lines."""

    body = "".join(f"{line}\n" for line in lines)
    return Hymn.from_markdown(f"---\ncategory: 甲——乙\n---\n\n# 1\n\n{body}")


def kinds(value: Hymn) -> list[str]:
    return [finding.kind for finding in findings([(1, value)])]


class AlphabetTest(TestCase):
    """Each edition is written with its own marks and no others."""

    def test_the_ordinary_line_of_each_edition_is_let_be(self) -> None:
        value = hymn("’Tis grace that makes us free—", "是恩典使我們自由——")

        self.assertEqual(kinds(value), [])

    def test_a_halfwidth_mark_among_the_fullwidth_ones(self) -> None:
        value = hymn("O Father of glory,", "哦,榮耀的父神，")

        self.assertEqual(kinds(value), ["a mark the edition does not set"])

    def test_a_straight_apostrophe_is_not_the_mark_the_book_sets(self) -> None:
        value = hymn("'Tis mercy all, immense and free;", "何等憐憫，何等自由；")

        self.assertEqual(kinds(value), ["a mark the edition does not set"])

    def test_an_apostrophe_the_wrong_way_round_either(self) -> None:
        value = hymn("‘Neath the shadow of His wing", "在祂翅膀蔭下")

        self.assertEqual(kinds(value), ["a mark the edition does not set"])

    def test_a_gloss_is_not_read_as_part_of_the_line(self) -> None:
        # The gloss is Markdown, so its brackets and caret are not the page's
        # marks and must not be judged as if they were.
        value = hymn("None shall move me from Beulah^[Meaning, married] Land.")

        self.assertEqual(kinds(value), [])

    def test_a_dash_written_singly_in_a_chinese_line(self) -> None:
        value = hymn("你耳所常愛聽聞—")

        self.assertEqual(kinds(value), ["a dash written singly"])

    def test_a_line_padded_out_to_a_column_width(self) -> None:
        # 607's stanzas were padded with ideographic spaces to line up the
        # second column `zh/647` prints them in.
        value = hymn("你們能否順從　　　所事奉的主，")

        self.assertEqual(kinds(value), ["a line padded to a column width"])

    def test_one_space_marks_a_half_line_and_is_allowed(self) -> None:
        value = hymn("你們能否順從 你一切的主，")

        self.assertEqual(kinds(value), [])


class BoundaryTest(TestCase):
    """A mark stays on the side of the break that its text is on."""

    def test_a_line_beginning_with_a_closing_quote(self) -> None:
        value = hymn("“靠耶穌血有安息！", "”這是何等安息。")

        self.assertEqual(kinds(value), ["a line begins with a closing mark"])

    def test_a_line_beginning_with_a_dash(self) -> None:
        # The dash breaks off from what precedes it, and `zh/265` sets it there.
        value = hymn("“開了，就沒有人能關。”", "——祂說了，照樣成全。")

        self.assertEqual(kinds(value), ["a line begins with a closing mark"])

    def test_a_line_ending_with_an_opening_quote(self) -> None:
        value = hymn("我們聽你如此說：“", "我們理當歡喜快樂。”")

        self.assertEqual(kinds(value), ["a line ends with an opening mark"])


class PairingTest(TestCase):
    """Quotation marks pair off, strictly in Chinese and loosely in English."""

    def test_a_chinese_quotation_the_hymn_does_not_close(self) -> None:
        value = hymn("“主，你已經有九十九，")

        self.assertEqual(kinds(value), ["a quotation the hymn does not close"])

    def test_an_english_quotation_closed_before_it_was_opened(self) -> None:
        value = hymn("Re-echoes—”God is love.”")

        self.assertEqual(
            kinds(value), ["a quotation closed before it was opened"]
        )

    def test_english_may_open_in_each_stanza_and_close_only_at_the_end(self) -> None:
        # 345 sets one speech running through five stanzas that way.
        value = Hymn.from_markdown(
            "---\ncategory: 甲——乙\n---\n\n# 1\n\n“Fear not, I am with thee,\n"
            "\n# 2\n\n“I’ll never forsake!”\n"
        )

        self.assertEqual(kinds(value), [])
