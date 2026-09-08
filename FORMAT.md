# The Markdown representation of a hymn

`data/N.md` is a bidirectionally lossless projection of one item of the YAML
collection `data/` was bootstrapped from. This is the contract it keeps; how it
is generated, and what else is built from it, is in
[DEVELOPER.md](DEVELOPER.md).

## Stanzas

The checked-in Markdown contains no Pandoc bracketed-span syntax. Each stanza
is a level-one heading followed by one paragraph whose physical lines are hard
line breaks. English and Chinese translations are adjacent lines within that
paragraph.

```markdown
# 1

God, our Father, we adore Thee!
阿爸父神，我們拜你，
We, Thy children, bless Thy Name!
稱頌你名永無止！
```

Text scalars in the canonical YAML are Markdown source, not literal text. The
projection therefore preserves inline constructs such as `*emphasis*` and
`^[inline notes]`; the converter's temporary language spans do not escape or
flatten that markup.

**No lyric is written with a Markdown escape**, and `tests/test_conversion.py`
asserts it over all 848 files. One page prints square brackets in its text —
`en/56` sets hymn 42's `The Father only [glorious claim]!` — and they are
written plainly, because a bracket that cannot begin a link needs no escape:
Pandoc reads and writes either spelling unchanged, so the readable one is the
source of record. A backslash anywhere in `data/` therefore means something has
gone in that the page does not print.

**Each edition is written with its own marks**, because the book sets each in
its own typography and one file holds both. A Chinese lyric line holds Han
characters and `，。、；：！？“”（）——…`; an English one holds Latin letters, a
space, and `,.;:!?-—()[]“”’`. `pixi run check-punctuation` asserts it over all
848 files, along with the rule the re-lineations were done under — a closing
mark stays with the line it closes, an opening mark goes with the line it
opens, and the dash counts as closing — and the pairing of quotation marks,
strict in Chinese and, in English, only that none is closed before it is
opened.

Two marks are in those sets for one line apiece, and the page is the reason:
`zh/439` prints 418's `…` and `en/847` prints 797's spaced `–`. The English is
never normalised toward ASCII. `PANDOC_MARKDOWN` disables `smart`, so what is
in `data/` is what the page prints, and `'tis` would be set as `‘tis` where the
book prints `’tis` — the mark is an elision, not a quotation.

The canonical language order is English then Chinese. After `auto-lang.lua`
restores the language of each line, a repeated language or a transition from
Chinese back to English marks the next YAML lyric-line mapping. This also
retains runs of English-only or Chinese-only mappings without placeholders.

## What the hymnal says beside the hymn

The book prints two kinds of prose about a hymn, and they are kept apart by
where they are written.

A **direction** governs how the hymn is sung — which lines to repeat, which
stanza leaves the chorus out, which stanzas the other edition does not have,
why no music is printed. The page sets it apart from the stanza, in parentheses
under the last line, so it is front matter, under `note`. `note` is a list:
the hymnal prints more than one on a hymn, and 355 prints one under each of its
two stanzas.

```yaml
note:
- Repeat the last four lines第四節末兩行重唱一遍
- This hymn may be sung to the tune of “Pass It On” (Not printed here due to copyright)
```

A **gloss** is a word about a word of the hymn: what `Beulah` means, that
`基督` may be sung as `耶穌`. The page anchors it — with an asterisk in the
line on 324, and elsewhere by quoting the word and naming its stanza — and
prints it at the foot. So it stays in the lyric line, as an inline footnote,
after the word it is about.

```markdown
明亮晨星^[第二節的“明亮晨星”指主基督]的光華，
```

**A repeat is stated three ways and `repeat` is the one anything can act on.**
The book writes the lines out a second time, or prints a direction —
*Repeat the last line of each stanza*, `每節重唱最後一行` — or marks the meter
`重` / `with repeat` and leaves the shape to the music. Where the lines are
written out `data/` already holds them; the other two are written down as
front matter, and 28 hymns carry it.

```yaml
repeat:
  lines: [5, 6, 7, 8]
  stanzas: [4]
```

`lines` are the stanza's own lines, numbered from one, in the order they are
sung again — not always a tail, because `en/71` sets hymn 57's repeat as the
fourth line twice and then the third and fourth again. `stanzas` is every
stanza unless it names some. It is not localized: every stanza of every hymn
that carries a repeat has the same number of lines in both editions.
`pixi run check-repeats` holds the three statements against one another, and a
*da capo* — 355's `回頭再唱正歌一遍`, the whole verse again after the chorus —
is the one form it does not hold.

Neither is inferred from the words: what a note says is checkable against the
hymn, and `pixi run check-notes` checks it. A gloss written as a direction, a
gloss quoting a word its line does not hold, a note naming a stanza the hymn
does not have that way, a repeat both directed and written out — each of those
was in `data/` before the two kinds were told apart.

## Localized front matter

Localized mappings are flattened by concatenation:

```yaml
category: Praise and Worship—The Father (His Greatness)讚美和敬拜——聖父（祂的偉大）
note:
- Repeat the last two lines重複最後兩行
```

A localized meter has a shared notation followed by its language-specific
suffixes:

```yaml
meter: 11.10.11.10. with chorus和
```

The codec expands the shared `11.10.11.10. ` prefix back into both YAML values.
A meter with zero or one detected language remains a YAML scalar.

`credit-note` is localized like any other and flattens the same way, but it is
the one field here that is not a quotation. Every other value is read off a
printed page; this one says why a credit reads as it does on the three hymns
whose two printings name different people, and it is written by
[`authors.py`](DEVELOPER.md#the-credits-table) rather than transcribed. It
carries English alone, like the credits it is about.

A meter whose two languages share no notation has none factored out and is
stored as any other localized field is:

```yaml
meter: Irregular Meter特.和
```

## How the languages are recovered

When Markdown is read, the codec injects an `auto-lang` map from Unicode script
to the collection's language tags, and `auto-lang.lua` restores temporary
`lang` spans in the Pandoc tree. The Python codec uses those spans to rebuild
the localized YAML mappings. When Markdown is written, `strip-lang.lua` removes
the temporary spans, and the codec removes the injected map before returning
the source.

The Lua filters and their generated Unicode script table are vendored under
`src/hymn_projection/filters`; their exact origin is recorded in the README
there.

## What this cannot do

The inference is checked against the complete source collection by the test
and regeneration workflow. Text which cannot be distinguished by Unicode
script must be corrected in the canonical data or represented explicitly;
script detection cannot recreate information absent from the text.
