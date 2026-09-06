"""Tests for the subject table and the preprocessing step that applies it."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.categories import (
    HEADER,
    Subject,
    apply,
    localized,
    read_mapping,
    read_table,
    rewrites,
    write_table,
)
from hymn_projection.model import Hymn


HYMN = """---
category: 讚美和敬拜——三一神
meter: 8.7.8.7.D.
---

# 1

God, our Father, we adore Thee!
阿爸父神，我們拜你，
"""

ENGLISH = "Praise and Worship—The Trinity"
TRINITY = ("1", "1", "", "讚美和敬拜", "三一神", "", "Praise and Worship", "The Trinity", "")
FIRE = ("2", "1", "", "聖靈", "火", "", "The Holy Spirit", "The Fire", "")


def table(directory: Path, rows: list[tuple[str, ...]]) -> Path:
    path = directory / "categories.tsv"
    body = "".join("\t".join(row) + "\n" for row in rows)
    path.write_text("\t".join(HEADER) + "\n" + body, encoding="utf-8")
    return path


def hymns(directory: Path, sources: list[str]) -> list[Path]:
    paths = []
    for number, source in enumerate(sources, start=1):
        path = directory / f"{number}.md"
        path.write_text(source, encoding="utf-8")
        paths.append(path)
    return paths


class SubjectTest(TestCase):
    """One row, and the two strings the hymnal prints it as."""

    def test_two_levels_join_with_the_dash_each_edition_uses(self) -> None:
        subject = Subject((1, 1), ("讚美和敬拜", "三一神"), ("Praise and Worship", "The Trinity"))

        self.assertEqual(subject.chinese, "讚美和敬拜——三一神")
        self.assertEqual(subject.english, ENGLISH)

    def test_a_third_level_is_parenthesized_as_the_book_prints_it(self) -> None:
        subject = Subject(
            (1, 2, 1),
            ("讚美和敬拜", "聖父", "祂的偉大"),
            ("Praise and Worship", "The Father", "His Greatness"),
        )

        self.assertEqual(subject.chinese, "讚美和敬拜——聖父（祂的偉大）")
        self.assertEqual(subject.english, "Praise and Worship—The Father (His Greatness)")
        self.assertEqual(subject.depth, 3)


class TableTest(TestCase):
    """The hand-edited file, which has to say what it means or fail loudly."""

    def test_a_table_round_trips_through_the_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "categories.tsv"
            subjects = read_table(table(Path(directory), [TRINITY, FIRE]))

            write_table(subjects, path)

            self.assertEqual(read_table(path), subjects)

    def test_the_order_of_the_file_is_the_order_of_the_book(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(
                Path(directory),
                [
                    ("1", "1", "1", "一", "二", "甲", "One", "Two", "A"),
                    ("1", "1", "2", "一", "二", "乙", "One", "Two", "B"),
                ],
            )

            self.assertEqual([s.number for s in read_table(path)], [(1, 1, 1), (1, 1, 2)])

    def test_a_missing_header_is_named_as_the_problem(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "categories.tsv"
            path.write_text("\t".join(TRINITY) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "header"):
                read_table(path)

    def test_a_row_missing_its_translation_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [TRINITY[:7] + ("", "")])

            with self.assertRaisesRegex(ValueError, "line 2"):
                read_table(path)

    def test_half_a_third_level_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            row = ("1", "1", "1", "讚美和敬拜", "聖父", "祂的偉大", "Praise", "The Father", "")
            path = table(Path(directory), [row])

            with self.assertRaisesRegex(ValueError, "third level"):
                read_table(path)

    def test_a_gap_in_the_numbering_is_rejected(self) -> None:
        # The numbering is the only record of the book's order, so a row
        # inserted without renumbering has to fail rather than be filed wrong.
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [TRINITY, ("3", "1", "") + FIRE[3:]])

            with self.assertRaisesRegex(ValueError, "does not follow"):
                read_table(path)

    def test_one_number_naming_two_headings_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [TRINITY, ("1", "2", "") + FIRE[3:]])

            with self.assertRaisesRegex(ValueError, "second name"):
                read_table(path)

    def test_a_subject_that_is_also_a_heading_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(
                Path(directory),
                [
                    TRINITY,
                    ("1", "1", "1", "讚美和敬拜", "三一神", "甲", "Praise and Worship", "The Trinity", "A"),
                ],
            )

            with self.assertRaisesRegex(ValueError, "heading of subjects"):
                read_table(path)

    def test_the_mapping_is_the_two_flattened_halves(self) -> None:
        with TemporaryDirectory() as directory:
            mapping = read_mapping(table(Path(directory), [TRINITY, FIRE]))

            self.assertEqual(
                mapping, {"讚美和敬拜——三一神": ENGLISH, "聖靈——火": "The Holy Spirit—The Fire"}
            )

    def test_one_english_subject_may_serve_two_chinese_ones(self) -> None:
        # The appendix prints a few subjects with wording of its own, which the
        # subject index still files under one English heading.
        with TemporaryDirectory() as directory:
            grace = ("Comfort", "By His Sufficient Grace")
            path = table(
                Path(directory),
                [
                    ("1", "1", "", "安慰與鼓勵", "因著祂足夠的恩典", "", *grace, ""),
                    ("1", "2", "", "安慰與鼓勵", "因著祂足彀的恩典", "", *grace, ""),
                ],
            )

            self.assertEqual(len(read_mapping(path)), 2)


class LocalizeTest(TestCase):
    """What the step puts on one hymn."""

    def test_the_english_half_is_added_and_the_chinese_kept(self) -> None:
        hymn = localized(Hymn.from_markdown(HYMN), ENGLISH)

        self.assertEqual(
            hymn.category.to_dict(), {"en": ENGLISH, "zh": "讚美和敬拜——三一神"}
        )

    def test_translating_twice_is_translating_once(self) -> None:
        once = localized(Hymn.from_markdown(HYMN), ENGLISH)

        twice = localized(Hymn.from_markdown(once.to_markdown()), ENGLISH)

        self.assertEqual(twice.to_markdown(), once.to_markdown())

    def test_a_retranslation_replaces_the_english_half(self) -> None:
        once = localized(Hymn.from_markdown(HYMN), "Praise and Worship—The Trinity")

        again = localized(Hymn.from_markdown(once.to_markdown()), "Praise—The Trinity")

        self.assertEqual(again.category.translations["en"], "Praise—The Trinity")


class ApplyTest(TestCase):
    """The pass over `data/`, which must be safe to run at any time."""

    def test_the_english_category_reaches_the_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(table(path, [TRINITY]))

            changed = apply(files, mapping)

            self.assertEqual(changed, files)
            self.assertIn(f"category: {ENGLISH}讚美和敬拜——三一神", files[0].read_text())

    def test_a_second_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(table(path, [TRINITY]))
            apply(files, mapping)

            self.assertEqual(apply(files, mapping), [])
            self.assertEqual(rewrites(files, mapping), [])

    def test_a_category_the_table_does_not_carry_is_named(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(table(path, [("1", "1", "") + FIRE[3:]]))

            with self.assertRaisesRegex(ValueError, "not in the table"):
                apply(files, mapping)

    def test_a_row_no_hymn_uses_is_named(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(table(path, [TRINITY, FIRE]))

            with self.assertRaisesRegex(ValueError, "match no hymn"):
                apply(files, mapping)

    def test_nothing_is_written_when_a_later_hymn_fails(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN, HYMN.replace("讚美和敬拜——三一神", "聖靈——火")])
            mapping = read_mapping(table(path, [TRINITY]))

            with self.assertRaises(ValueError):
                apply(files, mapping)

            self.assertEqual(files[0].read_text(encoding="utf-8"), HYMN)
