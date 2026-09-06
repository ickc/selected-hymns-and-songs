# Selected Hymns 詩歌選集

The text of the hymnal, kept as data so that it can be published in more than
one way. 848 hymns, English and Traditional Chinese together.

## The data

`data/N.md` — one Markdown file per hymn, numbered as the hymnal numbers them.
This is the source everything else is built from.

It is a lossless projection of the canonical YAML collection in
[`selected-hymns`](https://github.com/ickc/selected-hymns): each hymn can be
converted back to the canonical shape and comes out unchanged.
[FORMAT.md](FORMAT.md) describes what the Markdown looks like and why.

`data/categories.tsv` — what each hymn's Chinese subject is called in the
English edition, read off that edition's subject index. A hymn's category is
the one field of `data/N.md` that is written from somewhere else; see
[DEVELOPER.md](DEVELOPER.md).

`scan/` — the hymnal itself: one image per page of each language edition, and
the page each hymn is printed on. `data/` was read off these and corrected
against them, so where the two disagree the page is right. See
[scan/README.md](scan/README.md).

Both are carried in git. Everything else is generated.

## What is published from it

**<https://ickc.github.io/selected-hymns-and-songs/>** — the site, rebuilt from
`data/` on every push to `main`:

- **Open a hymn by its number.** A hymn is called out by number in a meeting,
  so typing the number is the whole of it; the hymn opens in a new tab, as
  slides to project or as text beside the scanned page.
- **Or search for it** from the box in the header, by a line, a title or a
  phrase in either language. The search reaches every slide, so a
  half-remembered line is enough, and it opens the hymn at that stanza.
- **Each hymn as slides to project**, one stanza at a time with the chorus that
  belongs to it, both languages, sized to fill the screen without overflowing
  it. Add `?grid` to a hymn's URL for two aligned columns instead of
  interleaved lines.
- **Or each hymn beside the hymnal**, the text in the middle and the scanned
  page of each edition either side of it, scrolling independently. Follow the
  music while the words are in front of you, or check a line against the book —
  the scan is the authority, and the page links to the file a typo is fixed in.
  Switch to one language, or to text or scans alone; on a phone the panes
  become a swipe. What is on screen is in the address bar, so a view can be
  sent to someone.

More products from the same data may follow.

## Working on it

[DEVELOPER.md](DEVELOPER.md) — the architecture, the tasks, and how it is
built, checked and published.
