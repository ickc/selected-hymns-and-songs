"""Project the book's two prefaces as one page.

Unlike the other projections this is not about the hymns. ``data/preface.en.markdown``
and ``data/preface.zh.markdown`` are the prose the two editions open with, and
this stacks them into one document -- English first, then Chinese -- for the
site. The files are the source; this page is generated beside the decks and the
pages, ignored by git, and rebuilt in CI.

Each edition's prose keeps its own ``# `` heading and is wrapped in a div
carrying its language, the same ``lang`` the inline spans elsewhere use, so a
reader's font stack and a screen reader both switch at the boundary.
"""

from __future__ import annotations

from pathlib import Path

from .slides import BCP47, _localized_inline, _yaml_scalar

#: What the two editions call this page.
TITLE = {"en": "Preface", "zh": "編者的話"}
#: The source files, in the order the page stacks them: English, then Chinese.
SOURCES = (("en", "preface.en.markdown"), ("zh", "preface.zh.markdown"))


def to_markdown(data: Path) -> str:
    """Render the two prefaces as one page, English above Chinese."""

    sections = []
    for language, name in SOURCES:
        text = (data / name).read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"{data / name} is empty")
        sections.append(f"::: {{lang={BCP47[language]}}}\n\n{text}\n\n:::")

    lines = [
        "---",
        f"title: {_yaml_scalar(_localized_inline(TITLE))}",
        # A document, not a projection of one hymn: it names the format the two
        # editions' names sit inside, as `index.md` and the indexes do.
        "lang: en",
        "format: html",
        "---",
        "",
    ]
    return "\n".join(lines) + "\n" + "\n\n".join(sections) + "\n"
