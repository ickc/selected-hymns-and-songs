"""Tests for the preface page, which stacks the two editions' front matter."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from hymn_projection.preface import to_markdown


class PrefaceTest(TestCase):
    def _data(self, root: Path, en: str = "# PREFACE\n\nEnglish.\n", zh: str = "# 編者的話\n\n中文。\n") -> Path:
        (root / "preface.en.markdown").write_text(en, encoding="utf-8")
        (root / "preface.zh.markdown").write_text(zh, encoding="utf-8")
        return root

    def test_english_comes_before_chinese_each_in_its_language(self) -> None:
        with TemporaryDirectory() as name:
            page = to_markdown(self._data(Path(name)))

        self.assertIn("format: html", page)
        self.assertLess(page.index("English."), page.index("中文。"))
        self.assertIn("::: {lang=en}", page)
        self.assertIn("::: {lang=zh-Hant}", page)
        self.assertLess(page.index("{lang=en}"), page.index("{lang=zh-Hant}"))

    def test_an_empty_preface_is_an_error(self) -> None:
        with TemporaryDirectory() as name:
            data = self._data(Path(name), en="   \n")
            with self.assertRaises(ValueError):
                to_markdown(data)
