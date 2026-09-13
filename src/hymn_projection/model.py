"""The validated hymn model and its lossless Markdown representation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import panflute as pf


# Pandoc's ``smart`` extension rewrites literal curly quotes and dashes.  The
# checked-in projection deliberately disables bracketed spans: language spans
# exist only inside the converter, on either side of the Lua filters. Hard line
# breaks expose physical lyric lines without line-block markers in the source.
PANDOC_MARKDOWN = (
    "markdown-smart+yaml_metadata_block+hard_line_breaks-line_blocks-bracketed_spans"
)
LANGUAGES = frozenset(("en", "zh"))
LANGUAGE_ORDER = {"en": 0, "zh": 1}
STANZA_NAME = re.compile(r"[1-9][0-9]*-chorus")
AUTO_LANG = {"Han": "zh", "Latin": "en"}
FILTER_DIRECTORY = Path(__file__).with_name("filters")
AUTO_LANG_FILTER = FILTER_DIRECTORY / "auto-lang.lua"
STRIP_LANG_FILTER = FILTER_DIRECTORY / "strip-lang.lua"
PRESERVE_MARKDOWN_FILTER = FILTER_DIRECTORY / "preserve-markdown.lua"


def _mapping(value: object, description: str) -> Mapping[Any, Any]:
    """Return a mapping or raise a schema error mentioning its purpose."""

    if not isinstance(value, Mapping):
        raise ValueError(f"{description} must be a mapping")
    return value


@cache
def pandoc_api_version() -> tuple[int, ...]:
    """Return the JSON API version used by the installed Pandoc."""

    empty_document = pf.convert_text("", standalone=True)
    return empty_document.api_version


@dataclass
class LocalizedText:
    """An ordered mapping of supported language tags to text."""

    translations: dict[str, str]

    def __post_init__(self) -> None:
        if not self.translations:
            raise ValueError("localized text cannot be empty")
        for language, text in self.translations.items():
            if language not in LANGUAGES:
                raise ValueError(f"unsupported language {language!r}")
            if not isinstance(text, str):
                raise ValueError("localized text values must be strings")

    @classmethod
    def from_dict(cls, value: object, description: str) -> LocalizedText:
        """Validate and construct localized text from a YAML value."""

        mapping = _mapping(value, description)
        return cls(dict(mapping))

    def to_dict(self) -> dict[str, str]:
        """Return an independent YAML-compatible mapping."""

        return dict(self.translations)


def _language(element: pf.Element) -> str | None:
    """Return an element's language when it is a language span."""

    if isinstance(element, pf.Span):
        return element.attributes.get("lang")
    return None


def _text_piece(element: pf.Element) -> str:
    """Stringify one inline without dropping significant boundary spaces."""

    if isinstance(element, pf.Space):
        return " "
    if isinstance(element, (pf.LineBreak, pf.SoftBreak)):
        return "\n"
    if isinstance(element, pf.Str):
        return element.text
    return pf.stringify(element)


def _exact_text(elements: Sequence[pf.Element]) -> str:
    """Stringify adjacent metadata inlines, including trailing spaces."""

    return "".join(_text_piece(element) for element in elements)


def _localized_metadata(value: LocalizedText) -> pf.MetaInlines:
    """Represent localized metadata as internal language spans."""

    return pf.MetaInlines(
        *(
            pf.Span(pf.RawInline(text, format="markdown"), attributes={"lang": language})
            for language, text in value.translations.items()
        )
    )


def _localized_from_metadata(value: pf.MetaValue, description: str) -> LocalizedText:
    """Recover localized metadata after ``auto-lang.lua`` has tagged it."""

    if not isinstance(value, pf.MetaInlines):
        raise ValueError(f"{description} must contain language-detectable text")
    translations: dict[str, str] = {}
    for element in value.content:
        language = _language(element)
        if not language:
            raise ValueError(f"all {description} text must resolve to language spans")
        if language in translations:
            raise ValueError(f"duplicate {language!r} text in {description}")
        translations[language] = pf.stringify(element)
    return LocalizedText(translations)


def _named_metadata(value: LocalizedText, description: str) -> pf.MetaMap:
    """Name the halves of a localized value instead of running them together.

    Most localized fields are flattened into one scalar and cut apart again by
    writing system, which works because their Chinese half is Han and their
    English half is not. Two fields are mostly figures, and a figure belongs to
    no script.

    A meter: ``8.8.8.8.D. (A)`` beside ``8.8.8.8.D.`` offers no boundary to cut
    at, and ``Irregular Meter`` beside ``10.10.10.8.5. 和`` offers one in the
    wrong place.

    A scripture reference: ``Psalm 133`` beside ``詩133`` happens to cut in the
    right place, but ``1 John 1:5-7`` beside ``約壹1:5-7`` begins with a figure,
    so the cut lands after ``1`` and the English half loses its book number.
    Three of the forty-one references are numbered books, and the field would
    be one imported citation away from breaking again.

    So both name their languages, and nothing about either is inferred from its
    characters.
    """

    if len(value.translations) < 2:
        raise ValueError(
            f"a localized {description} needs two languages to remain distinguishable"
        )
    return pf.MetaMap(
        **{
            language: pf.MetaInlines(pf.RawInline(text, format="markdown"))
            for language, text in value.translations.items()
        }
    )


def _notes_from_metadata(value: pf.MetaValue) -> list[LocalizedText]:
    """Recover the hymn's notes, in the order the page prints them."""

    items = value.content if isinstance(value, pf.MetaList) else [value]
    return [_localized_from_metadata(item, "note") for item in items]


def _tune_metadata(value: str | list[str]) -> pf.MetaValue:
    """Represent one tune name, or an ordered list of them, as metadata."""

    if isinstance(value, str):
        return pf.MetaInlines(pf.RawInline(value, format="markdown"))
    return pf.MetaList(*(_tune_metadata(name) for name in value))


def _tune_from_metadata(value: pf.MetaValue) -> str | list[str]:
    """Recover the tune names, keeping the order the hymnal numbers them in."""

    if isinstance(value, pf.MetaList):
        return [_tune_from_metadata(item) for item in value.content]
    return pf.stringify(value).strip()


def _named_from_metadata(value: pf.MetaValue) -> LocalizedText | None:
    """Recover a named pair, or nothing when the value is a plain scalar."""

    if not isinstance(value, pf.MetaMap):
        return None
    return LocalizedText(
        {
            language: _exact_text(text.content).strip()
            if isinstance(text, pf.MetaInlines)
            else pf.stringify(text)
            for language, text in value.content.items()
        }
    )


@dataclass
class LyricLine:
    """One lyric line containing one or more translations."""

    translations: dict[str, str]

    def __post_init__(self) -> None:
        if not self.translations:
            raise ValueError("a lyric line cannot be empty")
        for language, text in self.translations.items():
            if language not in LANGUAGES:
                raise ValueError(f"unsupported lyric language {language!r}")
            if not isinstance(text, str):
                raise ValueError("lyric text must be a string")
        order = [LANGUAGE_ORDER[language] for language in self.translations]
        if order != sorted(order):
            raise ValueError("lyric languages must be ordered en, then zh")

    @classmethod
    def from_dict(cls, value: object) -> LyricLine:
        """Validate and construct one lyric line from a YAML value."""

        return cls(dict(_mapping(value, "lyric line")))

    def to_dict(self) -> dict[str, str]:
        """Return an independent YAML-compatible mapping."""

        return dict(self.translations)

    def to_inlines(self) -> list[pf.Inline]:
        """Construct the internally tagged inline runs for this YAML line."""

        return [
            pf.Span(
                pf.RawInline(text, format="markdown"),
                attributes={"lang": language},
            )
            for language, text in self.translations.items()
        ]

    @staticmethod
    def from_languages(
        line_languages: Sequence[set[str]], source_lines: Sequence[str]
    ) -> list[LyricLine]:
        """Recover ordered YAML lines from one automatically tagged stanza."""

        if len(line_languages) != len(source_lines):
            raise ValueError("Markdown source does not match parsed lyric lines")
        lines: list[LyricLine] = []
        translations: dict[str, str] = {}
        previous_order = -1
        for languages, source in zip(line_languages, source_lines, strict=True):
            # Inline markup can interrupt the outer automatically inferred
            # span.  Notes are a separate flow in Pandoc, for example, so a
            # line containing ``text^[note]`` has two zh spans rather than one.
            if len(languages) != 1:
                raise ValueError(
                    "each lyric line must resolve to exactly one language"
                )
            language = languages.pop()
            language_order = LANGUAGE_ORDER.get(language, -1)
            if language_order < 0:
                raise ValueError(f"unsupported lyric language {language!r}")

            # Each YAML mapping is in en/zh order.  A repeated language, or a
            # transition from zh back to en, therefore begins the next mapping.
            if translations and language_order <= previous_order:
                lines.append(LyricLine(translations))
                translations = {}
            translations[language] = source
            previous_order = language_order

        if translations:
            lines.append(LyricLine(translations))
        return lines


@dataclass
class Repeat:
    """Which of a stanza's lines the hymnal sings again after it.

    The book states a repeat in three places and relates none of them: it
    writes the lines out a second time, it prints a direction under the last
    stanza, or it marks the meter ``重`` / ``with repeat``.  Where the lines
    are written out, `data/` already holds them and this is absent.  This is
    for the other two, and it says the one thing they leave to the singer --
    *which* lines -- so that a projection can sing what the book only names.

    ``lines`` are the stanza's own lines, numbered from one, in the order they
    are sung again.  They are not always a tail: `en/71` sets hymn 57's
    ``8.6.8.6. with repeat`` as the fourth line twice and then the third and
    fourth again, which is the same shape hymn 678 writes out as a chorus.

    ``stanzas`` is every stanza unless it names some.  242 is the one that
    names any: both its pages print the direction under the fourth stanza, and
    both mean that stanza alone.

    Not localized, because the structure is the tune's and both editions sing
    it.  Every stanza of every hymn that carries a repeat has the same number
    of lines in both languages, so the numbers mean the same thing on either
    side.  242 looks like a counter-example and is not: `en/266` prints
    *Repeat the last four lines* and `zh/258` prints ``第四節末兩行重唱一遍``,
    and the Chinese page sets its stanzas in two columns, so two of its rows
    are four of these lines.
    """

    lines: list[int]
    #: The stanzas this repeat is sung in, or ``None`` for every one of them.
    stanzas: list[int] | None = None

    def __post_init__(self) -> None:
        for name, value in (("lines", self.lines), ("stanzas", self.stanzas)):
            if value is None:
                continue
            if not isinstance(value, list) or not value:
                raise ValueError(f"repeat {name} must be a non-empty list")
            if not all(
                isinstance(number, int)
                and not isinstance(number, bool)
                and number > 0
                for number in value
            ):
                raise ValueError(f"repeat {name} must be positive line numbers")
        if self.stanzas is not None and len(self.stanzas) != len(set(self.stanzas)):
            raise ValueError("repeat stanzas must be distinct")

    @classmethod
    def from_dict(cls, value: object) -> Repeat:
        """Validate and construct a repeat from a YAML value."""

        mapping = _mapping(value, "repeat")
        unknown = set(mapping) - {"lines", "stanzas"}
        if unknown:
            raise ValueError(f"unknown repeat fields: {sorted(unknown)!r}")
        if "lines" not in mapping:
            raise ValueError("a repeat must say which lines are sung again")

        def numbers(name: str) -> list[int] | None:
            if name not in mapping:
                return None
            value = mapping[name]
            if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
                raise ValueError(f"repeat {name} must be a list")
            # Pandoc metadata has no numbers, only inlines, so a value read
            # back out of `data/N.md` arrives as a string either way.
            return [int(number) for number in value]

        return cls(lines=numbers("lines") or [], stanzas=numbers("stanzas"))

    def to_dict(self) -> dict[str, list[int]]:
        """Return an independent YAML-compatible mapping."""

        result: dict[str, list[int]] = {"lines": list(self.lines)}
        if self.stanzas is not None:
            result["stanzas"] = list(self.stanzas)
        return result

    def to_metadata(self) -> pf.MetaMap:
        """Represent this repeat as Pandoc metadata."""

        def listing(numbers: list[int]) -> pf.MetaList:
            return pf.MetaList(
                *(pf.MetaInlines(pf.Str(str(number))) for number in numbers)
            )

        content: dict[str, pf.MetaValue] = {"lines": listing(self.lines)}
        if self.stanzas is not None:
            content["stanzas"] = listing(self.stanzas)
        return pf.MetaMap(**content)

    def sung_in(self, name: int | str) -> bool:
        """Say whether this repeat is sung in the named stanza.

        A chorus is never one: the repeat belongs to the verse, and a chorus
        that repeats its own lines is written out where the book writes it.
        """

        if not isinstance(name, int):
            return False
        return self.stanzas is None or name in self.stanzas


@dataclass
class Stanza:
    """A numbered verse or named chorus and its lyric lines."""

    name: int | str
    lines: list[LyricLine]

    def __post_init__(self) -> None:
        valid_number = (
            isinstance(self.name, int)
            and not isinstance(self.name, bool)
            and self.name > 0
        )
        valid_chorus = isinstance(self.name, str) and STANZA_NAME.fullmatch(self.name)
        if not valid_number and not valid_chorus:
            raise ValueError(f"invalid stanza name {self.name!r}")
        if not self.lines:
            raise ValueError(f"stanza {self.name!r} cannot be empty")
        if not all(isinstance(line, LyricLine) for line in self.lines):
            raise ValueError("stanza lines must be LyricLine objects")

    @classmethod
    def from_yaml(cls, name: object, value: object) -> Stanza:
        """Validate and construct a stanza from its YAML key and value."""

        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise ValueError(f"stanza {name!r} must contain a list")
        return cls(name, [LyricLine.from_dict(line) for line in value])

    def to_yaml(self) -> list[dict[str, str]]:
        """Return the YAML-compatible list for this stanza."""

        return [line.to_dict() for line in self.lines]


@dataclass
class Hymn:
    """A validated hymn with YAML and Pandoc Markdown codecs."""

    category: LocalizedText
    stanzas: list[Stanza]
    author: LocalizedText | None = None
    #: Who set the hymn to music, as the *Index of Authors and Composers*
    #: credits it -- a name, an arranger, or the collection a melody came out
    #: of.  Localized like ``author`` because it is written the same way, and
    #: English-only for the same reason: the index is the English edition's.
    composer: LocalizedText | None = None
    #: Why this hymn's credit is not simply what one page prints.  The English
    #: edition prints its credits twice -- in the *Index of Authors and
    #: Composers* and, on a copyrighted song, over the hymn itself -- and on
    #: three hymns the two name different people.  Where `data/` had to choose
    #: or combine, this says so, so that a reader who checks either printing
    #: finds the discrepancy recorded rather than a silent third reading.
    #: English-only, like the credits it is about.
    credit_note: LocalizedText | None = None
    #: The stanzas the chorus is not sung after, where the book says so.  A
    #: chorus is otherwise sung after every stanza, and both 355 and 734 end on
    #: a verse: 355 is verse, chorus, verse -- its *D.C. al Fine* is how the
    #: score sends the second stanza back to the verse's music -- and both
    #: print a direction not to sing the chorus again.  The numbers are the
    #: stanzas', which the Chinese half of each direction names.
    chorus_omitted: list[int] | None = None
    meter: str | LocalizedText | None = None
    #: What the hymnal says about singing this hymn, in its own words: which
    #: lines to repeat, which stanza leaves the chorus out, which stanzas the
    #: other edition does not have.  A list, because the book prints more than
    #: one on a hymn -- 355 carries a direction under each of its two stanzas.
    #:
    #: A note is set apart from the stanza on the page and governs how the hymn
    #: is sung, which is why it is here and not in the lyrics.  A note *about a
    #: word* -- what `Beulah` means, that `Christ` may be sung as `Jesus` -- is
    #: the other thing the book prints, and stays in the line as an inline
    #: footnote, anchored where it belongs.
    note: list[LocalizedText] = field(default_factory=list)
    ref: LocalizedText | None = None
    #: Which lines the hymn sings again, where the book says so without
    #: writing them out.  See ``Repeat``.
    repeat: Repeat | None = None
    title: LocalizedText | None = None
    #: The tune the English edition sets the hymn to, and the second one where
    #: it prints two.  Not localized: a tune has one name, in the edition that
    #: names it.
    tune: str | list[str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.category, LocalizedText):
            raise ValueError("category must be localized text")
        if not self.stanzas or not all(isinstance(stanza, Stanza) for stanza in self.stanzas):
            raise ValueError("a hymn must contain stanzas")
        names = [stanza.name for stanza in self.stanzas]
        if len(names) != len(set(names)):
            raise ValueError("stanza names must be unique")
        if self.meter is not None and not isinstance(self.meter, (str, LocalizedText)):
            raise ValueError("meter must be a string or localized text")
        if self.tune is not None:
            tunes = self.tune if isinstance(self.tune, list) else [self.tune]
            if not tunes or not all(isinstance(name, str) and name for name in tunes):
                raise ValueError("tune must be a name or a list of names")
            if len(tunes) != len(set(tunes)):
                raise ValueError("a hymn cannot be set to one tune twice")
        for name in ("author", "composer", "credit_note", "ref", "title"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, LocalizedText):
                raise ValueError(f"{name} must be localized text")
        if not isinstance(self.note, list) or not all(
            isinstance(value, LocalizedText) for value in self.note
        ):
            raise ValueError("note must be a list of localized text")
        if self.chorus_omitted is not None:
            numbered = {stanza.name for stanza in self.stanzas if isinstance(stanza.name, int)}
            omitted = self.chorus_omitted
            if not isinstance(omitted, list) or not omitted or not all(
                isinstance(number, int) and not isinstance(number, bool)
                for number in omitted
            ):
                raise ValueError("chorus-omitted must be a non-empty list of stanza numbers")
            if len(omitted) != len(set(omitted)):
                raise ValueError("chorus-omitted stanzas must be distinct")
            for number in omitted:
                if number not in numbered:
                    raise ValueError(
                        f"chorus-omitted names stanza {number}, which this hymn has not"
                    )
            if len(numbered) == len(names):
                raise ValueError("chorus-omitted is given for a hymn with no chorus")
        if self.repeat is not None and not isinstance(self.repeat, Repeat):
            raise ValueError("repeat must be a Repeat")
        if self.repeat is not None:
            names = {stanza.name for stanza in self.stanzas}
            for name in self.repeat.stanzas or ():
                if name not in names:
                    raise ValueError(f"repeat names stanza {name}, which this hymn has not")
            longest = max(
                len(stanza.lines)
                for stanza in self.stanzas
                if self.repeat.sung_in(stanza.name)
            )
            for line in self.repeat.lines:
                if line > longest:
                    raise ValueError(
                        f"repeat names line {line} of a stanza that has {longest}"
                    )

    @classmethod
    def from_dict(cls, value: object) -> Hymn:
        """Validate and construct a hymn from a YAML-compatible mapping."""

        mapping = _mapping(value, "hymn")
        allowed = {
            "author", "category", "chorus-omitted", "composer", "credit-note",
            "meter", "note", "ref", "repeat", "stanza", "title", "tune",
        }
        unknown = set(mapping) - allowed
        missing = {"category", "stanza"} - set(mapping)
        if unknown:
            raise ValueError(f"unknown hymn fields: {sorted(unknown)!r}")
        if missing:
            raise ValueError(f"missing hymn fields: {sorted(missing)!r}")

        stanza_mapping = _mapping(mapping["stanza"], "stanza")
        meter: str | LocalizedText | None = None
        if "meter" in mapping:
            meter_value = mapping["meter"]
            if isinstance(meter_value, Mapping):
                meter = LocalizedText.from_dict(meter_value, "meter")
            elif isinstance(meter_value, str):
                meter = meter_value
            else:
                raise ValueError("meter must be a string or localized mapping")

        tune: str | list[str] | None = None
        if "tune" in mapping:
            tune_value = mapping["tune"]
            if isinstance(tune_value, str):
                tune = tune_value
            elif isinstance(tune_value, Sequence):
                tune = [str(name) for name in tune_value]
            else:
                raise ValueError("tune must be a name or a list of names")

        chorus_omitted: list[int] | None = None
        if "chorus-omitted" in mapping:
            omitted_value = mapping["chorus-omitted"]
            if isinstance(omitted_value, (str, bytes)) or not isinstance(
                omitted_value, Sequence
            ):
                raise ValueError("chorus-omitted must be a list")
            # Read back out of `data/N.md` these arrive as strings, as a
            # repeat's do: Pandoc metadata has no numbers.
            chorus_omitted = [int(number) for number in omitted_value]

        def optional_text(name: str) -> LocalizedText | None:
            if name not in mapping:
                return None
            return LocalizedText.from_dict(mapping[name], name)

        # The upstream collection carries at most one note per hymn and writes
        # it as a bare mapping; the hymnal prints as many as it needs to.  One
        # is read as a list of one so that nothing has to know which it was.
        note_value = mapping.get("note", [])
        notes = [
            LocalizedText.from_dict(item, "note")
            for item in (
                note_value if isinstance(note_value, Sequence)
                and not isinstance(note_value, (str, Mapping))
                else [note_value]
            )
        ]

        return cls(
            category=LocalizedText.from_dict(mapping["category"], "category"),
            repeat=Repeat.from_dict(mapping["repeat"]) if "repeat" in mapping else None,
            stanzas=[Stanza.from_yaml(name, lines) for name, lines in stanza_mapping.items()],
            author=optional_text("author"),
            chorus_omitted=chorus_omitted,
            composer=optional_text("composer"),
            credit_note=optional_text("credit-note"),
            meter=meter,
            note=notes,
            ref=optional_text("ref"),
            title=optional_text("title"),
            tune=tune,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical YAML mapping used by the source collection."""

        result: dict[str, Any] = {}
        if self.author is not None:
            result["author"] = self.author.to_dict()
        result["category"] = self.category.to_dict()
        if self.chorus_omitted is not None:
            result["chorus-omitted"] = list(self.chorus_omitted)
        if self.composer is not None:
            result["composer"] = self.composer.to_dict()
        if self.credit_note is not None:
            result["credit-note"] = self.credit_note.to_dict()
        if self.meter is not None:
            result["meter"] = (
                self.meter.to_dict()
                if isinstance(self.meter, LocalizedText)
                else self.meter
            )
        if self.note:
            result["note"] = [value.to_dict() for value in self.note]
        if self.ref is not None:
            result["ref"] = self.ref.to_dict()
        if self.repeat is not None:
            result["repeat"] = self.repeat.to_dict()
        result["stanza"] = {stanza.name: stanza.to_yaml() for stanza in self.stanzas}
        if self.title is not None:
            result["title"] = self.title.to_dict()
        if self.tune is not None:
            result["tune"] = list(self.tune) if isinstance(self.tune, list) else self.tune
        return result

    def to_document(self) -> pf.Doc:
        """Construct the internally language-tagged Panflute document."""

        blocks: list[pf.Block] = []
        for stanza in self.stanzas:
            blocks.append(pf.Header(pf.Str(str(stanza.name)), level=1))
            lyric_lines = [
                inlines for line in stanza.lines for inlines in line.to_inlines()
            ]
            paragraph: list[pf.Inline] = []
            for index, inlines in enumerate(lyric_lines):
                if index:
                    paragraph.append(pf.LineBreak())
                paragraph.append(inlines)
            blocks.append(pf.Para(*paragraph))

        metadata: dict[str, Any] = {"auto-lang": AUTO_LANG}
        if self.author is not None:
            metadata["author"] = _localized_metadata(self.author)
        metadata["category"] = _localized_metadata(self.category)
        if self.chorus_omitted is not None:
            metadata["chorus-omitted"] = pf.MetaList(
                *(pf.MetaInlines(pf.Str(str(number))) for number in self.chorus_omitted)
            )
        if self.composer is not None:
            metadata["composer"] = _localized_metadata(self.composer)
        if self.credit_note is not None:
            metadata["credit-note"] = _localized_metadata(self.credit_note)
        if self.meter is not None:
            metadata["meter"] = (
                _named_metadata(self.meter, "meter")
                if isinstance(self.meter, LocalizedText)
                else pf.MetaInlines(pf.RawInline(self.meter, format="markdown"))
            )
        if self.note:
            metadata["note"] = pf.MetaList(
                *(_localized_metadata(value) for value in self.note)
            )
        if self.ref is not None:
            # One language has nothing to cut apart, so it is written flat like
            # every other localized field; two are named.
            metadata["ref"] = (
                _named_metadata(self.ref, "reference")
                if len(self.ref.translations) > 1
                else _localized_metadata(self.ref)
            )
        if self.repeat is not None:
            metadata["repeat"] = self.repeat.to_metadata()
        if self.title is not None:
            metadata["title"] = _localized_metadata(self.title)
        if self.tune is not None:
            metadata["tune"] = _tune_metadata(self.tune)
        document = pf.Doc(*blocks, metadata=metadata)
        # Panflute 2.0 defaults to an API version rejected by Pandoc 3.8.
        document.api_version = pandoc_api_version()
        return document

    def to_markdown(self) -> str:
        """Render this hymn as standalone, unwrapped Pandoc Markdown."""

        markdown = pf.convert_text(
            self.to_document(),
            input_format="panflute",
            output_format=PANDOC_MARKDOWN,
            standalone=True,
            extra_args=[f"--lua-filter={STRIP_LANG_FILTER}", "--wrap=none"],
        )
        return _strip_auto_lang(markdown)

    @classmethod
    def from_markdown(cls, markdown: str) -> Hymn:
        """Parse and validate one hymn from Pandoc Markdown."""

        source_lines = iter(_lyric_sources(markdown))
        document = pf.convert_text(
            _inject_auto_lang(markdown),
            input_format=PANDOC_MARKDOWN,
            output_format="panflute",
            standalone=True,
            extra_args=[
                f"--lua-filter={AUTO_LANG_FILTER}",
                f"--lua-filter={PRESERVE_MARKDOWN_FILTER}",
            ],
        )
        plain_metadata = document.get_metadata()
        if "stanza" in plain_metadata:
            raise ValueError("stanza is body content and cannot appear in front matter")
        if plain_metadata.get("auto-lang") != AUTO_LANG:
            raise ValueError(f"auto-lang must be {AUTO_LANG!r}")

        allowed_metadata = {
            "auto-lang",
            "author",
            "category",
            "chorus-omitted",
            "composer",
            "credit-note",
            "meter",
            "note",
            "ref",
            "repeat",
            "title",
            "tune",
        }
        unknown = set(plain_metadata) - allowed_metadata
        if unknown:
            raise ValueError(f"unknown hymn metadata fields: {sorted(unknown)!r}")
        if "category" not in document.metadata:
            raise ValueError("missing hymn metadata field: 'category'")

        metadata: dict[str, Any] = {}
        if "author" in document.metadata:
            metadata["author"] = _localized_from_metadata(
                document.metadata["author"], "author"
            ).to_dict()

        metadata["category"] = _localized_from_metadata(
            document.metadata["category"], "category"
        ).to_dict()

        if "composer" in document.metadata:
            metadata["composer"] = _localized_from_metadata(
                document.metadata["composer"], "composer"
            ).to_dict()

        if "credit-note" in document.metadata:
            metadata["credit-note"] = _localized_from_metadata(
                document.metadata["credit-note"], "credit-note"
            ).to_dict()
        if "meter" in document.metadata:
            meter = _named_from_metadata(document.metadata["meter"])
            metadata["meter"] = (
                meter.to_dict()
                if meter is not None
                else pf.stringify(document.metadata["meter"])
            )
        if "tune" in document.metadata:
            metadata["tune"] = _tune_from_metadata(document.metadata["tune"])
        if "note" in document.metadata:
            metadata["note"] = [
                value.to_dict()
                for value in _notes_from_metadata(document.metadata["note"])
            ]
        if "ref" in document.metadata:
            reference = _named_from_metadata(document.metadata["ref"])
            metadata["ref"] = (
                reference.to_dict()
                if reference is not None
                else _localized_from_metadata(document.metadata["ref"], "ref").to_dict()
            )

        if "chorus-omitted" in plain_metadata:
            metadata["chorus-omitted"] = plain_metadata["chorus-omitted"]

        if "repeat" in plain_metadata:
            # Read from the plain metadata rather than the tagged tree: these
            # are numbers, and a number belongs to no writing system, so
            # `auto-lang.lua` leaves them alone.
            metadata["repeat"] = plain_metadata["repeat"]

        stanza: dict[int | str, list[dict[str, str]]] = {}
        current_name: int | str | None = None
        current_lines: list[dict[str, str]] = []
        for block in document.content:
            if isinstance(block, pf.Header):
                if block.level != 1:
                    raise ValueError("each stanza must begin with a level-one heading")
                if current_name is not None:
                    if not current_lines:
                        raise ValueError(f"stanza {current_name!r} cannot be empty")
                    stanza[current_name] = current_lines
                heading = pf.stringify(block)
                current_name = int(heading) if heading.isdecimal() else heading
                if current_name in stanza:
                    raise ValueError(f"duplicate stanza heading {current_name!r}")
                current_lines = []
            elif isinstance(block, pf.Para) and current_name is not None:
                if current_lines:
                    raise ValueError("each stanza must contain exactly one lyric paragraph")
                line_languages = _paragraph_languages(block)
                block_sources: list[str] = []
                for _ in line_languages:
                    try:
                        block_sources.append(next(source_lines))
                    except StopIteration as error:
                        raise ValueError(
                            "Markdown source has fewer lyric lines than Pandoc parsed"
                        ) from error
                current_lines.extend(
                    line.to_dict()
                    for line in LyricLine.from_languages(
                        line_languages, block_sources
                    )
                )
            else:
                raise ValueError(
                    "document body must contain stanza headings and lyric paragraphs"
                )
        if current_name is not None:
            if not current_lines:
                raise ValueError(f"stanza {current_name!r} cannot be empty")
            stanza[current_name] = current_lines

        try:
            next(source_lines)
        except StopIteration:
            pass
        else:
            raise ValueError("Markdown source has more lyric lines than Pandoc parsed")

        metadata["stanza"] = stanza
        if "title" in document.metadata:
            metadata["title"] = _localized_from_metadata(
                document.metadata["title"], "title"
            ).to_dict()
        return cls.from_dict(metadata)


def _front_matter_end(lines: Sequence[str]) -> int:
    """Return the index of a Markdown document's closing YAML delimiter."""

    if not lines or lines[0] != "---":
        raise ValueError("hymn Markdown must begin with a YAML metadata block")
    for index, line in enumerate(lines[1:], start=1):
        if line in {"---", "..."}:
            return index
    raise ValueError("unterminated YAML metadata block")


def _paragraph_languages(paragraph: pf.Para) -> list[set[str]]:
    """Return inferred languages for each physical line in a paragraph."""

    result: list[set[str]] = [set()]

    def visit(element: pf.Element, inherited: str | None = None) -> None:
        if isinstance(element, pf.LineBreak):
            result.append(set())
            return
        language = _language(element) or inherited
        if language:
            result[-1].add(language)
        content = getattr(element, "content", None)
        if content is not None:
            for child in content:
                if isinstance(child, pf.Element):
                    visit(child, language)

    for inline in paragraph.content:
        visit(inline)
    return result


def _inject_auto_lang(markdown: str) -> str:
    """Inject the collection's script map into Pandoc's Markdown input."""

    lines = markdown.splitlines()
    end = _front_matter_end(lines)
    if any(re.match(r"^auto-lang\s*:", line) for line in lines[1:end]):
        raise ValueError("auto-lang is injected by the reader and must not be stored")
    lines[1:1] = ["auto-lang:", "  Han: zh", "  Latin: en"]
    return "\n".join(lines) + "\n"


def _strip_auto_lang(markdown: str) -> str:
    """Strip the internal script map from Pandoc's Markdown output."""

    lines = markdown.splitlines()
    end = _front_matter_end(lines)
    auto_lang = ["auto-lang:", "  Han: zh", "  Latin: en"]
    for index in range(1, end - len(auto_lang) + 1):
        if lines[index : index + len(auto_lang)] == auto_lang:
            del lines[index : index + len(auto_lang)]
            return "\n".join(lines) + "\n"
    raise ValueError("Pandoc output is missing the internal auto-lang map")


def _lyric_sources(markdown: str) -> list[str]:
    """Return the Markdown source of each physical lyric line."""

    lines = markdown.splitlines()
    end = _front_matter_end(lines)

    sources: list[str] = []
    for line in lines[end + 1 :]:
        if line and not line.startswith("# "):
            sources.append(line)
    return sources
