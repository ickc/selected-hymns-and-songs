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
projection therefore preserves inline constructs such as `*emphasis*`,
`^[inline notes]` and an escaped `\[bracket\]` the page really prints;
the converter's temporary language spans do not escape or flatten that markup.

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
