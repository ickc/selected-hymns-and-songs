"""Tests for the title table and the preprocessing step that applies it."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.slides import title
from hymn_projection.titles import (
    HEADER,
    apply,
    named,
    read_titles,
    rewrites,
    write_titles,
)


HYMN = """---
category: 讚美和敬拜——聖父（祂的偉大）
---

# 1

O Lord my God, when I in awesome wonder,
當我思念，我主，你創造大工，
"""

NAME = "How great Thou art"


def table(directory: Path, rows: list[tuple[int, str]]) -> Path:
    path = directory / "titles.tsv"
    body = "".join(f"{number}\t{text}\n" for number, text in rows)
    path.write_text("\t".join(HEADER) + "\n" + body, encoding="utf-8")
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
            path = Path(directory) / "titles.tsv"
            titles = {8: NAME, 19: "Abba"}

            write_titles(titles, path)

            self.assertEqual(read_titles(path), titles)

    def test_a_missing_header_is_named_as_the_problem(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "titles.tsv"
            path.write_text(f"8\t{NAME}\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "header"):
                read_titles(path)

    def test_a_row_naming_no_hymn_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(8, "")])

            with self.assertRaisesRegex(ValueError, "line 2"):
                read_titles(path)

    def test_a_hymn_named_twice_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(8, NAME), (8, "Abba")])

            with self.assertRaisesRegex(ValueError, "twice"):
                read_titles(path)

    def test_the_table_must_be_in_hymn_order(self) -> None:
        # It is read off the book in order and written back in order, so a row
        # out of place is an edit that has lost its bearings.
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(19, "Abba"), (8, NAME)])

            with self.assertRaisesRegex(ValueError, "hymn order"):
                read_titles(path)


class NameTest(TestCase):
    """What the step puts on one hymn, and what it deliberately leaves alone."""

    def test_only_the_english_half_is_written(self) -> None:
        hymn = named(Hymn.from_markdown(HYMN), NAME)

        self.assertEqual(hymn.title.to_dict(), {"en": NAME})

    def test_the_chinese_first_line_still_names_the_hymn(self) -> None:
        # No Chinese index names a hymn, so the pair is the book's English
        # name beside the line the Chinese page opens with.
        hymn = named(Hymn.from_markdown(HYMN), NAME)

        self.assertEqual(
            title(hymn), {"en": NAME, "zh": "當我思念，我主，你創造大工"}
        )

    def test_a_hymn_the_book_does_not_name_keeps_both_first_lines(self) -> None:
        hymn = Hymn.from_markdown(HYMN)

        self.assertEqual(
            title(hymn),
            {
                "en": "O Lord my God, when I in awesome wonder",
                "zh": "當我思念，我主，你創造大工",
            },
        )

    def test_naming_twice_is_naming_once(self) -> None:
        once = named(Hymn.from_markdown(HYMN), NAME)

        twice = named(Hymn.from_markdown(once.to_markdown()), NAME)

        self.assertEqual(twice.to_markdown(), once.to_markdown())


class ApplyTest(TestCase):
    """The pass over `data/`, which must be safe to run at any time."""

    def test_the_name_reaches_the_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])

            changed = apply(files, read_titles(table(path, [(1, NAME)])))

            self.assertEqual(changed, files)
            self.assertIn(f"title: {NAME}", files[0].read_text())

    def test_a_second_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            titles = read_titles(table(path, [(1, NAME)]))
            apply(files, titles)

            self.assertEqual(apply(files, titles), [])
            self.assertEqual(rewrites(files, titles), [])

    def test_a_hymn_the_table_drops_loses_its_title(self) -> None:
        # The scripture portions have no name in the index, and a row deleted
        # from the table has to take the title with it.
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            apply(files, read_titles(table(path, [(1, NAME)])))

            apply(files, read_titles(table(path, [])))

            self.assertNotIn("title:", files[0].read_text(encoding="utf-8"))

    def test_a_row_no_hymn_answers_to_is_named(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            titles = read_titles(table(path, [(1, NAME), (9, "Glorify Thy name")]))

            with self.assertRaisesRegex(ValueError, "not there"):
                apply(files, titles)
