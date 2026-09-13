"""Tests for relating the three places the hymnal states a repeat."""

from unittest import TestCase

from hymn_projection.model import Hymn, Repeat
from hymn_projection.repeats import findings, named_lines


def hymn(
    *stanzas: list[str],
    meter: str | None = None,
    note: list[str] | None = None,
    repeat: str | None = None,
) -> Hymn:
    """Build a hymn whose stanzas are given as their lyric lines."""

    front = f"meter: {meter}\n" if meter else ""
    front += "".join(f"- {value}\n" for value in note or [])
    front = f"note:\n{front}" if note else front
    front += f"repeat:\n{repeat}\n" if repeat else ""
    body = "".join(
        f"\n# {index}\n\n" + "".join(f"{line}\n" for line in lines)
        for index, lines in enumerate(stanzas, start=1)
    )
    return Hymn.from_markdown(f"---\ncategory: 甲——乙\n{front}---\n{body}")


def kinds(value: Hymn) -> list[str]:
    return [finding.kind for finding in findings([(1, value)])]


LAST_LINE = "  lines:\n  - 4"


class ReadingADirectionTest(TestCase):
    """How many lines an English direction says are sung again."""

    def test_the_bare_direction_means_one_line(self) -> None:
        self.assertEqual(named_lines("Repeat the last line of each stanza"), 1)

    def test_a_number_written_as_a_word(self) -> None:
        self.assertEqual(named_lines("Repeat the last two lines"), 2)

    def test_a_number_written_as_a_figure(self) -> None:
        self.assertEqual(named_lines("Repeat the last 2 lines of each stanza"), 2)

    def test_the_article_the_hymnal_leaves_out(self) -> None:
        self.assertEqual(named_lines("Repeat last two lines of each stanza"), 2)

    def test_what_names_no_lines_at_all(self) -> None:
        self.assertIsNone(named_lines("第三節不唱“和”詩"))


class AccountingTest(TestCase):
    """Everything that asks for a repeat has to say which lines."""

    def test_a_hymn_that_asks_for_no_repeat(self) -> None:
        value = hymn(["一", "二", "三", "四"], meter="6.6.6.6.")

        self.assertEqual(kinds(value), [])

    def test_a_meter_that_asks_for_one_and_nothing_says_which(self) -> None:
        value = hymn(["一", "二", "三", "四"], meter="6.6.6.6. 重")

        self.assertEqual(
            kinds(value), ["a repeat the meter asks for is not written down"]
        )

    def test_a_note_that_orders_one_and_nothing_says_which(self) -> None:
        value = hymn(["一", "二", "三", "四"], note=["每節重唱最後一行"])

        self.assertEqual(
            kinds(value), ["a repeat a note orders is not written down"]
        )

    def test_a_meter_whose_repeat_the_lyrics_write_out(self) -> None:
        # The 11 hymns whose stanzas already end with their last line twice;
        # `notes.writes_the_repeat_out` is what sees them.
        value = hymn(["一", "二", "三", "四。", "四！"], meter="6.6.6.6. 重")

        self.assertEqual(kinds(value), [])

    def test_a_meter_whose_repeat_is_written_down(self) -> None:
        value = hymn(["一", "二", "三", "四"], meter="6.6.6.6. 重", repeat=LAST_LINE)

        self.assertEqual(kinds(value), [])

    def test_a_da_capo_is_not_a_repeat_this_field_can_hold(self) -> None:
        # 355's `回頭再唱正歌一遍` sends the singer back through the whole verse
        # after the chorus, which is not a tail of a stanza sung where it ends.
        value = hymn(["一", "二", "三", "四"], note=["回頭再唱正歌一遍"])

        self.assertEqual(kinds(value), [])


class AgreementTest(TestCase):
    """A repeat written down has to agree with what asked for it."""

    def test_a_repeat_that_nothing_asks_for(self) -> None:
        value = hymn(["一", "二", "三", "四"], meter="6.6.6.6.", repeat=LAST_LINE)

        self.assertEqual(
            kinds(value), ["a repeat is written down that nothing asks for"]
        )

    def test_a_repeat_written_down_and_written_out(self) -> None:
        value = hymn(
            ["一", "二", "三", "四。", "四！"], meter="6.6.6.6. 重", repeat=LAST_LINE
        )

        self.assertIn("a repeat is written down and written out", kinds(value))

    def test_a_repeat_shorter_than_the_note_it_stands_under(self) -> None:
        value = hymn(
            ["一", "二", "三", "四"],
            note=["Repeat the last two lines重複最後兩行"],
            repeat=LAST_LINE,
        )

        self.assertEqual(
            kinds(value),
            ["a repeat does not sing as many lines as its note names"],
        )

    def test_the_chinese_half_of_a_note_is_not_counted_against_it(self) -> None:
        # `zh/258` prints 242's direction as `第四節末兩行重唱一遍` and `en/266`
        # as `Repeat the last four lines`, because the Chinese page sets its
        # stanzas in two columns: two of its rows are four of these lines.
        value = hymn(
            ["一", "二", "三", "四"],
            note=["Repeat the last two lines第四節末一行重唱一遍"],
            repeat="  lines:\n  - 3\n  - 4",
        )

        self.assertEqual(kinds(value), [])

    def test_a_da_capo_only_the_score_asks_for(self) -> None:
        # 745 is marked *Fine* and *D.C.* on both pages and nowhere else, and
        # prints its last two lines twice with their own music.
        value = hymn(
            ["一", "二", "三", "四", "五，", "六；", "五，", "六。"],
            meter="特",
            repeat="  lines:\n  - 1\n  - 2\n  - 3",
        )

        self.assertEqual(findings([(745, value)]), [])
        self.assertEqual(
            kinds(value),
            [
                "a repeat is written down and written out",
                "a repeat is written down that nothing asks for",
            ],
        )


class ModelTest(TestCase):
    """What a repeat may name."""

    def test_a_repeat_naming_a_line_the_stanza_has_not(self) -> None:
        with self.assertRaises(ValueError):
            hymn(["一", "二"], meter="6.6. 重", repeat="  lines:\n  - 3")

    def test_a_repeat_naming_a_line_a_shorter_stanza_has_not(self) -> None:
        # The longest stanza has the line; the first, which also sings it, has not.
        with self.assertRaisesRegex(ValueError, "stanza 1"):
            hymn(["一", "二"], ["一", "二", "三", "四"], repeat="  lines:\n  - 3")

    def test_a_repeat_naming_a_stanza_the_hymn_has_not(self) -> None:
        with self.assertRaises(ValueError):
            hymn(
                ["一", "二"],
                meter="6.6. 重",
                repeat="  lines:\n  - 2\n  stanzas:\n  - 4",
            )

    def test_a_repeat_is_sung_in_every_stanza_unless_it_names_some(self) -> None:
        self.assertTrue(Repeat(lines=[4]).sung_in(3))
        self.assertTrue(Repeat(lines=[4], stanzas=[4]).sung_in(4))
        self.assertFalse(Repeat(lines=[4], stanzas=[4]).sung_in(3))

    def test_a_chorus_never_carries_the_stanza_repeat(self) -> None:
        self.assertFalse(Repeat(lines=[4]).sung_in("1-chorus"))
