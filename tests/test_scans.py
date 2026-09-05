"""Tests for reading the scanned editions' page intervals."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.scans import Edition, missing_images, read_edition, stage


def write(directory: Path, rows: list[str]) -> Path:
    path = directory / "en.csv"
    path.write_text(
        "segment,start_page,end_page\n" + "\n".join(rows) + "\n", encoding="utf-8"
    )
    return path


class EditionTest(TestCase):
    """The CSV contract, which is another project's file and not ours to bend."""

    def test_the_front_and_post_hymn_matter_are_not_hymns(self) -> None:
        with TemporaryDirectory() as directory:
            path = write(Path(directory), ["0,1,7", "1,8,8", "2,9,9"])

            edition = read_edition(path, "en")

            self.assertEqual(edition.hymns, {1: (8, 8)})

    def test_a_hymn_absent_from_an_edition_has_no_pages(self) -> None:
        with TemporaryDirectory() as directory:
            path = write(Path(directory), ["0,1,1", "1,2,2", "2,,", "3,3,3", "4,4,4"])

            edition = read_edition(path, "en")

            self.assertEqual(edition.pages(2), [])
            self.assertNotIn(2, edition.hymns)

    def test_a_hymn_spans_every_page_of_its_interval(self) -> None:
        edition = Edition("en", {11: (25, 26)})

        self.assertEqual(edition.pages(11), [25, 26])

    def test_consecutive_hymns_may_share_a_page(self) -> None:
        with TemporaryDirectory() as directory:
            # Hymn 42 begins below hymn 41 on page 15 and runs on to 16.
            path = write(Path(directory), ["0,1,1", "1,15,15", "2,15,16", "3,17,17"])

            edition = read_edition(path, "en")

            self.assertEqual(edition.pages(1), [15])
            self.assertEqual(edition.pages(2), [15, 16])

    def test_one_page_bound_of_two_is_an_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = write(Path(directory), ["0,1,1", "1,2,", "2,3,3"])

            with self.assertRaisesRegex(ValueError, "one page bound"):
                read_edition(path, "en")

    def test_a_missing_segment_is_an_error(self) -> None:
        with TemporaryDirectory() as directory:
            # Without this the rows after the gap would each describe the pages
            # of a different hymn than the one they name.
            path = write(Path(directory), ["0,1,1", "1,2,2", "3,3,3", "4,4,4"])

            with self.assertRaisesRegex(ValueError, "expected segment 2"):
                read_edition(path, "en")

    def test_a_backwards_interval_is_an_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = write(Path(directory), ["0,1,1", "1,9,8", "2,10,10"])

            with self.assertRaisesRegex(ValueError, "spans 9 to 8"):
                read_edition(path, "en")


class ImageTest(TestCase):
    """The images are copied in from another project and can fall behind it."""

    def test_a_page_without_its_image_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "en").mkdir()
            (root / "en" / "8.png").write_bytes(b"")

            absent = missing_images({"en": Edition("en", {1: (8, 9)})}, root)

            self.assertEqual(absent, [root / "en" / "9.png"])

    def test_staging_links_every_page_into_the_rendered_site(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for language in ("en", "zh"):
                (root / "scan" / language).mkdir(parents=True)
                (root / "scan" / language / "8.png").write_bytes(b"page")
            output = root / "_site"
            output.mkdir()

            self.assertEqual(stage(root / "scan", output), 2)

            self.assertEqual((output / "scan" / "en" / "8.png").read_bytes(), b"page")
            self.assertEqual((output / "scan" / "zh" / "8.png").read_bytes(), b"page")

    def test_staging_replaces_what_a_previous_build_left(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for language in ("en", "zh"):
                (root / "scan" / language).mkdir(parents=True)
                (root / "scan" / language / "8.png").write_bytes(b"new")
                (root / "_site" / "scan" / language).mkdir(parents=True)
                (root / "_site" / "scan" / language / "8.png").write_bytes(b"old")

            stage(root / "scan", root / "_site")

            self.assertEqual(
                (root / "_site" / "scan" / "en" / "8.png").read_bytes(), b"new"
            )
