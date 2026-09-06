"""Tests for reading a hymn's meter off the syllables of its Chinese lyrics."""

from unittest import TestCase

from hymn_projection.meters import (
    disagreements,
    implied,
    notation,
    printed,
    syllables,
)
from hymn_projection.model import Hymn


def hymn(meter: str | None, *stanzas: list[str]) -> Hymn:
    front = f"meter: {meter}\n" if meter else ""
    body = "".join(
        f"\n# {index}\n\n" + "".join(f"line {index}\n{line}\n" for line in lines)
        for index, lines in enumerate(stanzas, start=1)
    )
    return Hymn.from_markdown(f"---\ncategory: 甲——乙\n{front}---\n{body}")


class SyllableTest(TestCase):
    """Chinese is one syllable to the character, and punctuation is not sung."""

    def test_punctuation_does_not_count(self) -> None:
        self.assertEqual(syllables("但願我能像馬利亞，"), 8)

    def test_an_empty_line_is_no_syllables(self) -> None:
        self.assertEqual(syllables("，。！"), 0)


class NotationTest(TestCase):
    """Reading the hymnal's shorthand, and writing it back."""

    def test_a_meter_states_one_length_a_line(self) -> None:
        self.assertEqual(printed("8.6.8.6."), [8, 6, 8, 6])

    def test_a_doubled_meter_states_eight_lines(self) -> None:
        self.assertEqual(printed("8.7.8.7.D."), [8, 7, 8, 7, 8, 7, 8, 7])

    def test_what_follows_the_numbers_is_not_a_count(self) -> None:
        self.assertEqual(printed("6.6.8.6. 和"), [6, 6, 8, 6])

    def test_a_meter_of_no_numbers_states_nothing(self) -> None:
        self.assertIsNone(printed("特"))

    def test_eight_lines_that_repeat_are_written_doubled(self) -> None:
        self.assertEqual(notation([8, 7, 8, 7, 8, 7, 8, 7]), "8.7.8.7.D.")

    def test_four_equal_lines_are_not_a_doubled_meter(self) -> None:
        self.assertEqual(notation([8, 8, 8, 8]), "8.8.8.8.")


class ImpliedTest(TestCase):
    """What the lyrics themselves say the meter is."""

    def test_verses_that_agree_imply_their_meter(self) -> None:
        self.assertEqual(
            implied(hymn("8.6.8.6.", ["一二三四五六七八", "一二三四五六"] * 2)),
            "8.6.8.6.",
        )

    def test_verses_that_disagree_imply_nothing(self) -> None:
        self.assertIsNone(
            implied(hymn("8.6.8.6.", ["一二三四五六七八"], ["一二三四五六"]))
        )

    def test_the_chorus_is_not_counted(self) -> None:
        source = hymn("6.6.", ["一二三四五六"] * 2).to_markdown()
        with_chorus = source + "\n# 1-chorus\n\nchorus line\n一二三\n"

        self.assertEqual(implied(Hymn.from_markdown(with_chorus)), "6.6.")


class DisagreementTest(TestCase):
    """The report, whose shape is what says how to fix a hymn."""

    def test_a_hymn_that_scans_is_not_reported(self) -> None:
        scanning = hymn("6.6.", ["一二三四五六"] * 2)

        self.assertEqual(disagreements([(1, scanning)]), [])

    def test_a_hymn_with_no_meter_is_reported_as_such(self) -> None:
        found = disagreements([(1, hymn(None, ["一二三四五六"] * 2))])

        self.assertEqual([d.kind for d in found], ["no meter"])

    def test_one_verse_a_syllable_short_is_named_as_that(self) -> None:
        # The shape a dropped character makes.
        short = hymn("6.6.", ["一二三四五六", "一二三四五六"], ["一二三四五", "一二三四五六"])

        found = disagreements([(1, short)])

        self.assertEqual([d.kind for d in found], ["one verse, one syllable out"])
        self.assertEqual(found[0].stanzas[1][1], [5, 6])

    def test_every_verse_agreeing_on_another_meter_is_named_as_that(self) -> None:
        # The shape a mistyped meter makes.
        other = hymn("6.6.", ["一二三四五", "一二三四五"], ["一二三四五", "一二三四五"])

        found = disagreements([(1, other)])

        self.assertEqual([d.kind for d in found], ["every verse says the same other meter"])
        self.assertEqual(found[0].implied, "5.5.")

    def test_verses_that_disagree_with_each_other_are_named_as_that(self) -> None:
        ragged = hymn("6.6.", ["一二三四五六", "一二三"], ["一二三四五", "一二三四五六七"])

        found = disagreements([(1, ragged)])

        self.assertEqual([d.kind for d in found], ["verses disagree with each other"])
        self.assertIsNone(found[0].implied)


class IrregularTest(TestCase):
    """`Irregular Meter` / `特`, which states no lengths to count against."""

    def test_an_irregular_meter_states_no_lengths(self) -> None:
        self.assertIsNone(printed("Irregular Meter特"))

    def test_a_hymn_the_hymnal_calls_irregular_is_not_reported(self) -> None:
        ragged = hymn("Irregular Meter特", ["一二三四五六", "一二三"], ["一二三四五"])

        self.assertEqual(disagreements([(1, ragged)]), [])

    def test_a_hymn_with_no_meter_at_all_still_is(self) -> None:
        found = disagreements([(1, hymn(None, ["一二三四五六"], ["一二三"]))])

        self.assertEqual([d.kind for d in found], ["no meter"])


class DoubledMeterTest(TestCase):
    """The two editions count a chorus differently, and neither is wrong.

    Where the chorus is sung to the second half of a doubled tune, the English
    page writes `8.7.8.7.D.` and the Chinese page writes `8.7.8.7.和`. The
    eight lines are the verse and the chorus together.
    """

    def test_a_doubled_meter_may_be_the_verse_and_its_chorus(self) -> None:
        source = hymn("6.6.D.", ["一二三四五六", "一二三四五六"]).to_markdown()
        with_chorus = source + "\n# 1-chorus\n\nchorus line\n一二三四五六\n"
        with_chorus += "another\n一二三四五六\n"

        self.assertEqual(disagreements([(1, Hymn.from_markdown(with_chorus))]), [])

    def test_a_verse_short_of_the_doubled_meter_is_still_reported(self) -> None:
        source = hymn("6.6.D.", ["一二三四五六", "一二三四五"]).to_markdown()
        with_chorus = source + "\n# 1-chorus\n\nchorus line\n一二三四五六\n"
        with_chorus += "another\n一二三四五六\n"

        found = disagreements([(1, Hymn.from_markdown(with_chorus))])

        self.assertEqual(len(found), 1)
