"""Tests for the lossless hymn conversion boundaries."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import yaml

from hymn_projection.converter import (
    markdown_to_site,
    markdown_to_yaml,
    yaml_to_markdown,
)
from hymn_projection.environment import BUILD_MODE_ENV
from hymn_projection.model import Hymn
from hymn_projection.categories import HEADER
from hymn_projection.scans import SCAN_LANGUAGES


HYMN_DATA = {
    "author": {"en": "An Author"},
    "category": {"zh": "分類——測試"},
    "meter": {"en": "8.6.8.6. with chorus", "zh": "8.6.8.6. 和"},
    "note": {"en": "Keep *meaningful* Markdown"},
    "stanza": {
        1: [
            {"en": "A “quoted” line—with punctuation.", "zh": "第一行。"},
            {"zh": "　　保留全形空格。"},
        ],
        "1-chorus": [{"en": "A line with *emphasis* and ^[a note]."}],
    },
    "title": {"en": "A title <!-- remains literal -->"},
}


def make_site(root: Path, hymns: int) -> tuple[Path, Path]:
    """Build the Quarto project and scans one projection run needs.

    `markdown_to_site` writes into a Quarto project and reads two things from
    beside it: where `data/` is browsable, and which pages each hymn is printed
    on. Both are real inputs, so a test supplies real ones rather than reaching
    past them.
    """

    site = root / "site"
    site.mkdir(parents=True, exist_ok=True)
    (site / "_quarto.yml").write_text(
        "source-repo: https://example.invalid/blob/main\n", encoding="utf-8"
    )
    scans = root / "scan"
    # Segment 0 is the front matter and the last is the post-hymn matter, so a
    # collection of N hymns is N + 2 rows and hymn n is on page n + 1.
    rows = ["segment,start_page,end_page", "0,1,1"]
    rows += [f"{number},{number + 1},{number + 1}" for number in range(1, hymns + 1)]
    rows.append(f"{hymns + 1},{hymns + 2},{hymns + 2}")
    for language in SCAN_LANGUAGES:
        (scans / language).mkdir(parents=True, exist_ok=True)
        (scans / f"{language}.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        for number in range(1, hymns + 1):
            (scans / language / f"{number + 1}.png").write_bytes(b"")
    return site, scans


def make_table(markdown: Path) -> Path:
    """Write the subject index beside the hymns, which the site projection reads.

    The fixture files every hymn under one subject; the table is what says
    where that subject comes in the book and what the English edition calls it.
    """

    path = markdown / "categories.tsv"
    path.write_text(
        "\t".join(HEADER) + "\n" + "\t".join(("1", "1", "", "分類", "測試", "", "Category", "Test", "")) + "\n",
        encoding="utf-8",
    )
    return path


class HymnConversionTest(TestCase):
    """Exercise the object and collection round trips."""

    def test_object_round_trip(self) -> None:
        hymn = Hymn.from_dict(HYMN_DATA)
        markdown = hymn.to_markdown()

        self.assertEqual(hymn.to_dict(), HYMN_DATA)
        self.assertEqual(Hymn.from_markdown(markdown), hymn)
        self.assertNotIn("{lang=", markdown)
        self.assertNotIn("auto-lang:", markdown)
        self.assertIn("category: 分類——測試", markdown)
        self.assertIn("meter: 8.6.8.6. with chorus和", markdown)
        self.assertIn("A “quoted” line—with punctuation.\n第一行。", markdown)
        self.assertIn("第一行。\n　　保留全形空格。\n", markdown)
        self.assertIn("note: Keep *meaningful* Markdown", markdown)
        self.assertIn("A line with *emphasis* and ^[a note].", markdown)

    def test_latin_scalar_meter_remains_a_scalar(self) -> None:
        hymn = Hymn.from_dict(dict(HYMN_DATA, meter="C.M."))

        recovered = Hymn.from_markdown(hymn.to_markdown())

        self.assertEqual(recovered.meter, "C.M.")

    def test_double_meter_notation_is_shared_between_languages(self) -> None:
        meter = {
            "en": "7.7.7.7.D. with repeat",
            "zh": "7.7.7.7.D. 重",
        }
        hymn = Hymn.from_dict(dict(HYMN_DATA, meter=meter))
        markdown = hymn.to_markdown()

        self.assertIn("meter: 7.7.7.7.D. with repeat重", markdown)
        self.assertEqual(Hymn.from_markdown(markdown).meter.to_dict(), meter)

    def test_directory_round_trip_is_byte_exact(self) -> None:
        source_yaml = yaml.safe_dump([HYMN_DATA], allow_unicode=True, sort_keys=False)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.yml"
            markdown = root / "data"
            recovered = root / "recovered.yml"
            source.write_text(source_yaml, encoding="utf-8")

            yaml_to_markdown(source, markdown)
            markdown_to_yaml(markdown, recovered)

            self.assertEqual(recovered.read_bytes(), source.read_bytes())

    def test_an_empty_source_directory_is_named_as_the_problem(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            empty = Path(temporary_directory) / "data"
            empty.mkdir()

            with self.assertRaisesRegex(ValueError, "no N.md files"):
                markdown_to_yaml(empty, Path(temporary_directory) / "out.yml")

    def test_a_hymn_that_leaves_the_source_leaves_the_projection(self) -> None:
        source_yaml = yaml.safe_dump([HYMN_DATA, HYMN_DATA], allow_unicode=True, sort_keys=False)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.yml"
            markdown = root / "data"
            site, scans = make_site(root, hymns=2)
            source.write_text(source_yaml, encoding="utf-8")
            yaml_to_markdown(source, markdown)
            make_table(markdown)
            markdown_to_site(markdown, site, scans, jobs=2)
            self.assertTrue((site / "slide" / "2.md").exists())
            self.assertTrue((site / "hymn" / "2.md").exists())

            (markdown / "2.md").unlink()
            markdown_to_site(markdown, site, scans, jobs=2)

            # Both projections, not just the one the decks are rendered from: a
            # page left behind would go on being published and link to a deck
            # that is no longer there.
            self.assertFalse((site / "slide" / "2.md").exists())
            self.assertFalse((site / "hymn" / "2.md").exists())
            self.assertTrue((site / "slide" / "1.md").exists())
            self.assertTrue((site / "hymn" / "1.md").exists())

    def test_the_projection_writes_the_subject_index(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "data"
            source.mkdir()
            (source / "1.md").write_text(
                Hymn.from_dict(HYMN_DATA).to_markdown(), encoding="utf-8"
            )
            make_table(source)
            site, scans = make_site(root, hymns=1)

            markdown_to_site(source, site, scans, jobs=1)

            index = (site / "subject.md").read_text(encoding="utf-8")
            self.assertIn("## I. [Category]{lang=en} [分類]{lang=zh-Hant}", index)
            self.assertIn("[[1]{.subject-number}", index)
            self.assertIn("](hymn/1.html)", index)

    def test_the_projection_writes_the_index_of_tunes(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "data"
            source.mkdir()
            (source / "1.md").write_text(
                Hymn.from_dict(dict(HYMN_DATA, tune="Beecher")).to_markdown(),
                encoding="utf-8",
            )
            make_table(source)
            site, scans = make_site(root, hymns=1)

            markdown_to_site(source, site, scans, jobs=1)

            index = (site / "tune.md").read_text(encoding="utf-8")
            self.assertIn("[[Beecher]{lang=en}]{.tune-name}", index)
            self.assertIn("[[1](hymn/1.html)]{.tune-hymns}", index)

    def test_developer_projection_writes_the_chorus_report(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "data"
            source.mkdir()
            (source / "1.md").write_text(
                Hymn.from_dict(HYMN_DATA).to_markdown(), encoding="utf-8"
            )
            make_table(source)

            site, scans = make_site(root, hymns=1)
            with patch.dict("os.environ", {BUILD_MODE_ENV: "develop"}):
                markdown_to_site(source, site, scans, jobs=1)

            report = (site / "chorus.md").read_text(encoding="utf-8")
            self.assertIn("search: false", report)

    def test_production_projection_removes_the_chorus_report(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "data"
            source.mkdir()
            site, scans = make_site(root, hymns=1)
            (source / "1.md").write_text(
                Hymn.from_dict(HYMN_DATA).to_markdown(), encoding="utf-8"
            )
            make_table(source)
            (site / "chorus.md").write_text("stale", encoding="utf-8")
            (site / "chorus.html").write_text("stale", encoding="utf-8")

            with patch.dict("os.environ", {BUILD_MODE_ENV: "production"}):
                markdown_to_site(source, site, scans, jobs=1)

            self.assertFalse((site / "chorus.md").exists())
            self.assertFalse((site / "chorus.html").exists())

    def test_parallel_projection_is_byte_identical(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "data"
            source.mkdir()
            for number in range(1, 4):
                (source / f"{number}.md").write_text(
                    Hymn.from_dict(HYMN_DATA).to_markdown(), encoding="utf-8"
                )
            make_table(source)

            serial, scans = make_site(root / "serial", hymns=3)
            parallel, _ = make_site(root / "parallel", hymns=3)
            markdown_to_site(source, serial, scans, jobs=1)
            markdown_to_site(source, parallel, scans, jobs=3)

            def written(site: Path) -> dict[Path, bytes]:
                return {
                    path.relative_to(site): path.read_bytes()
                    for path in site.rglob("*")
                    if path.is_file() and path.name != "_quarto.yml"
                }

            self.assertEqual(written(parallel), written(serial))

    def test_unknown_hymn_field_is_rejected(self) -> None:
        invalid = dict(HYMN_DATA, unexpected="value")

        with self.assertRaisesRegex(ValueError, "unknown hymn fields"):
            Hymn.from_dict(invalid)

    def test_explicit_null_is_rejected(self) -> None:
        invalid = dict(HYMN_DATA, meter=None)

        with self.assertRaisesRegex(ValueError, "meter must be"):
            Hymn.from_dict(invalid)

    def test_one_tune_and_an_ordered_pair_both_survive_the_round_trip(self) -> None:
        for tune in ("Azmon", ["Azmon", "Lyngham"]):
            with self.subTest(tune=tune):
                hymn = Hymn.from_dict(dict(HYMN_DATA, tune=tune))

                self.assertEqual(Hymn.from_markdown(hymn.to_markdown()).tune, tune)
                self.assertEqual(hymn.to_dict()["tune"], tune)

    def test_a_hymn_set_to_one_tune_twice_is_rejected(self) -> None:
        invalid = dict(HYMN_DATA, tune=["Azmon", "Azmon"])

        with self.assertRaisesRegex(ValueError, "one tune twice"):
            Hymn.from_dict(invalid)

    def test_an_empty_tune_is_rejected(self) -> None:
        invalid = dict(HYMN_DATA, tune=[])

        with self.assertRaisesRegex(ValueError, "tune must be"):
            Hymn.from_dict(invalid)


class IrregularMeterTest(TestCase):
    """A meter whose two languages share no notation to factor out."""

    SOURCE = """---
category: 甲——乙
meter: Irregular Meter特.和
---

# 1

A line
一二三
"""

    def test_an_irregular_meter_reads_as_localized_text(self) -> None:
        hymn = Hymn.from_markdown(self.SOURCE)

        self.assertEqual(
            hymn.meter.to_dict(), {"en": "Irregular Meter", "zh": "特.和"}
        )

    def test_an_irregular_meter_round_trips(self) -> None:
        hymn = Hymn.from_markdown(self.SOURCE)

        self.assertEqual(hymn.to_markdown(), self.SOURCE)

    def test_a_numeric_localized_meter_still_factors_its_notation(self) -> None:
        source = self.SOURCE.replace("Irregular Meter特.和", "8.6.8.6. with chorus和")

        hymn = Hymn.from_markdown(source)

        self.assertEqual(
            hymn.meter.to_dict(), {"en": "8.6.8.6. with chorus", "zh": "8.6.8.6. 和"}
        )
        self.assertEqual(hymn.to_markdown(), source)
