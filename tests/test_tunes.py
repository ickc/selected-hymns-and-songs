"""Tests for the tune table and the preprocessing step that applies it."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.model import Hymn
from hymn_projection.tunes import (
    HEADER,
    apply,
    played,
    read_tunes,
    rewrites,
    write_tunes,
)


HYMN = """---
category: 讚美和敬拜——聖子（祂的拯救）
meter: 8.6.8.6.
---

# 1

O for a thousand tongues to sing
哦，願我有千萬舌頭，
"""

AZMON = "Azmon"
LYNGHAM = "Lyngham"


def table(directory: Path, rows: list[tuple[int, str]]) -> Path:
    path = directory / "tunes.tsv"
    body = "".join(f"{number}\t{tune}\n" for number, tune in rows)
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
            path = Path(directory) / "tunes.tsv"
            tunes = {60: [AZMON], 146: [AZMON, LYNGHAM]}

            write_tunes(tunes, path)

            self.assertEqual(read_tunes(path), tunes)

    def test_a_hymn_set_to_two_tunes_keeps_the_printed_order(self) -> None:
        # The hymnal numbers them, and the page over the staves says `First
        # tune` and `Second tune`: which is first is part of the fact.
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(146, LYNGHAM), (146, AZMON)])

            self.assertEqual(read_tunes(path), {146: [LYNGHAM, AZMON]})

    def test_a_missing_header_is_named_as_the_problem(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tunes.tsv"
            path.write_text(f"146\t{AZMON}\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "header"):
                read_tunes(path)

    def test_a_row_naming_no_tune_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(146, "")])

            with self.assertRaisesRegex(ValueError, "line 2"):
                read_tunes(path)

    def test_one_tune_given_to_a_hymn_twice_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(146, AZMON), (146, AZMON)])

            with self.assertRaisesRegex(ValueError, "twice"):
                read_tunes(path)

    def test_the_table_must_be_in_hymn_order(self) -> None:
        # It is read off the two indexes in order and written back in order,
        # so a row out of place is an edit that has lost its bearings.
        with TemporaryDirectory() as directory:
            path = table(Path(directory), [(146, AZMON), (60, AZMON)])

            with self.assertRaisesRegex(ValueError, "hymn order"):
                read_tunes(path)


class TuneTest(TestCase):
    """What the step puts on one hymn."""

    def test_the_one_tune_of_a_hymn_is_stored_as_its_name(self) -> None:
        hymn = played(Hymn.from_markdown(HYMN), [AZMON])

        self.assertEqual(hymn.tune, AZMON)

    def test_two_tunes_are_stored_as_the_ordered_pair(self) -> None:
        hymn = played(Hymn.from_markdown(HYMN), [AZMON, LYNGHAM])

        self.assertEqual(hymn.tune, [AZMON, LYNGHAM])

    def test_the_tune_is_not_localized(self) -> None:
        # Only the English edition names a tune; claiming a Chinese half would
        # be inventing one.
        hymn = played(Hymn.from_markdown(HYMN), [AZMON])

        self.assertEqual(hymn.to_dict()["tune"], AZMON)

    def test_setting_twice_is_setting_once(self) -> None:
        once = played(Hymn.from_markdown(HYMN), [AZMON, LYNGHAM])

        twice = played(Hymn.from_markdown(once.to_markdown()), [AZMON, LYNGHAM])

        self.assertEqual(twice.to_markdown(), once.to_markdown())


class ApplyTest(TestCase):
    """The pass over `data/`, which must be safe to run at any time."""

    def test_the_tune_reaches_the_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])

            changed = apply(files, read_tunes(table(path, [(1, AZMON)])))

            self.assertEqual(changed, files)
            self.assertIn(f"tune: {AZMON}", files[0].read_text())

    def test_a_second_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            tunes = read_tunes(table(path, [(1, AZMON), (1, LYNGHAM)]))
            apply(files, tunes)

            self.assertEqual(apply(files, tunes), [])
            self.assertEqual(rewrites(files, tunes), [])

    def test_a_hymn_the_table_drops_loses_its_tune(self) -> None:
        # The supplement is not in either index of tunes, and a row deleted
        # from the table has to take the tune with it.
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            apply(files, read_tunes(table(path, [(1, AZMON)])))

            apply(files, read_tunes(table(path, [])))

            self.assertNotIn("tune:", files[0].read_text(encoding="utf-8"))

    def test_a_row_no_hymn_answers_to_is_named(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)
            files = hymns(path, [HYMN])
            tunes = read_tunes(table(path, [(1, AZMON), (9, LYNGHAM)]))

            with self.assertRaisesRegex(ValueError, "not there"):
                apply(files, tunes)
