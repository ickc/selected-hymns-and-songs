"""Tests for the credits table and the preprocessing step that applies it."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.authors import (
    COMPILER,
    DAGGER,
    HEADER,
    apply,
    credited,
    read_authors,
    rewrites,
    write_authors,
)
from hymn_projection.model import Hymn


HYMN = """---
category: 讚美和敬拜——聖子（祂的拯救）
meter: 8.6.8.6.
---

# 1

O for a thousand tongues to sing
哦，願我有千萬舌頭，
"""


def table(*rows: str) -> str:
    return "\t".join(HEADER) + "\n" + "".join(row + "\n" for row in rows)


class TableTest(TestCase):
    """Reading the table, which is one row per hymn and keeps its blanks."""

    def test_a_row_carries_both_credits(self) -> None:
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(table("1\tCharles Wesley\tCarl G. Glaser\t"))

            self.assertEqual(
                read_authors(path), {1: ("Charles Wesley", "Carl G. Glaser", "")}
            )

    def test_a_row_can_say_why_its_credit_reads_as_it_does(self) -> None:
        # Three hymns have one: the two printings name different people, so the
        # cell beside them is a reading and not a transcription.
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(table("1\tA and B\tA and B\tThe page prints A, the index B."))

            self.assertEqual(
                read_authors(path),
                {1: ("A and B", "A and B", "The page prints A, the index B.")},
            )

    def test_a_note_cannot_stand_where_there_is_no_credit(self) -> None:
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(table("1\t\t\tThe two indexes disagree."))

            with self.assertRaises(ValueError):
                read_authors(path)

    def test_a_blank_cell_is_kept_rather_than_dropped(self) -> None:
        # The index heads itself "(Blanks indicate untraceable sources)", so a
        # blank is the book's own statement and not a hole in the reading.
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(
                table("1\t\tJohn Zundel\t", "2\tIsaac Watts\t\t", "3\t\t\t")
            )

            self.assertEqual(
                read_authors(path),
                {
                    1: ("", "John Zundel", ""),
                    2: ("Isaac Watts", "", ""),
                    3: ("", "", ""),
                },
            )

    def test_a_row_that_is_not_four_fields_is_an_error(self) -> None:
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(table("1\tCharles Wesley\tCarl G. Glaser"))

            with self.assertRaises(ValueError):
                read_authors(path)

    def test_the_table_must_be_in_hymn_order(self) -> None:
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(table("2\tIsaac Watts\t\t", "1\tCharles Wesley\t\t"))

            with self.assertRaises(ValueError):
                read_authors(path)

    def test_one_hymn_cannot_be_credited_twice(self) -> None:
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            path.write_text(table("1\tCharles Wesley\t\t", "1\tIsaac Watts\t\t"))

            with self.assertRaises(ValueError):
                read_authors(path)

    def test_what_is_written_reads_back_the_same(self) -> None:
        with TemporaryDirectory() as name:
            path = Path(name) / "authors.tsv"
            credits = {
                1: ("Charles Wesley", "Carl G. Glaser", ""),
                2: ("", "John Zundel", "Both indexes name him."),
            }
            write_authors(credits, path)

            self.assertEqual(read_authors(path), credits)


class CreditTest(TestCase):
    """What the table does to a hymn."""

    def test_a_hymn_gets_both_names_in_english(self) -> None:
        # Not localized: the index is the English edition's, and the Chinese
        # edition credits nobody.
        hymn = credited(Hymn.from_markdown(HYMN), ("Charles Wesley", "Carl G. Glaser", ""))

        self.assertEqual(hymn.author.translations, {"en": "Charles Wesley"})
        self.assertEqual(hymn.composer.translations, {"en": "Carl G. Glaser"})
        self.assertIsNone(hymn.credit_note)

    def test_a_note_reaches_the_hymn_as_its_own_field(self) -> None:
        # Beside the credit rather than inside it: the front matter still says
        # who wrote the hymn, and says separately why it reads that way.
        hymn = credited(
            Hymn.from_markdown(HYMN),
            ("A and B", "A and B", "The page prints A, the index B."),
        )

        self.assertEqual(hymn.author.translations, {"en": "A and B"})
        self.assertEqual(
            hymn.credit_note.translations, {"en": "The page prints A, the index B."}
        )
        self.assertIn("credit-note:", hymn.to_markdown())

    def test_deleting_a_note_takes_it_out_of_the_hymn(self) -> None:
        was = credited(Hymn.from_markdown(HYMN), ("A and B", "A and B", "Why."))

        self.assertIsNone(credited(was, ("A and B", "A and B", "")).credit_note)

    def test_a_blank_clears_one_field_without_touching_the_other(self) -> None:
        hymn = credited(Hymn.from_markdown(HYMN), ("", "Carl G. Glaser", ""))

        self.assertIsNone(hymn.author)
        self.assertEqual(hymn.composer.translations, {"en": "Carl G. Glaser"})

    def test_the_dagger_becomes_the_word_its_legend_gives(self) -> None:
        # The mark belongs to no script, so `auto-lang` has nothing to tag it
        # as. The book supplies the wording: "(t indicates compiler)".
        hymn = credited(Hymn.from_markdown(HYMN), (DAGGER, "Ira D. Sankey", ""))

        self.assertEqual(hymn.author.translations, {"en": COMPILER})
        self.assertNotIn(DAGGER, hymn.to_markdown())

    def test_a_hymn_the_table_skips_loses_the_credits_it_had(self) -> None:
        # Every hymn above 764 is in this case: the English back matter's
        # supplement has no author index at all.
        was = credited(
            Hymn.from_markdown(HYMN), ("Charles Wesley", "Carl G. Glaser", "Why.")
        )

        self.assertIsNone(credited(was, None).author)
        self.assertIsNone(credited(was, None).composer)
        self.assertIsNone(credited(was, None).credit_note)


class ApplyTest(TestCase):
    """The preprocessing step over `data/`."""

    def _data(self, root: Path, numbers: tuple[int, ...] = (1, 2)) -> list[Path]:
        paths = []
        for number in numbers:
            path = root / f"{number}.md"
            path.write_text(HYMN)
            paths.append(path)
        return paths

    def test_applying_twice_changes_nothing_the_second_time(self) -> None:
        with TemporaryDirectory() as name:
            files = self._data(Path(name))
            credits = {
                1: ("Charles Wesley", "Carl G. Glaser", "Why."),
                2: ("", "John Zundel", ""),
            }

            self.assertEqual(len(apply(files, credits)), 2)
            self.assertEqual(apply(files, credits), [])

    def test_deleting_a_row_takes_the_credit_back_out(self) -> None:
        with TemporaryDirectory() as name:
            files = self._data(Path(name))
            apply(files, {1: ("Charles Wesley", "", ""), 2: ("Isaac Watts", "", "")})

            self.assertEqual(len(apply(files, {1: ("Charles Wesley", "", "")})), 1)
            self.assertNotIn("author:", files[1].read_text())

    def test_a_row_naming_a_hymn_that_is_not_there_is_an_error(self) -> None:
        # A row cannot go stale unnoticed.
        with TemporaryDirectory() as name:
            files = self._data(Path(name))

            with self.assertRaises(ValueError):
                rewrites(
                    files, {1: ("Charles Wesley", "", ""), 900: ("Someone", "", "")}
                )

    def test_check_reports_what_apply_would_write(self) -> None:
        with TemporaryDirectory() as name:
            files = self._data(Path(name))
            credits = {1: ("Charles Wesley", "Carl G. Glaser", "")}

            stale = [path for path, _ in rewrites(files, credits)]

            self.assertEqual(stale, [files[0]])
            self.assertNotIn("author:", files[0].read_text())
