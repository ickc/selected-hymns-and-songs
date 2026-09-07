"""Tests for the subject index, the projection of the whole collection."""

from unittest import TestCase

from hymn_projection.categories import Subject
from hymn_projection.model import Hymn
from hymn_projection.subjects import _ranges, _roman, to_markdown


def hymn(category: str, first: str) -> Hymn:
    return Hymn.from_markdown(f"---\ncategory: {category}\n---\n\n# 1\n\n{first}\n主啊\n")


TRINITY = Subject((1, 1), ("讚美和敬拜", "三一神"), ("Praise and Worship", "The Trinity"))
GREATNESS = Subject(
    (1, 2, 1),
    ("讚美和敬拜", "聖父", "祂的偉大"),
    ("Praise and Worship", "The Father", "His Greatness"),
)
GLORY = Subject(
    (1, 2, 2),
    ("讚美和敬拜", "聖父", "祂的榮耀"),
    ("Praise and Worship", "The Father", "His Glory"),
)
FIRE = Subject((2, 1), ("聖靈", "火"), ("The Holy Spirit", "The Fire"))


class NumeralTest(TestCase):
    """The English index heads its eighteen sections with Roman numerals."""

    def test_the_sections_of_this_hymnal_are_numbered_as_it_prints_them(self) -> None:
        self.assertEqual(
            [_roman(number) for number in (1, 4, 5, 9, 10, 14, 18)],
            ["I", "IV", "V", "IX", "X", "XIV", "XVIII"],
        )


class RangeTest(TestCase):
    """What each section covers, as the book's table of contents states it."""

    def test_a_run_of_numbers_is_stated_as_its_ends(self) -> None:
        self.assertEqual(_ranges([1, 2, 3, 4, 5, 6, 7]), "1\u20137")

    def test_a_section_the_supplement_added_to_states_both_runs(self) -> None:
        # Every section but four is in this case: the 84 supplement hymns were
        # filed into the same eighteen, so the contents page prints two runs.
        self.assertEqual(
            _ranges([171, 172, 173, 776]), "171\u2013173, 776"
        )

    def test_a_section_of_one_hymn_states_that_hymn(self) -> None:
        self.assertEqual(_ranges([816]), "816")

    def test_the_numbers_need_not_arrive_in_order(self) -> None:
        self.assertEqual(_ranges([3, 1, 2]), "1\u20133")


class IndexTest(TestCase):
    """What the page says, which is the book's outline and nothing else."""

    def setUp(self) -> None:
        self.subjects = [TRINITY, GREATNESS, GLORY, FIRE]
        self.entries = [
            (1, hymn("讚美和敬拜——三一神", "God, our Father")),
            (8, hymn("讚美和敬拜——聖父（祂的偉大）", "O Lord my God")),
            (9, hymn("讚美和敬拜——聖父（祂的榮耀）", "The heavens declare")),
            (178, hymn("聖靈——火", "O Thou who camest from above")),
        ]

    def test_each_level_is_headed_once_and_numbered_as_printed(self) -> None:
        page = to_markdown(self.subjects, self.entries)

        self.assertEqual(page.count("## I. [Praise and Worship]{lang=en}"), 1)
        self.assertIn("### 2. [The Father]{lang=en} [聖父]{lang=zh-Hant} {#subject-1-2}", page)
        self.assertIn("#### (1) [His Greatness]{lang=en}", page)
        self.assertIn("#### (2) [His Glory]{lang=en}", page)

    def test_a_two_level_subject_is_headed_at_the_second_level(self) -> None:
        page = to_markdown(self.subjects, self.entries)

        self.assertIn("### 1. [The Trinity]{lang=en} [三一神]{lang=zh-Hant} {#subject-1-1}", page)
        self.assertNotIn("#### 1. [The Trinity]", page)

    def test_a_hymn_is_its_number_and_its_opening_line_in_both_languages(self) -> None:
        page = to_markdown(self.subjects, self.entries)

        self.assertIn(
            "[[8]{.subject-number} [O Lord my God]{lang=en} [主啊]{lang=zh-Hant}](hymn/8.html)",
            page,
        )

    def test_a_hymn_with_no_english_shows_the_line_it_has(self) -> None:
        # 39 hymns are in the Chinese hymnal only, and the entry is whatever
        # the hymn actually carries rather than a gap where English would be.
        chinese_only = Hymn.from_markdown("---\ncategory: 聖靈——火\n---\n\n# 1\n\n我心單愛主\n")
        page = to_markdown(self.subjects, [(178, chinese_only)])

        self.assertIn("[[178]{.subject-number} [我心單愛主]{lang=zh-Hant}](hymn/178.html)", page)

    def test_the_top_headings_are_offered_as_a_strip_to_jump_by(self) -> None:
        page = to_markdown(self.subjects, self.entries)

        self.assertIn("(#subject-1)", page)
        self.assertIn("(#subject-2)", page)
        # One entry per section, not one per subject under it.
        self.assertEqual(page.count("(#subject-1)"), 1)

    def test_the_strip_states_what_each_section_covers(self) -> None:
        # The book's own contents page does, and these come from the hymns
        # filed below rather than from a second table that could disagree.
        page = to_markdown(self.subjects, self.entries)

        self.assertIn("[1, 8\u20139]{.subject-range}", page)
        self.assertIn("[178]{.subject-range}", page)

    def test_a_section_no_hymn_is_filed_under_states_no_numbers(self) -> None:
        page = to_markdown(self.subjects, self.entries[:1])

        self.assertIn("(#subject-2)", page)
        self.assertEqual(page.count("{.subject-range}"), 1)

    def test_every_hymn_reaches_the_page_exactly_once(self) -> None:
        page = to_markdown(self.subjects, self.entries)

        for number in (1, 8, 9, 178):
            self.assertEqual(page.count(f"](hymn/{number}.html)"), 1)

    def test_a_hymn_the_index_does_not_list_is_named(self) -> None:
        entries = self.entries + [(999, hymn("福音——無此主題", "Nowhere"))]

        with self.assertRaisesRegex(ValueError, "hymn 999"):
            to_markdown(self.subjects, entries)

    def test_a_subject_no_hymn_is_filed_under_still_heads_its_place(self) -> None:
        # The table and `data/` agreeing is `check-categories`' business; the
        # page's is to keep the outline whole rather than renumber around a gap.
        page = to_markdown(self.subjects, self.entries[:1])

        self.assertIn("#### (1) [His Greatness]{lang=en}", page)
        self.assertEqual(page.count("hymn/8.html"), 0)
