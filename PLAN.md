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
| `stanza` | 848 | 812 both, 36 Chinese-only | D5 done; see D6 |
| `meter` | 803 | n/a — notation is shared | 45 missing, see D1 |
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

### D1 — 138 hymns have no meter, and most of them should say "Irregular" — **93 done**

The English page prints `Irregular Meter` and the Chinese page prints `特`
(`特和` when there is a chorus). 93 English pages contain the word
`Irregular`; `data/` contains it zero times. Hymn 840 is typical: the Chinese
page reads `特`, `data/840.md` has no `meter` at all.

101 of the 138 are hymns ≤ 764, so the English metrical index (§6) can confirm
them wholesale; 37 are in the Chinese-only appendix and must be read off the
Chinese page.

**This one had a model consequence**, now resolved. `_meter_metadata` factored
a localized meter into a shared numeric prefix plus per-language suffixes and
asserted the shared part matched `METER_PREFIX`; `Irregular Meter` and `特`
share nothing. Both halves of the codec now fall back to storing a meter as
plain localized text when there is no shared notation to factor out, which is
what every other localized field already does.

93 hymns are done: those with no meter where every page reading of either
edition says irregular and none gives a number. 36 of them are `特.和`, the
form the Chinese page prints when the chorus is sung to the same tune — the
mark itself is the hymn having a chorus block, which agrees with the meter on
227 of the 232 hymns where both are already present.

**45 hymns still have no meter**: 9 with no legible page reading at all, and
the rest where the readings conflict or give numbers the lyrics do not scan as.
`pixi run meter-report` lists them.

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

### D5 — three hymns are missing their English lyrics entirely — **done**

**797, 824, 845.** `scan/en.csv` gives each an English page (847–848, 866,
875), and the English edition's own list of Chinese-only hymns (`en/923.txt`,
*Hymns Available In Chinese But Not In English*) does not include them. English
page 847 plainly prints hymn 797 as *"Thy way, not mine, O Lord"* — and
`data/797.md` had four Chinese stanzas and no English at all.

Transcribed off the page images. Two things turned up in the doing:

- **797 and 798 were each other.** Not only their subjects, which had already
  been swapped back: the Chinese page 855 prints 求你揀選我道路 under 797 and
  page 857 prints 我無能力 under 798, and `data/` held both hymns entire under
  the other's number. So the earlier subject-only fix had left each file
  internally inconsistent; the stanzas have now moved too.
- **824 had to be re-lineated.** The English page breaks its one stanza into
  seven six-syllable lines; `data/` had the Chinese as the four lines of its
  12.12.12.6. meter, and the Chinese page sets the text continuously under the
  staff with no lineation of its own. Re-broken at its own commas into the same
  seven, unchanged character for character.

Also: 845's fourth stanza was missing a syllable (從未拒絕人來信 for
從未曾拒絕人來信, which its 8.8.8.5. meter wants), and its four Chinese choruses
against the English edition's one are carried by the projection's existing rule
— each language takes the most recent chorus at or before its stanza — so only
`1-chorus` has an English half and `site/chorus.md` lists 845 for review.

`data/` is now Chinese-only for exactly 36 hymns, and the remaining difference
from the book's 39 is D6.

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

Note that D5 and D6 cancelled out numerically — 39 hymns lacked English text in
`data/` and 39 are absent from the English edition — which is exactly why
nobody noticed the two sets were not the same 39. With D5 done the count no
longer matches, and these three are what is left.

### D7 — one hymn's meter may disagree with its page — **tooling done, 175 left**

The Chinese page for 779 (`zh/838.txt`) reads `6. 4. 6. 4 雙`; `data/779.md`
says `8.6.8.6.D.`.

Running the audit turned out not to need the pages at all, or not first. A
meter *is* a syllable count and Chinese is one syllable to the character, so
`meters.py` counts the lyrics and `pixi run meter-report` says where the count
and the meter disagree — a check on the transcription and the meter at once,
classified by the shape of the disagreement, because the shape says which of
the two is wrong. It found the eight dropped characters listed above.

Three things it taught us about the data:

- **The two editions write a doubled tune's chorus differently, and neither is
  wrong.** Where the chorus is sung to the second half of the tune, the English
  page writes `8.7.8.7.D.` and the Chinese page writes `8.7.8.7.和` — the same
  eight sung lines, counted as one doubled verse on one page and as a verse
  plus a chorus on the other. (The Chinese also writes `6.6.6.5.雙.和` where it
  wants to say both.) 44 of the apparent disagreements were only this, and
  `data/`'s scalar `X.D.` on those hymns is the English form, correct as it
  stands.
- **Some Chinese verses were transcribed with two printed lines joined into
  one.** Hymn 69's page reads `6.6.6.5.雙.和` and prints eight half-lines two to
  a row; `data/` has four lines of 12.11.12.11 and a meter to match. Hymn 824,
  re-lineated in D5, was the same thing. This is a lineation question rather
  than a meter one, and the meter is how to find the rest of them.
- **`data/777.md`'s meter is `.8.6.8.6.6.6.7.5.`**, with a leading dot that is
  simply a typo.

**175 hymns still disagree**: 92 where every verse agrees on some other meter
than the one stored, 45 with no meter, 36 whose verses disagree with each
other, and 2 a single syllable out (453, whose page says `6.6.11.雙`, and 772,
whose page says `8.8.8.8.7.` — both meter errors, not text ones). Each needs a
page read.

### D8 — the category is single-valued, but the book's index is not

The subject index files some hymns under several subjects. Hymn 13 is under
*(5) His Love* **and** *(8) His Sonship* (Chinese: 祂的愛 and 祂的兒子名分);
hymn 133 is under *(14) His Kingdom* and *(26) Rejoicing in Him*. The hymn
*page* prints exactly one subject, and that is what `data/N.md` carries.

So `category` is the hymn's **home** subject, and the index has placements the
home subject does not capture. A faithful subject-index page (§4) needs the
many-to-many relation, which lives in the index, not in `data/N.md`. This is a
design fact, not a defect — but it decided the shape of §4: the page built in
§4 files each hymn once, under the subject its own page prints, and says so.

### D9 — the order of the subjects is lost — **done**

`data/categories.tsv` was sorted by the lowest hymn number filed under each
subject. That is *not* the book's order. Under *The Father*, the book runs
Greatness, Glory, Majesty, Mercy, Love, Faithfulness, Redemption, Sonship,
Crying Abba; sorted by first hymn number it came out Greatness, Glory, Love,
Redemption, Majesty, Mercy, Crying Abba, Faithfulness, Sonship. The printed
numbering (`I.` / `2.` / `(1)`) is the order, and we had not kept it.

The table now carries it, in `n1 n2 n3` beside `zh1 zh2 zh3` and `en1 en2 en3`,
and the reader checks it: every level has to run 1, 2, 3… under its parent, a
heading has to keep one number throughout, and a level 2 is either one subject
or a run of them.

The order was read back off the Chinese subject index (`zh/003`–`zh/007`,
主題目錄) from the OCR's own bounding boxes, two columns a page. The names were
not taken from that reading — we already had all 285 — only the sequence, which
made the pass self-checking three ways:

- all 285 subjects matched, exactly once, with nothing left over and nothing
  unmatched;
- of the 307 index lines, 222 had a printed number the OCR read legibly, and
  every one of them agreed with the position it had been given;
- 703 of the 848 hymns appear in the OCR of the index line of the very subject
  they are filed under. The 145 that do not are lines whose hymn list wrapped
  onto a continuation line, or ranges the OCR broke (`252-26l`), not
  disagreements.

It also turned up **D11**.

### D11 — hymn 583's subject was a typo — **fixed**

`data/583.md` said `因著信靠祂`; its own page (`zh/621`) prints `因著信靠主`, as
the twelve other hymns under that subject do. The table had carried both, two
rows flattening to one English heading, and the index prints only one entry —
whose hymn run, 577-579.581-584, includes 583. 285 subjects now, not 286.

### D10 — fixed in passing

`DEVELOPER.md` still said the category table had 290 rows; it had 286 by then
and has 285 now. Corrected, and it names subjects rather than rows.

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

## 4. A subject index page — **done**

`site/subject.md`, written by `md-to-site` from `data/categories.tsv` and the
category on every `data/N.md`, and reachable from the navbar. 18 sections, 232
subheadings, 57 third-level subjects, 848 hymn numbers each appearing exactly
once, in the order the book prints them.

All three of the things this section said were missing were dealt with:

1. **The levels are now explicit.** `zh1 zh2 zh3` / `en1 en2 en3`, and the code
   joins them for `data/N.md` instead of splitting them apart. 228 subjects are
   two-level and 57 three-level, under 18 level-1 headings. The join
   reproduces all 285 old rows byte for byte, which is how the widening was
   checked.
2. **The order is now stored** — see D9, which is where the reconstruction and
   its three checks are written up.
3. **The cross-listings are still not held**, as expected: the page is built
   from `data/N.md` and labels itself *hymns under the subject their own page
   prints*, alongside a note that the book also lists them by first line. The
   second table remains an option, not a plan.

**What the page does not do.** No collapsing: 303 headings and 848 numbers make
a long page, but it is one document — the browser's find works on it, it prints,
it needs no JavaScript, and it is in the search index one entry per section, so
a subject can be searched for by name in either language. A hymn's first line is
the link's `title`, so it is there on hover without 848 of them down the page.

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

1. ~~**D5** — transcribe the missing English for 797, 824, 845.~~ Done; it also
   turned up a whole-hymn swap between 797 and 798.
2. **D7 + D1** — ~~audit meters~~ done as a syllable count rather than a page
   read, and ~~the model change~~ made; 93 irregulars filled, 175 hymns still
   disagree and need the page.
3. **§3 preface** — two pages, high value, nearly free. **Next.**
4. ~~**D9 + §4** — widen the category table with levels and printed numbering,
   then generate the subject index page.~~ Done; it also turned up D11.
5. **§6b tunes**, then **6a** — double-sourced, self-verifying.
6. **§5 authors** — biggest, weakest verification, most valuable per hymn. Last
   because everything before it makes the tooling better.
7. **D2/D3/D4/D6** — the small consistency fixes, folded into whichever pass
   is already touching those pages.
