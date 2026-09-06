"""Tests for the category table and the preprocessing step that applies it."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.categories import (
    HEADER,
    apply,
    localized,
    read_mapping,
    rewrites,
    write_mapping,
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


def table(directory: Path, rows: list[str]) -> Path:
    path = directory / "categories.tsv"
    path.write_text("\t".join(HEADER) + "\n" + "".join(rows), encoding="utf-8")
    return path


def hymns(directory: Path, sources: list[str]) -> list[Path]:
    paths = []
    for number, source in enumerate(sources, start=1):
        path = directory / f"{number}.md"
        path.write_text(source, encoding="utf-8")
        paths.append(path)
    return paths


class TableTest(TestCase):
    """The hand-edited file, which has to say what it means or fail loudly."""

    def test_a_table_round_trips_through_the_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "categories.tsv"
            rows = [("讚美和敬拜——三一神", ENGLISH), ("聖靈——火", "The Holy Spirit—The Fire")]

            write_mapping(rows, path)

            self.assertEqual(read_mapping(path), dict(rows))

    def test_a_missing_header_is_named_as_the_problem(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "categories.tsv"
            path.write_text(f"讚美和敬拜——三一神\t{ENGLISH}\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "header"):
                read_mapping(path)

    def test_a_row_missing_its_translation_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), ["讚美和敬拜——三一神\t\n"])

            with self.assertRaisesRegex(ValueError, "line 2"):
                read_mapping(path)

    def test_a_repeated_chinese_category_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(
                Path(directory),
                [f"讚美和敬拜——三一神\t{ENGLISH}\n", "讚美和敬拜——三一神\tThe Trinity\n"],
            )

            with self.assertRaisesRegex(ValueError, "repeats"):
                read_mapping(path)

    def test_one_english_category_may_serve_several_chinese_ones(self) -> None:
        # The appendix prints a few subjects with wording of their own, which
        # the subject index still files under one English heading.
        with TemporaryDirectory() as directory:
            path = table(
                Path(directory),
                [
                    "安慰與鼓勵——因著祂足夠的恩典\tComfort and Encouragement—By His Sufficient Grace\n",
                    "安慰與鼓勵——因著祂足彀的恩典\tComfort and Encouragement—By His Sufficient Grace\n",
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
            mapping = read_mapping(table(path, [f"讚美和敬拜——三一神\t{ENGLISH}\n"]))

            changed = apply(files, mapping)

            self.assertEqual(changed, files)
            self.assertIn(f"category: {ENGLISH}讚美和敬拜——三一神", files[0].read_text())

    def test_a_second_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(table(path, [f"讚美和敬拜——三一神\t{ENGLISH}\n"]))
            apply(files, mapping)

            self.assertEqual(apply(files, mapping), [])
            self.assertEqual(rewrites(files, mapping), [])

    def test_a_category_the_table_does_not_carry_is_named(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(table(path, ["聖靈——火\tThe Holy Spirit—The Fire\n"]))

            with self.assertRaisesRegex(ValueError, "not in the table"):
                apply(files, mapping)

    def test_a_row_no_hymn_uses_is_named(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            mapping = read_mapping(
                table(
                    path,
                    [
                        f"讚美和敬拜——三一神\t{ENGLISH}\n",
                        "聖靈——火\tThe Holy Spirit—The Fire\n",
                    ],
                )
            )

            with self.assertRaisesRegex(ValueError, "match no hymn"):
                apply(files, mapping)

    def test_nothing_is_written_when_a_later_hymn_fails(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN, HYMN.replace("讚美和敬拜——三一神", "聖靈——火")])
            mapping = read_mapping(table(path, [f"讚美和敬拜——三一神\t{ENGLISH}\n"]))

            with self.assertRaises(ValueError):
                apply(files, mapping)

            self.assertEqual(files[0].read_text(encoding="utf-8"), HYMN)
