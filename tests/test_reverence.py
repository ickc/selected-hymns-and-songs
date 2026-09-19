"""Tests for the pronouns read off the page, and for what holds without them."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.reverence import (
    HEADER,
    Reading,
    apply,
    findings,
    read_ledger,
    rewrite,
)


def hymn(*lines: str) -> Hymn:
    """Build a one-stanza hymn from its lyric lines."""

    body = "".join(f"{line}\n" for line in lines)
    return Hymn.from_markdown(f"---\ncategory: 甲——乙\n---\n\n# 1\n\n{body}")


def kinds(*hymns: tuple[int, Hymn], readings: list[Reading] | None = None) -> list[str]:
    return [finding.kind for finding in findings(list(hymns), readings or [])]


def table(directory: Path, *rows: tuple[object, ...]) -> Path:
    """Write a ledger of the given rows and return its path."""

    path = directory / "reverence.tsv"
    lines = ["\t".join(HEADER)]
    lines += ["\t".join("" if cell is None else str(cell) for cell in row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class LedgerTest(TestCase):
    """The table is a reading of a page, and says so or is refused."""

    def test_a_row_is_read_with_its_page(self) -> None:
        with TemporaryDirectory() as name:
            path = table(Path(name), (55, 1, 3, 2, "祢", 82, "神在你身顯着！"))

            reading, = read_ledger(path)

        self.assertEqual(reading.key, (55, "1", 3, 2))
        self.assertEqual((reading.pronoun, reading.page), ("祢", 82))

    def test_a_row_may_say_the_chinese_edition_prints_no_such_line(self) -> None:
        # 404's fourth stanza is in the English edition and in `data/`, and
        # `zh/425` ends the hymn at its third.
        with TemporaryDirectory() as name:
            path = table(Path(name), (404, 4, 0, 3, "祢", None, "我尋求你同在，"))

            reading, = read_ledger(path)

        self.assertIsNone(reading.page)

    def test_a_pronoun_the_hymnal_does_not_set(self) -> None:
        with TemporaryDirectory() as name:
            path = table(Path(name), (55, 1, 0, 0, "袮", 82, "你名何等芬芳"))

            with self.assertRaisesRegex(ValueError, "is not one of"):
                read_ledger(path)

    def test_an_offset_that_is_not_a_pronoun(self) -> None:
        with TemporaryDirectory() as name:
            path = table(Path(name), (55, 1, 0, 1, "祢", 82, "你名何等芬芳"))

            with self.assertRaisesRegex(ValueError, "is not a pronoun"):
                read_ledger(path)

    def test_one_pronoun_read_twice(self) -> None:
        with TemporaryDirectory() as name:
            path = table(
                Path(name),
                (55, 1, 0, 0, "祢", 82, "你名何等芬芳"),
                (55, 1, 0, 0, "你", 82, "你名何等芬芳"),
            )

            with self.assertRaisesRegex(ValueError, "is already read"):
                read_ledger(path)


class RewriteTest(TestCase):
    """Applying a reading writes it at the offset it was read at."""

    def test_the_offset_the_reading_names_is_the_one_that_changes(self) -> None:
        value = hymn("耶穌！你名何等芬芳，你名何等芬芳。")
        reading = Reading(1, "1", 0, 3, "祢", 8, "耶穌！你名何等芬芳，你名何等芬芳。")

        # The line prints the pronoun twice and the reading names one of them.
        self.assertIn(
            "耶穌！祢名何等芬芳，你名何等芬芳。", rewrite(1, value, [reading])
        )

    def test_a_line_that_has_changed_since_it_was_read_is_refused(self) -> None:
        value = hymn("耶穌！你名何等芬芳，")
        reading = Reading(1, "1", 0, 3, "祢", 8, "耶穌！你名何等甘甜，")

        with self.assertRaisesRegex(ValueError, "and the table read"):
            rewrite(1, value, [reading])

    def test_the_line_may_have_been_corrected_to_the_reading_already(self) -> None:
        # Idempotence: the reading is written into `data/`, and reading the
        # table back against what it wrote must not then refuse it.
        value = hymn("耶穌！祢名何等芬芳，")
        reading = Reading(1, "1", 0, 3, "祢", 8, "耶穌！你名何等芬芳，")

        self.assertIn("耶穌！祢名何等芬芳，", rewrite(1, value, [reading]))

    def test_a_row_for_a_hymn_that_is_not_here(self) -> None:
        with TemporaryDirectory() as name:
            directory = Path(name)
            (directory / "1.md").write_text(hymn("你名").to_markdown(), encoding="utf-8")
            reading = Reading(2, "1", 0, 0, "祢", 8, "你名")

            with self.assertRaisesRegex(ValueError, "read a hymn that is not here"):
                apply([directory / "1.md"], [reading])


class ConsistencyTest(TestCase):
    """One printed line spells its pronouns one way wherever it is printed."""

    def test_two_printings_of_a_line_that_agree(self) -> None:
        one = hymn("主耶穌，我求祢快來，")
        other = hymn("主耶穌，我求祢快來！")

        self.assertEqual(kinds((830, one), (831, other)), [])

    def test_two_printings_of_a_line_that_do_not(self) -> None:
        # How 830 was caught: the layer read one copy of its last line and not
        # the other, and the closing mark differs between the two copies.
        one = hymn("主耶穌，我求祢快來，")
        other = hymn("主耶穌，我求你快來！")

        self.assertEqual(kinds((830, one), (831, other)), ["one line spelled two ways"])

    def test_a_line_with_no_pronoun_in_it_is_not_compared(self) -> None:
        self.assertEqual(kinds((1, hymn("我心、我靈眞要湧出讚美，"))), [])


class ThouTest(TestCase):
    """A plain 你 under an English ``Thou`` was read off the page or is wrong."""

    def test_an_unread_plain_you_under_thou(self) -> None:
        value = hymn("When we see Thee, as the victim,", "看你身懸十字苦架，")

        self.assertEqual(
            kinds((165, value)), ["a plain 你 where the English says Thou"]
        )

    def test_the_same_pronoun_once_it_has_been_read(self) -> None:
        # 423 is the hymnal addressing the believer as *thee*, and its 你 is
        # what `zh/444` prints; the row is what says a person looked.
        value = hymn("What have I giv’n for Thee?", "爲我，你舍何情？")
        reading = Reading(423, "1", 0, 3, "你", 444, "爲我，你舍何情？")

        self.assertEqual(kinds((423, value), readings=[reading]), [])

    def test_a_reverential_pronoun_under_thou_is_nothing_to_report(self) -> None:
        value = hymn("How great Thou art,", "祢眞偉大！")

        self.assertEqual(kinds((8, value)), [])

    def test_a_modern_you_says_nothing_about_the_chinese(self) -> None:
        # The collection's later material addresses God as *you*, so the
        # English witness is read in one direction only.
        value = hymn("Heavenly Father, I appreciate you,", "親愛天父，我感謝你，")

        self.assertEqual(kinds((4, value)), [])


class FeminineTest(TestCase):
    """妳 is the feminine pronoun and belongs to two hymns."""

    def test_the_two_hymns_it_belongs_to(self) -> None:
        value = hymn("女子阿，妳當思想，")

        self.assertEqual(kinds((109, value)), [])

    def test_anywhere_else(self) -> None:
        value = hymn("我們敬拜，因妳所是，")

        self.assertEqual(
            kinds((1, value)),
            ["the feminine 妳 outside the two hymns it belongs to"],
        )
