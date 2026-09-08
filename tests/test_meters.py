"""Tests for reading a hymn's meter off the syllables of its Chinese lyrics."""

from unittest import TestCase

from hymn_projection.meters import (
    chorus_disagreements,
    disagreements,
    repeats,
    implied,
    notation,
    printed,
    shape,
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


def chorused(meter: str | None, *stanzas: tuple[str, list[str]]) -> Hymn:
    """Build a hymn whose stanzas are named, so a chorus can be one of them."""

    front = f"meter: {meter}\n" if meter else ""
    body = "".join(
        f"\n# {name}\n\n" + "".join(f"line\n{line}\n" for line in lines)
        for name, lines in stanzas
    )
    return Hymn.from_markdown(f"---\ncategory: 甲——乙\n{front}---\n{body}")


class SyllableTest(TestCase):
    """Chinese is one syllable to the character, and punctuation is not sung."""

    def test_punctuation_does_not_count(self) -> None:
        self.assertEqual(syllables("但願我能像馬利亞，"), 8)

    def test_an_empty_line_is_no_syllables(self) -> None:
        self.assertEqual(syllables("，。！"), 0)

    def test_a_note_beside_the_line_is_not_sung_in_it(self) -> None:
        # The hymnal's own direction, which `data/N.md` keeps as an inline
        # note. 830 prints one and used to count as nine syllables long.
        self.assertEqual(syllables("求你快回來。^[重唱「求你快回來」兩次。]"), 5)


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


class RepeatTest(TestCase):
    """`重` / `with repeat`: sing the last line, or the last phrase, twice."""

    def test_a_meter_with_no_repeat_offers_only_its_lengths(self) -> None:
        self.assertEqual(repeats("8.6.8.6.", [8, 6, 8, 6]), [[8, 6, 8, 6]])

    def test_a_repeat_offers_every_tail_sung_again(self) -> None:
        self.assertIn([8, 6, 8, 6, 6], repeats("8.6.8.6. 重", [8, 6, 8, 6]))
        self.assertIn([8, 6, 8, 6, 8, 6], repeats("8.6.8.6. 重", [8, 6, 8, 6]))

    def test_a_verse_that_writes_the_repeat_out_scans(self) -> None:
        # 82 writes its repeated last line as a line of its own.
        written = hymn("6.5. 重", ["一二三四五六", "一二三四五", "一二三四五"])

        self.assertEqual(disagreements([(1, written)]), [])

    def test_a_verse_that_does_not_write_it_out_scans_too(self) -> None:
        # 57 and 71 leave the repeat to the singer, and both are right.
        plain = hymn("6.5. 重", ["一二三四五六", "一二三四五"])

        self.assertEqual(disagreements([(1, plain)]), [])


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

        self.assertEqual([d.kind for d in found], ["syllables are missing or added"])
        self.assertEqual(found[0].implied, "5.5.")

    def test_verses_that_disagree_with_each_other_are_named_as_that(self) -> None:
        ragged = hymn("6.6.", ["一二三四五六", "一二三"], ["一二三四五", "一二三四五六七"])

        found = disagreements([(1, ragged)])

        self.assertEqual([d.kind for d in found], ["syllables are missing or added"])
        self.assertIsNone(found[0].implied)

    def test_a_verse_the_chinese_does_not_have_is_not_a_short_verse(self) -> None:
        # 840 prints five English stanzas over one Chinese one, and says so on
        # its English page. Counting the four as zero made it the worst
        # disagreement in the collection.
        source = hymn("6.6.", ["一二三四五六", "一二三四五六"]).to_markdown()
        english_only = source + "\n# 2\n\nEnglish alone\nMore English\n"

        self.assertEqual(disagreements([(1, Hymn.from_markdown(english_only))]), [])


class LineationTest(TestCase):
    """Whether the syllables are all there, and whether the lines are the page's.

    A verse is one run of syllables cut into lines, so a meter and a stanza
    can differ in two quite different ways: on what they hold, which is a
    finding about the text, or only on where they cut it, which is a finding
    about nothing at all when the book itself cuts it both ways.
    """

    def test_lines_that_hold_the_meter_joined_are_not_a_missing_syllable(self) -> None:
        # 617's page states `7.6.7.6.雙` over rows of thirteen characters.
        joined = hymn("6.5.", ["一二三四五六七八九十甲"], ["一二三四五六七八九十甲"])

        found = disagreements([(1, joined)])

        self.assertEqual(
            [d.kind for d in found],
            ["the meter counts a break the lines do not print"],
        )

    def test_lines_that_cut_the_meter_finer_are_not_either(self) -> None:
        # 137's page states `13.13.13.13.` over the same shape 617 calls 7.6.
        split = hymn(
            "11.11.",
            ["一二三四五六", "七八九十甲", "一二三四五六", "七八九十甲"],
            ["一二三四五六", "七八九十甲", "一二三四五六", "七八九十甲"],
        )

        found = disagreements([(1, split)])

        self.assertEqual(
            [d.kind for d in found],
            ["the lines print a break the meter does not count"],
        )

    def test_a_break_in_neither_place_is_named_as_moved(self) -> None:
        # The whole verse is present and cut where it cannot be sung, so one
        # of the two readings of this verse is wrong.
        moved = hymn("8.6.", ["一二三四五六七八", "一二三四五六"], ["一二三四五六", "七八九十甲乙丙丁"])

        found = disagreements([(1, moved)])

        self.assertEqual([d.kind for d in found], ["a line break is in a different place"])

    def test_the_worst_of_several_is_the_one_named(self) -> None:
        # A hymn may be several at once, and the missing syllable is the one
        # worth reading a page over.
        both = hymn(
            "8.6.",
            ["一二三四五六", "七八九十甲乙丙丁"],
            ["一二三四五六七八", "一二三四五"],
        )

        found = disagreements([(1, both)])

        self.assertEqual([d.kind for d in found], ["syllables are missing or added"])
        self.assertEqual(
            found[0].kinds,
            ["syllables are missing or added", "a line break is in a different place"],
        )


class IrregularTest(TestCase):
    """`Irregular Meter` / `特`, which states no lengths to count against."""

    def test_an_irregular_meter_states_no_lengths(self) -> None:
        self.assertIsNone(printed("Irregular Meter特"))

    def test_verses_that_agree_are_not_reported(self) -> None:
        # An irregular meter is the hymnal declining to name a pattern no
        # other tune shares, not a hymn that cannot be counted.
        even = hymn("Irregular Meter特", ["一二三四五六", "一二三"], ["六五四三二一", "三二一"])

        self.assertEqual(disagreements([(1, even)]), [])

    def test_verses_that_do_not_agree_still_are(self) -> None:
        # The only check these 93 hymns can have: the verses against each other.
        ragged = hymn("Irregular Meter特", ["一二三四五六", "一二三"], ["一二三四五"])

        found = disagreements([(1, ragged)])

        self.assertEqual([d.kind for d in found], ["syllables are missing or added"])

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


class DoubledChorusTest(TestCase):
    """Where the verse is half a doubled meter, the chorus is the other half.

    A hymn whose verses are all exactly half of what the meter states has
    nothing wrong with its verses: what does not scan is the chorus meant to
    complete them, and the report says so by holding the two together.
    """

    def test_the_finding_is_reported_against_verse_and_chorus(self) -> None:
        source = hymn("6.6.D.", ["一二三四五六", "一二三四五六"]).to_markdown()
        with_chorus = source + "\n# 1-chorus\n\nchorus line\n一二三四五\n"
        with_chorus += "another\n一二三四五六\n"

        found = disagreements([(1, Hymn.from_markdown(with_chorus))])

        self.assertEqual([d.stanzas for d in found], [[(1, [6, 6, 5, 6])]])


class ShapeTest(TestCase):
    """The count a hymn always has, whatever the hymnal prints over it."""

    def test_the_shape_counts_the_chorus_too(self) -> None:
        sung = chorused(
            None, ("1", ["一二三四"]), ("1-chorus", ["一二三"]), ("2", ["五六七八"])
        )

        self.assertEqual(
            shape(sung), [(1, [4]), ("1-chorus", [3]), (2, [4])]
        )


class ChorusTest(TestCase):
    """Every chorus is sung to the same strain, so all of them scan alike."""

    def test_choruses_of_one_length_are_not_reported(self) -> None:
        sung = chorused(
            None, ("1", ["一二三四"]), ("1-chorus", ["一二三"]),
            ("2", ["五六七八"]), ("2-chorus", ["四五六"]),
        )

        self.assertEqual(chorus_disagreements([(1, sung)]), [])

    def test_a_chorus_a_syllable_out_is_reported(self) -> None:
        sung = chorused(
            None, ("1", ["一二三四"]), ("1-chorus", ["一二三"]),
            ("2", ["五六七八"]), ("2-chorus", ["四五六七"]),
        )

        found = chorus_disagreements([(1, sung)])

        self.assertEqual([f.number for f in found], [1])
        self.assertEqual(found[0].choruses, [("1-chorus", [3]), ("2-chorus", [4])])

    def test_a_hymn_with_one_chorus_has_nothing_to_compare(self) -> None:
        sung = chorused(None, ("1", ["一二三四"]), ("1-chorus", ["一二三"]))

        self.assertEqual(chorus_disagreements([(1, sung)]), [])
