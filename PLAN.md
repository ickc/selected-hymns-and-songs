# Plan

Proposals, not commitments. Nothing here is built. Each section says what the
book actually contains, what `data/` already has, what is genuinely missing,
and what it would cost — so the decision to build it can be made on evidence
rather than on optimism.

Page numbers below are **PDF page numbers** in
[`selected-hymns-and-songs-pdf`](https://github.com/ickc/selected-hymns-and-songs-pdf)
(`en/NNN.txt`, `zh/NNN.txt`, and the matching `.json` with per-line bounding
boxes), because that is where you go to look. The printed page numbers differ.

---

## 1. Where the data stands

### Every field, counted

| field | hymns | both languages? | verdict |
| --- | --- | --- | --- |
| `category` | 848 | yes, all 848 | done |
| `stanza` | 848 | 809 both, 39 Chinese-only | see D5/D6 |
| `meter` | 710 | n/a — notation is shared | 138 missing, see D1 |
| `note` | 25 | 19 both, 6 Chinese-only | see D4 |
| `ref` | 11 | 0 both — 6 English-only, 5 Chinese-only | see D3 |
| `author` | 4 | 0 both — all English-only | see D2 |
| `title` | 0 | — | correctly empty; the hymnal prints no titles |

So: **no, not every field is bilingual.** `category` is, now. `meter` is
effectively bilingual because the numeric notation is shared and the only
worded parts (`with chorus` / `和`, `with repeat` / `重`) are already carried in
both — 105 distinct localized meters, 0 with a Chinese half missing. But
`author`, `ref` and six of the `note`s are single-language, and three hymns are
missing an entire language of lyrics.

### Structure is clean

All 848 files parse, stanza numbering is `1..n` with no gaps or duplicates on
every hymn, and 32 hymns carry more than one chorus (already handled by the
chorus resolution and its report). No structural defects found.

---

## 2. Defects beyond the title and the category

### D1 — 138 hymns have no meter, and most of them should say "Irregular"

The English page prints `Irregular Meter` and the Chinese page prints `特`
(`特和` when there is a chorus). 93 English pages contain the word
`Irregular`; `data/` contains it zero times. Hymn 840 is typical: the Chinese
page reads `特`, `data/840.md` has no `meter` at all.

101 of the 138 are hymns ≤ 764, so the English metrical index (§6) can confirm
them wholesale; 37 are in the Chinese-only appendix and must be read off the
Chinese page.

**This one has a model consequence.** `_meter_metadata` factors a localized
meter into a shared numeric prefix plus per-language suffixes, and asserts the
shared part matches `METER_PREFIX` (`(?:[0-9]+\.)+(?:D\.)?\s+`). `Irregular
Meter` and `特` share nothing. Adding irregular meters therefore requires
either relaxing that rule or giving the meter a second representation. Worth
deciding before the extraction, not after.

### D2 — `author` is populated on 4 hymns out of 848

416 Graham Kendrick, 439 Thomas O. Chisholm, 453 Dennis Cleveland, 749 Bob
McGee. All English-only, and all four are copyright-bearing songs — which is
exactly the set the preface says is *not* in the author index ("Author's and
composer's names, except for copyright-bearing songs, are listed numerically in
an index at the rear of the book"). So these four came off the hymn page
itself, and the other ~760 are sitting in an index nobody has read yet. That is
proposal §5.

### D3 — `ref` is inconsistent, monolingual, and partly redundant

All eleven of them:

```
108 Psalm 45 - Part 1     245 啟一章
109 Psalm 45 - Part 2     246 啟二、三章
110 Psalm 110             247 啟三章
111 Psalm 8               248 啟三章
112 Psalm 68              189 以西結書第47章
749 "Isaiah 7:14"
```

Six English, five Chinese, none both. Three different citation styles in the
Chinese alone (`啟一章`, `啟二、三章`, `以西結書第47章`). And 749's `ref` is a
verbatim duplicate of the scripture reference already inside its own category,
`Psalms and Scripture Portions—Isaiah 7:14 / 詩篇與經文片段——賽7:14`.

Decide what `ref` is *for* before filling it in. Two coherent readings:

- **It is the scripture a hymn versifies.** Then hymns 734–764 have it in
  their category already and `ref` should be derived from there, not duplicated
  beside it; and 108–112, 189, 245–248 are the handful outside that section
  that also carry one.
- **It is a note printed on the page.** Then it should be read off all 848
  pages, in whichever language prints it, and left absent where nothing is
  printed.

My reading is the second — `Psalm 45 - Part 1` is a page annotation, not a
category — but either way the field currently means neither thing
consistently. Cheapest honest fix: audit those eleven pages, normalise the
citation style within each language, and fill the missing half where the other
edition prints one.

### D4 — six `note`s have lost their English half

470, 584, 611, 659, 705, 720 carry Chinese only (`最後一句唱兩遍`,
`重唱每節最後一行`). All six are ≤ 764, so an English page exists for each. The
other nineteen are bilingual and say the same thing in English
(`Repeat the last line of each stanza`). The OCR of those six English pages is
too poor to settle whether the English edition prints the note or not — it has
to be read off the page image.

While there: the English wording is not normalised either — `Repeat the last
two lines` (71, 76) vs `Repeat the last 2 lines` (282, 290), and
`Repeat last two lines of each stanza` (638) without the leading article.

### D5 — three hymns are missing their English lyrics entirely

**797, 824, 845.** `scan/en.csv` gives each an English page (847–848, 866,
875), and the English edition's own list of Chinese-only hymns (`en/923.txt`,
*Hymns Available In Chinese But Not In English*) does not include them. English
page 847 plainly prints hymn 797 as *"Thy way, not mine, 0 Lord"* — and
`data/797.md` has four Chinese stanzas and no English at all.

This is the largest single gap in the collection: three hymns' worth of English
text that the book prints and we do not have. It is also a straightforward
transcription job, not a research one.

### D6 — three hymns carry English the book does not print

**779, 789, 840.** All three are in the English edition's own list of
Chinese-only hymns, both scans agree (`scan/en.csv` has both bounds empty), and
the Chinese page carries no English line — yet `data/` has full English lyrics
for each: *"Behold, how good, how pleasant 'tis"*, *"Lord, in Thy presence we
are met"*, *"There were ninety and nine that safely lay"*. Someone supplied the
original English these Chinese texts were translated from.

That is probably a *good* thing to have, but it is undocumented, and it means
the hymn page shows English with no English scan beside it to check it
against. Either document it as a deliberate addition (a fourth entry in
DEVELOPER.md's list of departures from the scan) or drop it. I would keep it
and say so.

Note that D5 and D6 cancel out numerically — 39 hymns lack English text in
`data/` and 39 are absent from the English edition — which is exactly why
nobody noticed the two sets are not the same 39.

### D7 — one hymn's meter may disagree with its page

The Chinese page for 779 (`zh/838.txt`) reads `6. 4. 6. 4 雙`; `data/779.md`
says `8.6.8.6.D.`. The OCR may be wrong. Nobody has ever run the
category-versus-page-header audit for the *meter* half of the same header line,
and it costs almost nothing to run now that the tooling exists. Do it before
building anything on top of `meter` (§6 depends on it).

### D8 — the category is single-valued, but the book's index is not

The subject index files some hymns under several subjects. Hymn 13 is under
*(5) His Love* **and** *(8) His Sonship* (Chinese: 祂的愛 and 祂的兒子名分);
hymn 133 is under *(14) His Kingdom* and *(26) Rejoicing in Him*. The hymn
*page* prints exactly one subject, and that is what `data/N.md` carries.

So `category` is the hymn's **home** subject, and the index has placements the
home subject does not capture. A faithful subject-index page (§4) needs the
many-to-many relation, which lives in the index, not in `data/N.md`. This is a
design fact, not a defect — but it decides the shape of §4.

### D9 — the order of the subjects is lost

`data/categories.tsv` is sorted by the lowest hymn number filed under each
subject. That is *not* the book's order. Under *The Father*, the book runs
Greatness, Glory, Majesty, Mercy, Love, Faithfulness, Redemption, Sonship,
Crying Abba; sorted by first hymn number it comes out Greatness, Glory, Love,
Redemption, Majesty, Mercy, Crying Abba, Faithfulness, Sonship. The printed
numbering (`I.` / `2.` / `(1)`) is the order, and we did not keep it.

### D10 — fixed in passing

`DEVELOPER.md` still said the category table had 290 rows; it has had 286 since
four rows were dropped. Corrected.

---

## 3. The preface

**Source.** Two pages, one each: `en/001` (English *PREFACE*, ~2.6 kB of OCR)
and `zh/001` (Chinese *編者的話*, ~1.1 kB).

**They are not translations of each other.** The English preface is about how
764 hymns were chosen out of three centuries of English hymnody, who is
represented, and what the indexes are. The Chinese 編者的話 is about how the
Chinese edition was assembled *afterwards* — existing Chinese translations
sought out and revised to match the English tune, meter and stanza count, the
missing ones newly translated, and hymns 765–848 added because good Chinese
hymns had no English counterpart. It even asks bilingual meetings to avoid
choosing from that appendix. Two documents, one book. Present them as two, not
as a bilingual pair.

The Chinese preface is, incidentally, the primary-source explanation of the
whole 765–848 structure this project keeps running into.

**Why an LLM is the right tool.** The OCR is legible but corrupt in ways only a
reader can repair: `aud` for `and`, `fonnat` for `format`, `sainL~.` for
`saints,`, `·111e` for `The`, `Tree of Lite Publishers` for `Tree of Life
Publishers`. Every one of those is unambiguous *in context* and unfixable by
rule. The job is: read the page image, read the OCR, emit the text, and flag
anything the two disagree on rather than guessing.

**Where it lives.** Not in `data/N.md` — it is not a hymn.
`data/preface.en.md` and `data/preface.zh.md`, plain Pandoc Markdown with the
same YAML-front-matter habit, seems right; the site grows an `about` page
rendering both. Consider recording the transcription's provenance in the front
matter (which PDF page, which method) so a later reader knows it was
reconstructed rather than typed from the paper book.

**Open question.** The book's own front matter also contains the *TABLE OF
CONTENTS* (`en/002`, `zh/002`) and *INDEX OF INDEXES* (`en/003`). The TOC is
the source of the title-cased level‑1 and level‑2 subject names already in
`data/categories.tsv`; transcribing it would be cheap and would let §4's tree
show the hymn-number ranges the book prints. The index of indexes is about the
paper book's page numbers and is worthless here.

**Cost.** Small. Two pages, one reading pass each, a careful diff against the
OCR. This is the one proposal that is nearly free.

---

## 4. A subject index page

**What we have.** `data/categories.tsv`, 286 subjects, both languages, and
every one of the 848 hymns filed under exactly one of them. From that alone a
tree can be built today.

**What we are missing — three things.**

1. **The levels are implicit.** The table stores one flat string per language.
   Splitting `Praise and Worship—The Son, His Person and Work (His Divinity)`
   into three levels means splitting on the first em dash and a trailing
   parenthesis — which works, until a level‑2 name legitimately contains a
   comma (`The Son, His Person and Work`, already there) or a scripture
   reference contains a colon and digits (`Psalms and Scripture
   Portions—Psalm 126:1-3`). Parsing a format we control is silly when we can
   store it. **Proposal: widen `data/categories.tsv` to explicit level
   columns** — `zh1 zh2 zh3 en1 en2 en3`, empty where a level is absent (229 of
   286 subjects are two-level, 57 are three-level, 18 distinct level‑1
   headings). `categories.py` then joins them for `data/N.md` instead of
   splitting them apart, which is the direction that cannot go wrong. Same file,
   same idempotent apply, same CI check.

2. **The order (D9).** Add the printed numbering as columns —
   `I` / `2` / `(1)` — or a single sort key like `I.2.1`. The Chinese subject
   index (`zh/003`–`zh/007`, 主題目錄) prints all three levels numbered, and
   covers the appendix hymns in the same sequence, so it is a better single
   source for ordering than the English index, which splits 1–764 from the
   supplement. Reconstructing this is a re-read of five pages we have already
   read once for the labels.

3. **The cross-listings (D8).** The index files a hymn under every subject it
   belongs to; `data/N.md` records only its home subject. Building the tree
   from `data/N.md` alone silently drops those placements. Two honest options:
   build the tree from `data/N.md` and label the page *hymns by their printed
   subject* (cheap, self-consistent, slightly less than the book); or extract
   the full index and carry the extra placements in a second table (faithful,
   another extraction pass). I lean to the first now and the second later, if at
   all — the cross-listings are a small minority and the site has search.

**Ordering within a subject.** The book lists hymns under a subject by first
line, not by number (`Behold, what love 13` before `We praise Thee 26`). By
number is more useful on a screen and is what we can do without another
extraction. Say so on the page rather than pretending it is the book's order.

**Shape of the page.** `site/subject.md`, generated by `md-to-site` alongside
the decks and pages, from `data/categories.tsv` plus the categories in
`data/N.md`. A collapsible three-level list, both languages side by side the
way the hymn meta line does it, each hymn a number linking to `hymn/N.html`.
It should also be reachable from the navbar, which currently has only the
landing page.

**Cost.** Moderate. The generator is a day's work over data we already have;
the table widening is mechanical; the numbering is one careful reading pass
over five Chinese pages.

---

## 5. Index of authors and composers

**Source.** `en/879`–`en/894`, sixteen pages, printed 821–836. Three columns:
`Hymn | Author, Translator, Source | Composer, Arranger, Source`. Roughly 764
rows — one per hymn 1–764, many with one or both cells blank (the preface says
copyright-bearing songs are omitted, which is why we already have exactly those
four on the hymn pages, D2).

**The supplement has no author index.** The English back matter's supplement
(`en/916`–`en/923`) carries a table of contents, a first-lines index, a subject
index and the list of Chinese-only hymns — and no authors. The Chinese back
matter (`zh/923`–`zh/933`) is a first-line stroke-count index and nothing else.
So authors are available for 1–764 and for no hymn above that, and they are
English-only. Both of those are fine and should be stated on the page rather
than looking like gaps.

**Why this needs a reading pass, not a parser.** The OCR loses the column
structure completely — `en/879` extracts as a bare list of hymn numbers with
the two text columns dropped, and `en/881` and `en/887` do the same. Where the
columns do survive, the numbers are corrupt in the usual ways (`IOI` for `101`,
`I 16` for `116`, `Naida Heam` for `Naida Hearn`, `Carl Gottholf Glaser` for
`Gottlob`). The `.json` extraction carries per-line bounding boxes, which is
what made the two-column English subject index tractable before; the same trick
should work here, with the page image read visually as the check.

**Self-verification.** Unlike the category work, there is no second source to
cross-check against — no hymn-number-set matching, no Chinese counterpart. The
verification available is weaker and must be built in deliberately:

- every hymn 1–764 appears exactly once, in ascending order, no gaps;
- names recur across the book (Charles Wesley, Isaac Watts, M. E. Barber,
  Watchman Nee), so a name appearing once with an odd spelling is a flag;
- composer names cross-check against the alphabetical index of tunes (§6),
  which lists the same repertoire from a different page;
- the four authors already in `data/` must survive unchanged — a free spot check
  on four rows, and a conflict there means the extraction is wrong.

Given that, I would extract per page with an explicit "unsure" marker rather
than a confident guess, and review the flagged rows by hand.

**Where it lives.** `data/authors.tsv` — `hymn`, `author`, `composer` — read
and applied by a module beside `categories.py`, under the same contract: the
table is the rebuildable input, `data/N.md` is what the site is built from, an
idempotent `apply-authors` writes one into the other, and `check-authors` in CI
fails when they drift apart. Two new fields on the hymn (`author` exists;
`composer` does not) plus the rendering on the hymn page and the deck.

**Cost.** The largest of the four. Sixteen dense pages, ~1,500 names, weak
verification, and a model change. But it is also the one that adds the most to
each individual hymn page.

---

## 6. Metrical index of tunes

**We do not have the data.** This is worth saying plainly, because the plan
depends on it. The book's metrical index is three-level — meter, then **tune
name**, then hymn number:

```
6. 5. 6. 5. D.
  Evelyns .......... 46, 607
  Longstaff ........ 605
  McMaster ......... 147, 550
```

`data/N.md` has the meter. It has no tune name, and no field for one. What we
can build from today's data is a *metrical index of hymns* — meter, then hymn
numbers — which is a different and less useful page: it cannot tell you that
46 and 607 are sung to the same tune, which is the entire point of a metrical
index.

**So there are two proposals here, and they should not be confused.**

**6a. Metrical index of hymns** — derivable now. Group the 710 hymns that have
a meter by that meter, sort the meters numerically (not as strings: `8.6.8.6.`
before `10.10.10.10.`), list hymn numbers. Blocked in practice by D1: 138
hymns have no meter and would simply be missing from the page. Do D1 first.

**6b. Tune names** — an extraction, and a good one. Sources:

- *ALPHABETICAL INDEX OF TUNES*, `en/895`–`en/898`, four pages: tune name →
  hymn numbers. This is the mapping, and inverting it gives every hymn its tune.
- *METRICAL INDEX OF TUNES*, `en/899`–`en/904`, six pages: meter → tune name →
  hymn numbers. Same facts, grouped differently.

**Two independent sources for the same relation is the good part.** Extract
both and require them to agree: every (tune, hymn) pair in one must appear in
the other, and the meter each hymn is filed under in the metrical index must
equal the `meter` already in `data/N.md`. That is the same self-verifying
structure that made the category mapping trustworthy — disagreements are
localised and few, rather than a confidence estimate over the whole extraction.

It also pays for D1 for free: `Irregular Meters` is a heading in the metrical
index (`en/904`), so that index says which hymns are irregular, and D7's meter
audit gets a third opinion.

**Scope limits, again worth stating rather than hiding.** Tunes are English
edition only, hymns 1–764. One tune serves many hymns — `Beecher` is 1, 106,
226 and 365 — and the book sometimes prints one text twice under two tunes as
two hymn numbers (122 and 123 are both *All hail the pow'r of Jesus' name*, to
*Diadem* and to *Coronation*). Whether any single hymn number carries two tunes
is not knowable until the index is read; the model should not assume a scalar
`tune` until it is.

**Where it lives.** `data/tunes.tsv` — `hymn`, `tune`, and possibly `meter` as
the cross-check column — applied into a new `tune` field on the hymn under the
same preprocessing contract. Then both index pages (alphabetical and metrical)
are generated from `data/N.md` and are as faithful as the book's.

**Cost.** Ten pages, but far more tractable than §5 because of the double
source. Do it after D1 and D7.

---

## 7. Cross-cutting decisions

These apply to all four and should be settled once.

**The preprocessing contract holds.** `data/categories.tsv` established a
pattern worth repeating exactly: a hand-editable table in `data/`, an
idempotent `apply-*` that writes it into `data/N.md`, a `check-*` in CI that
fails when the two drift, and `data/N.md` remaining the only thing the site is
built from. Every proposal above fits it. Adding a third and fourth table means
generalising the `categories.py` machinery rather than copying it three times —
the validate-before-writing, the parallel rewrite, the "row matches no hymn"
and "value not in the table" errors are all field-agnostic already.

**Front-matter pages are not in `scan/`.** By design: `scan/` carries only the
pages some hymn occupies. Everything in §3, §4 and §5 is read off pages that
are therefore *not in this repository* — they exist only in the private PDF
project. Three options: leave it (the extraction is a one-time job and its
output is committed); extend `scan/` to carry the front and back matter too
(~70 more pages, ~1.7 MB, and the site could then show the index pages beside
the generated ones the way it does for hymns); or carry just the pages a
generated page claims to reproduce. This decides whether a future reader can
check our transcription without the private repo — which is the same argument
`scan/README.md` already makes for the hymn pages, so option 2 is the
consistent answer.

**The model will need changes.** At minimum: `meter` must accommodate
`Irregular Meter` / `特`, which breaks the shared-prefix representation (D1);
`composer` and `tune` are new fields, and `tune` may be plural (§6b). None is
hard, but each touches the codec, the round trip, and the tests, and they are
better done as one considered change than as three drive-bys.

**Extraction protocol.** What worked for the categories should be the rule:
prefer a relation that can be checked against a second source; extract with
bounding boxes and verify by reading the page image; never let OCR text be the
final authority on a digit; and record what could not be resolved in the
committed table itself rather than in a commit message.

---

## 8. Suggested order

1. **D5** — transcribe the missing English for 797, 824, 845. Largest real gap,
   no research required.
2. **D7 + D1** — audit meters against the page headers, then fill the 138
   irregulars. Unblocks §6 and settles the model change early.
3. **§3 preface** — two pages, high value, nearly free.
4. **D9 + §4** — widen the category table with levels and printed numbering,
   then generate the subject index page.
5. **§6b tunes**, then **6a** — double-sourced, self-verifying.
6. **§5 authors** — biggest, weakest verification, most valuable per hymn. Last
   because everything before it makes the tooling better.
7. **D2/D3/D4/D6** — the small consistency fixes, folded into whichever pass
   is already touching those pages.
