"""Project a hymn as the page that shows the text against the scan.

The second one-way projection, beside ``slides``.  Both read the same
``data/N.md`` through the same model, so the words on the page and the words on
the slide cannot drift apart; what differs is the division, and it differs
because the two are read differently.

A slide is divided for a screen and for singing: stanzas over four lines are
halved, and the chorus is repeated after every stanza it is sung with.  A page
is read against the scan beside it, so it keeps the hymn's own shape — every
stanza and every chorus once, in the order the source writes them, which is the
order the hymnal prints them.  Repeating a chorus four times here would put
four copies of it against the one copy on the page.

Like ``slides``, this says what is there and not how it looks: the panes carry
a name, the lyrics keep the ``lyrics`` Div and one language span
per translation, and ``hymn-page.scss`` and ``hymn-page.html`` make a layout of
it.  The controls that page carries — which language, text or scan or both —
are the same on all 848 pages and are therefore built there rather than written
into 848 files.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import LANGUAGE_ORDER, Hymn, Stanza
from .scans import SCAN_LANGUAGES, Edition
from .slides import (
    BCP47,
    INLINE_NOTE,
    _extract_notes,
    _localized_inline,
    _yaml_scalar,
    chorus_shape,
    chorus_sources,
    document_language,
    span,
    title,
)


# A pane carries its name and nothing else: `hymn-page.html` builds the switcher
# and holds what each is called, because that is the same on all 848 pages. The
# scan panes are named for their edition, which is how the language switch knows
# to hide a scan with the text beside it.
PANES = {"en": "scan-en", "zh": "scan-zh"}
# The alt text of a scanned page, which is all a reader with no images gets.
EDITION_NAMES = {"en": "English 英文版", "zh": "Chinese 中文版"}


@dataclass(frozen=True)
class Collection:
    """What one page needs to know about the collection it belongs to."""

    #: The scanned editions, which say what pages a hymn is printed on.
    editions: dict[str, Edition]
    #: Where ``data/N.md`` is browsable. **Not** where this page's own Markdown
    #: is: that file is generated, ignored by git, and has never existed in the
    #: repository. Someone who has spotted a typo here has to be sent to the
    #: file the typo can be fixed in.
    source_url: str
    #: The highest hymn number, so the last page knows not to link past itself.
    highest: int


def _fence(width: int, classes: str, body: str) -> str:
    """Wrap a body in a fenced Div, the fence widening with the nesting."""

    rule = ":" * width
    return f"{rule} {{{classes}}}\n{body}\n{rule}"


def _plain(text: str) -> str:
    """Strip singing instructions from text bound for a plain-text field."""

    return INLINE_NOTE.sub("", text).strip()


def _lyrics(stanza: Stanza) -> str:
    """Render one stanza's lines, one paragraph each, notes lifted out.

    The same shape the slides carry, so one stylesheet aligns the two languages
    into columns for either.
    """

    lines, notes = _extract_notes(stanza.lines)
    paragraphs = [
        "\\\n".join(
            span(text, language) for language, text in line.translations.items()
        )
        for line in lines
    ]
    block = _fence(3, ".lyrics", "\n\n".join(paragraphs))
    if not notes:
        return block
    ordered = sorted(notes, key=lambda note: LANGUAGE_ORDER[note[0]])
    body = "\\\n".join(span(text, language) for language, text in ordered)
    return block + "\n\n" + _fence(3, ".singing-note", body)


def _stanza_label(stanza: Stanza, choruses: list[str]) -> str:
    """Name a stanza the way the hymnal does, and a chorus the way it is sung."""

    if isinstance(stanza.name, int):
        return str(stanza.name)
    label = f"{span('Chorus', 'en')} {span('副歌', 'zh')}"
    # One chorus needs no name; several do, and the source's own name is the
    # one the chorus report and `data/N.md` use.
    if len(choruses) > 1:
        label += f" `{stanza.name}`"
    return label


def _ranges(numbers: list[int]) -> str:
    """Write consecutive stanza numbers as ranges: 1, 2, 3, 5 as "1-3, 5"."""

    spans: list[tuple[int, int]] = []
    for number in numbers:
        if spans and number == spans[-1][1] + 1:
            spans[-1] = (spans[-1][0], number)
        else:
            spans.append((number, number))
    return ", ".join(
        str(first) if first == last else f"{first}\u2013{last}"
        for first, last in spans
    )


def _resolution(hymn: Hymn, name: str) -> str:
    """Say which stanzas sing this chorus, when that had to be worked out.

    Only for the hymns whose chorus changes partway through. Everywhere else
    the answer is every stanza, or the stanza above, and saying so on 831 pages
    would bury the 17 where it is worth reading. Hymn 705 states its own rule
    in prose; this is that sentence, derived, for the rest of them.
    """

    if chorus_shape(hymn) != "mixed":
        return ""
    sources = chorus_sources(hymn.stanzas)
    stanzas = {
        language: [
            number
            for number, taken in sorted(sources.items())
            if taken.get(language) == name
        ]
        for language in SCAN_LANGUAGES
    }
    sung = {language: numbers for language, numbers in stanzas.items() if numbers}
    if not sung:
        return ""
    plural = "" if all(len(numbers) == 1 for numbers in sung.values()) else "s"
    if len(sung) == len(SCAN_LANGUAGES) and len(set(map(tuple, sung.values()))) == 1:
        # Both languages take this chorus after the same stanzas, so naming
        # them once says it: the hymn is mixed elsewhere, not here.
        text = f"Sung after stanza{plural} {_ranges(next(iter(sung.values())))}"
    else:
        editions = {"en": "in English", "zh": "in Chinese"}
        text = f"Sung after stanza{plural} " + ", ".join(
            f"{_ranges(numbers)} {editions[language]}"
            for language, numbers in sung.items()
        )
    return "\n\n" + _fence(3, ".hymn-resolution", span(text, "en"))


def _heading(hymn: Hymn, number: int) -> str:
    """The hymn's own heading: what the hymnal prints above the first stanza."""

    parts = [_fence(3, ".hymn-number", str(number))]
    parts.append(
        _fence(
            3,
            ".hymn-title",
            "\\\n".join(
                span(text, language) for language, text in title(hymn).items()
            ),
        )
    )
    # The meter is dropped from a slide, which nobody reads it off. It is
    # printed in the hymnal, so a page compared against the hymnal keeps it.
    meta = [_localized_inline(hymn.category.translations)]
    if hymn.meter is not None:
        meter = (
            hymn.meter
            if isinstance(hymn.meter, str)
            else _localized_inline(hymn.meter.translations)
        )
        meta.append(meter)
    if hymn.tune is not None:
        # Beside the meter, which is where a hymnal reader looks for it: the
        # two together are what say whether one text can be sung to another's
        # music. The name is English -- no Chinese index names a tune.
        names = hymn.tune if isinstance(hymn.tune, list) else [hymn.tune]
        meta.append(span(", ".join(names), "en"))
    for field in ("author", "ref"):
        value = getattr(hymn, field)
        if value is not None:
            meta.append(_localized_inline(value.translations))
    parts.append(_fence(3, ".hymn-meta", " · ".join(meta)))
    if hymn.note is not None:
        parts.append(_fence(3, ".hymn-note", _localized_inline(hymn.note.translations)))
    return _fence(5, ".hymn-heading", "\n\n".join(parts))


def _text_pane(hymn: Hymn, number: int) -> str:
    """The middle pane: the hymn as the source writes it."""

    choruses = [
        str(stanza.name) for stanza in hymn.stanzas if not isinstance(stanza.name, int)
    ]
    blocks = [_heading(hymn, number)]
    for stanza in hymn.stanzas:
        chorus = not isinstance(stanza.name, int)
        identifier = f"c{stanza.name}" if chorus else f"s{stanza.name}"
        heading = f"## {_stanza_label(stanza, choruses)} {{#{identifier}}}"
        resolution = _resolution(hymn, str(stanza.name)) if chorus else ""
        blocks.append(
            _fence(
                5,
                ".hymn-stanza" + (" .hymn-chorus" if chorus else ""),
                f"{heading}{resolution}\n\n{_lyrics(stanza)}",
            )
        )
    return _fence(
        7, '.hymn-pane .hymn-text data-pane="text"', "\n\n".join(blocks)
    )


def _scan_pane(number: int, language: str, edition: Edition) -> str:
    """One side pane: the pages of one edition this hymn is printed on.

    A page is shown whole. Consecutive hymns share pages, so the hymn above or
    below this one is often on it too — cropping to a guessed region would hide
    exactly the boundary the scan is here to settle.
    """

    pages = edition.pages(number)
    if pages:
        # Raw HTML rather than an image with a caption: Pandoc would make that
        # a figure and Quarto would number it, and "Figure 1" is not what a
        # scanned page 16 is called.
        body = "\n\n".join(
            f'<figure class="hymn-scan-page">\n'
            f'<img src="../scan/{language}/{page}.png" loading="lazy"\n'
            f'     alt="{EDITION_NAMES[language]}, page {page}, hymn {number}">\n'
            f'<figcaption>{EDITION_NAMES[language]} p. {page}</figcaption>\n'
            f"</figure>"
            for page in pages
        )
    else:
        # 39 hymns are in the Chinese hymnal and not the English one. Saying so
        # is the answer to the question an empty pane would raise.
        english = language == "en"
        body = _fence(
            3,
            ".hymn-absent",
            span(
                f"Hymn {number} is not in the "
                f"{'English' if english else 'Chinese'} edition.",
                "en",
            )
            + "\\\n"
            + span("英文版沒有這首詩歌。" if english else "中文版沒有這首詩歌。", "zh"),
        )
    return _fence(
        7, f'.hymn-pane .hymn-scan data-pane="{PANES[language]}"', body
    )


def _links(number: int, collection: Collection) -> str:
    """The per-hymn links, which `hymn-page.html` lifts into its toolbar.

    Only these differ between pages, so only these are written here; the
    toolbar around them is the same on all 848 and is built there.
    """

    links = [
        f"[{span('Slides', 'en')} {span('投影片', 'zh')}]"
        f"(../slide/{number}.html){{.hymn-link-slides}}",
        # data/N.md, not the Markdown this page was rendered from. That file is
        # generated by `md-to-site` and is not in the repository at all.
        f"[{span('Source', 'en')} {span('原始檔', 'zh')}]"
        f"({collection.source_url}/{number}.md){{.hymn-link-source}}",
    ]
    if number > 1:
        links.append(f"[{number - 1}]({number - 1}.html){{.hymn-link-previous}}")
    if number < collection.highest:
        links.append(f"[{number + 1}]({number + 1}.html){{.hymn-link-next}}")
    return _fence(5, ".hymn-links", " ".join(links))


def page_title(hymn: Hymn, number: int) -> str:
    """The browser tab's title: a number and the line the hymn is known by."""

    names = " ".join(_plain(text) for text in title(hymn).values())
    return f"{number} {names}"


def to_markdown(hymn: Hymn, number: int, collection: Collection) -> str:
    """Render one hymn as the page Markdown its text and scan are compared on."""

    metadata = [
        # As with the decks: a project declaring more than one format renders
        # every document to all of them unless the document picks one.
        "format: html",
        # The three panes are the page, and Quarto's article grid is a column
        # to read prose in. This one wants the window.
        "page-layout: custom",
        # One entry per slide is the search index this site wants: a
        # half-remembered line should open the deck at the stanza that sings
        # it. These pages hold the same words, and indexing them too would put
        # every hymn in the results twice for no new match.
        "search: false",
        # `pagetitle` rather than `title`: it names the tab without Quarto
        # rendering a title block above panes that want the whole window.
        f"pagetitle: {_yaml_scalar(page_title(hymn, number))}",
        f"lang: {document_language(hymn)}",
        f"number: {number}",
    ]
    body = [
        _links(number, collection),
        _fence(
            9,
            ".hymn-compare",
            "\n\n".join(
                [
                    _scan_pane(number, "en", collection.editions["en"]),
                    _text_pane(hymn, number),
                    _scan_pane(number, "zh", collection.editions["zh"]),
                ]
            ),
        ),
    ]
    return "---\n" + "\n".join(metadata) + "\n---\n\n" + "\n\n".join(body) + "\n"


__all__ = ["BCP47", "Collection", "page_title", "to_markdown"]
