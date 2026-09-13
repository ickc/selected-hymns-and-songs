# Plan

Proposals, not commitments, and the ones that were taken up say so in their
own heading. Each section says what the book actually contains, what `data/`
already has, what is genuinely missing, and what it would cost — so the
decision to build it can be made on evidence rather than on optimism. What is
done keeps its section rather than losing it, because the cost estimate and
what the work actually turned up are the record of whether the estimate was
any good.

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
| `meter` | 848 | 382 name both, 466 print alike | D1 done; every hymn now has one |
| `note` | 37, holding 40 | 22 notes both, 15 Chinese-only, 3 English-only | D4 and D20 done — a list now, and the single-language ones are single-language in the book too; see D16 |
| `ref` | 41 | 36 both, 5 Chinese-only | D3 done; every page that prints one now has it |
| `repeat` | 28 | n/a — one statement about the hymn, not two | D21 done; which lines are sung again where the book says so without writing them out |
| `author` | 704 | 0 both — all English-only | §5 done; 1–764 only, the supplement is not indexed |
| `composer` | 708 | 0 both — all English-only | §5 done; new field, same scope |
| `title` | 778 | 0 both — all English-only | D12 done; 31 scripture portions and 39 Chinese-only hymns have no name in the book |
| `tune` | 764 | n/a — the Chinese edition names no tune | §6b done; 765 pairs, hymns 1–764, one hymn with two |

So: **no, not every field is bilingual.** `category` is, now. `meter` is:
466 hymns print the same notation in both editions and carry one scalar, and
the other 382 name their two halves in the front matter, which is what lets a
page that says `Irregular Meter` sit beside one that counts. But
`author` and `composer` are single-language, five of the 41 `ref`s and eighteen
of the 40 notes are, and 36 hymns have no English lyrics.
`author` and `composer` are single-language because their source is: the index
they come from is the English edition's, and the Chinese edition credits
nobody. The five `ref`s and the eighteen notes are single-language because the
book is — a note about what the *other* edition lacks is printed by one edition
only, which is half of what the fifteen Chinese-only and three English-only
notes say. A hymn can hold one of each: 355's first note is Chinese only,
because only its Chinese page prints one, and its second is in both. And the
36 hymns have no English because the English edition prints none: its own list
of Chinese-only hymns names 39, and D6 is the other three.

### Structure is clean

All 848 files parse, stanza numbering is `1..n` with no gaps or duplicates on
every hymn, and 32 hymns carry more than one chorus (already handled by the
chorus resolution and its report). No structural defects found.

---

## 2. Defects beyond the title and the category

### D1 — 138 hymns had no meter — **done, all 848 now have one**

The English page prints `Irregular Meter` and the Chinese page prints `特`
(`特和` when there is a chorus). 93 English pages contain the word `Irregular`;
`data/` contained it zero times. Hymn 840 was typical: the Chinese page reads
`特`, `data/840.md` had no `meter` at all.

**This one had a model consequence**, now resolved. `_meter_metadata` factored
a localized meter into a shared numeric prefix plus per-language suffixes and
asserted the shared part matched `METER_PREFIX`; `Irregular Meter` and `特`
share nothing. Both halves of the codec now fall back to storing a meter as
plain localized text when there is no shared notation to factor out, which is
what every other localized field already does.

The first 93 were the hymns with no meter where every page reading of either
edition said irregular and none gave a number. 36 of them are `特.和`, the form
the Chinese page prints when the chorus is sung to the same tune — the mark
itself is the hymn having a chorus block, which agrees with the meter on 227 of
the 232 hymns where both were already present.

That left 45 with no meter: 9 with no legible page reading at all, and the rest
where the readings conflicted or gave numbers the lyrics do not scan as. All 45
have now been read off the page and filled — 14 of them hymns ≤764, closed by
[D13](#d13--the-metrical-index-against-both-editions-pages--done-59-meters-settled),
and the other 31 read off the Chinese page one at a time, since only three of
them (797, 824, 845) have an English page and that page prints no meter.

**Every hymn in the collection now carries a meter**, and `pixi run
meter-report` no longer has a "no meter" class. Of the 31 supplement hymns just
filled, 27 scan exactly as the meter read off the page says they should — a
check of the reading that costs nothing, because the meter is a syllable count
and Chinese is one syllable to the character. The four that do not are 766 and
496 (a verse that disagrees with its fellows), 774 and 824 (the joined
half-lines described under D7), 761 (an antiphonal stanza transcribed as one
block — since split, under D7) and 799 (`9.9.9.8.` against lyrics that count
`9.9.9.7.` on both pages) — each a finding about the *text*, now that the meter
is known.

### D2 — `author` is populated on 4 hymns out of 848 — **done, 704 now**

416 Graham Kendrick, 439 Thomas O. Chisholm, 453 Dennis Cleveland, 749 Bob
McGee. All English-only, and all four are copyright-bearing songs — which is
exactly the set the preface says is *not* in the author index ("Author's and
composer's names, except for copyright-bearing songs, are listed numerically in
an index at the rear of the book"). So these four came off the hymn page
itself, and the other ~760 are sitting in an index nobody has read yet. That is
proposal §5.

**§5 read it.** All four turn out to be *in* the index as well, so the preface's
rule is not one the book keeps. Three agree with it letter for letter. The
fourth does not: the index prints hymn 439's author `Thomas D. Chisholm` where
the hymn's own page prints `Thomas O. Chisholm`, and its composer `Carl H.
Lowden` where the page prints `C. Harold Lowden`. That is D15, and D15 settled
it back the way `data/` had it: the index contradicts itself at hymn 397, and
the page's own copyright line repeats the Lowden it credits.

### D3 — `ref` is inconsistent, monolingual, and partly redundant — **done, 41 now, and printed once**

`data/` had eleven references, six English and five Chinese and none both:

```
108 Psalm 45 - Part 1     245 啟一章
109 Psalm 45 - Part 2     246 啟二、三章
110 Psalm 110             247 啟三章
111 Psalm 8               248 啟三章
112 Psalm 68              189 以西結書第47章
749 "Isaiah 7:14"
```

**The pages answered the question the section could not.** Both editions print
the reference in the same place — one line under the meter, above the first
staff — so it is a page annotation, which was the second of the two readings.
The section's other worries mostly dissolved on being looked at:

- **The three Chinese citation styles were ours, not the book's.** The Chinese
  edition is uniform — book name, then 第N章 — and `data/` had been
  abbreviating: `啟示錄第三章` had become `啟三章`, `以西結書第四十七章` had
  become `以西結書第47章` with the chapter in Arabic figures. All five are now
  as printed.
- **749's quotation marks were YAML, not data.** `Isaiah 7:14` contains a
  colon, so the emitter quotes it.
- **The five English references had a Chinese half all along**, and it is not a
  translation of the English one: `詩篇第四十五篇(上)` and `(下)` for *Part 1*
  and *Part 2*, and `詩篇第一百一十篇`, `詩篇第八篇`, `詩篇第六十八篇` for the
  other three. The five Chinese ones have no English half — the English pages
  for 189 and 245–248 print the meter and then the music.

**And thirty more were missing.** *Psalms and Scripture Portions*, hymns
734–764, is thirty-one hymns that each versify one passage, and every one of
their pages prints the citation in both editions. `data/` had it for 749 alone.
That is what made the field look arbitrary: it was not that eleven hymns had a
reference, it was that forty-one did and thirty had lost it.

**Where the verification came from.** These thirty-one are printed twice —
under the meter, and as the subject the book's index files the hymn under — and
`data/categories.tsv` already carries the index's copy from §4. So every page
reading had a second witness. They agree on all thirty-one, down to the
chapter and verse, with two classes of difference in how the citation is set:

- the page writes no space after a comma where the index does, `Psalm
  16:5,8,9,11` against `Psalm 16:5, 8, 9, 11`;
- hymn **764** alone differs in substance-adjacent punctuation: its English page
  prints `Revelation 19:6,7`, while the index and the Chinese page both print
  `19:6-7`.

`ref` carries the page's wording, `category` the index's, which is why the two
now disagree in small ways on those thirty-one hymns.

**One model change came out of it.** A reference is mostly figures, so it hits
the same problem the meter has, and one case hits it fatally: `1 John 1:5-7`
beside `約壹1:5-7` *begins* with a figure, the cut by writing system lands after
the `1`, and the English half comes back without its book number. Three of the
forty-one are numbered books. So a two-language reference now names its halves
the way a meter does; a one-language one stays flat. See
[DEVELOPER.md](DEVELOPER.md#why-the-meter-and-the-reference-name-their-languages).

**Closed since.** On those thirty-one the hymn page printed the citation twice
— once inside the category, once as the reference — and punctuated differently,
`約壹1:5–7` beside `約壹1:5-7`, because the two come from different printings.
That is the book duplicating itself and the projection showing both, and it
read as a stutter.

**The category gave the passage up.** A category is what many hymns share, and
the index's subdivision of *Psalms and Scripture Portions* is one passage to one
hymn — the hymn's `ref` in other clothes. Both pages print only the section
over these hymns, with the passage on a line of its own, so the 31 subjects are
now one: section XVIII is a subject by itself, and `data/categories.tsv` has 255
rows where it had 285. The subject page names the passage beside each hymn
instead, from `ref`, which is where the book's index had it.

The hymn page still shows the passage a second time on these hymns, as the
credit: the author index's *Source* column names the passage as the author, and
`data/authors.tsv` carries that as printed.

### D4 — six `note`s have lost their English half — **done: the English edition prints no note**

470, 584, 611, 659, 705, 720 carry Chinese only (`最後一句唱兩遍`,
`重唱每節最後一行`). All six are ≤ 764, so an English page exists for each, and
this section assumed the English half had been lost. **It had not. All six
English pages were read, and not one of them prints a note.** In every case the
repetition the Chinese note describes is already in the English setting: the
music writes the repeated phrase out under the staff (470, 611, 659, 720), or
the meter line says `with repeat` (584), or both.

Then the same question was put to the other nineteen, whose notes are
bilingual. A sweep of the text layer of all 764 English hymn pages finds
`Repeat the last …` on exactly **three** pages — and those three are hymns
**242, 666 and 678**, which carry no `note` in `data/` at all. So the English
half of every bilingual note in `data/` is on no English page either.

Nor is the Chinese half always on a Chinese page. Four were checked against
the image:

| hymn | Chinese page | what it prints |
| --- | --- | --- |
| 705 | `zh/761` | `（第三至第六節,用第二節和詩）` at the foot — the note, with a comma `data/` dropped |
| 470 | `zh/492` | nothing; the meter line reads `特.重` |
| 584 | `zh/623` | nothing; the meter line reads `6.6.8.6.重` |
| 638 | `zh/680` | nothing; the meter line reads `8.8.8.8.8.8.重` |

So `note` is a mixed inheritance from `data.yml`: some of it transcribes the
Chinese page, some of it is on neither page, and its English is editorial
throughout. **That is why the wording was left alone.** Normalising `Repeat the
last 2 lines` to `Repeat the last two lines` would be imposing consistency on
text whose source is unknown, and the variation may yet turn out to be
somebody's, so it stays until [D16](#d16--neither-editions-page-annotations-are-carried--partly-done)
settles where the field's contents come from. [D20](#d20--the-footnotes-were-two-kinds-of-thing-and-four-were-neither--done-19-inline-notes-classified-7-stay-8-move-4-no-page-prints)
has since made the field a list and given it a check, and cleared all
twenty-five mechanically — no hymn told to repeat its last line already prints
the repeat — but did not re-read their pages. It also added a seventh hymn to
the six above: 355's Chinese page prints a note, its English page prints none,
and the English half `data/` carried there has been removed.

**One fix did come out of it.** Hymn 470's Chinese meter is `特.重` on the page
and was `特` in `data/`; the `重` is the mark that made the note redundant in
the first place. 57 other hymns carried a bare `特` and had not been checked
for a dropped `.重` or `.和`.

**Checked since, and none was dropped.** 58 hymns carry a bare `特`. The nine
with anything that could want a mark — 750's chorus, 242's `repeat`, and the
seven whose lyrics write a repeat out (21, 393, 735, 736, 740, 745, 840) — were
read off their Chinese pages, and all nine print `特` alone. The other 49 have
no chorus and no repeat for a mark to describe. A `重` over a repeat that is
neither written out nor noted, as 54's and 57's were, would still not be seen;
that is the one shape this could have missed. Reading those pages turned up
three notes `data/` did not carry, now under D20, and a second *da capo*, now
under D21.

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

### D6 — three hymns carry English the book does not print — **done, kept and documented**

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

**Kept, and said so** — DEVELOPER.md now has a "What is kept here although the
hymnal does not print it" list beside the list of what was added, and this is
its first entry.

One of the three is not a mystery. **840's English is hymn 720's**, *There were
ninety and nine that safely lay*, which the English edition does print; the two
differ only in where two lines break and in one closing quotation mark. So 840
is a second Chinese translation of a hymn already in the book, and whoever built
`data.yml` carried 720's English across to it. 779's and 789's English appears
nowhere else in the collection and remains unsourced.

Note that D5 and D6 cancelled out numerically — 39 hymns lacked English text in
`data/` and 39 are absent from the English edition — which is exactly why
nobody noticed the two sets were not the same 39. With D5 done the count no
longer matches, and these three are what is left.

### D13 — the metrical index against both editions' pages — **done, 59 meters settled**

Extracting the tunes (§6b) meant extracting the *Metrical Index of Tunes*
whole, and that index files every hymn 1–764 under a meter. Compared against
the meter `data/N.md` carried, **733 of the 764 agreed**. Each of the other 31
was then read off **both** editions' pages — the English one, and the Chinese
one, which nothing in this repository had looked at before.

The Chinese page is the witness that decided it, and it turned three of the
first reading's conclusions around. Its verdict is blunt: **on eleven of the
twelve hymns where the index disagreed with `data/`, the Chinese page agrees
with the index.** `data/`'s meters came from a decade-old OCR of the English
page; the index and the Chinese page are two independent printings, and where
all three can be compared the OCR is what is wrong.

**Twelve `data/` defects, corrected:**

| hymn | was | now | who says so |
|---|---|---|---|
| 6 | `8.6.8.6. with chorus` | `8.8.8.8.` | index, Chinese page, and the hymn itself |
| 264 | `8.8.8.8.D.` | `8.8.8.8.D. (A)` | index and English page |
| 281 | `8.7.8.7.D.` | `8.7.8.7.D. (I)` | index and English page |
| 283 | `6.6.9.6.` | `6.6.8.6.` | all three |
| 325 | `12.8.2.9. with chorus` | `12.8.12.9. with chorus` | index and English page |
| 384 | `9.10.9.10.10.` | `11.11.12.11.` | all three |
| 468 | `6.6.6.6.8.6.` | `8.6.8.6. with chorus` | all three |
| 491 | `13.10.13.14. with chorus` | `13.10.13.4. with chorus` | all three |
| 501 | `7.6.8.6.8.6.7.4.` | `Irregular Meter` | all three |
| 560 | `8.7.8.7.3. with chorus` | `8.7.8.7. with chorus` | all three |
| 700 | `9.9.9.7. with chorus` | `Irregular Meter` | all three |
| 705 | `6.6.8.6. with chorus` | `8.5.8.5. with chorus` | all three |

384 is the shape of the whole class: `9.10.9.10.10.` is hymn **385**'s meter,
printed at the top of the next page. The transcription took the wrong line.

**Hymn 6 is a misprint in the book.** It is the Doxology, *Praise God, from
whom all blessings flow*: one stanza, four lines of eight syllables, no chorus,
set to `Old Hundredth`, which is Long Meter. `scan/en/20.png` prints
`8. 6. 8. 6. with chorus` over it. The metrical index files it under
`8. 8. 8. 8. (Long Meter)`, the Chinese page prints `8.8.8.8.`, and the hymn has
one stanza and no chorus block. Three witnesses against one, and the repository's
rule that the page wins is a rule about transcription, not about which of two
printed statements is true.

**Four where the index is the odd one out**, and `data/` keeps what it had:

| hymn | the two pages | the index |
|---|---|---|
| 278 | `8.8.8.6.` | `8.8.8.6. with Chorus` — but the hymn has five stanzas and no chorus |
| 296 | `6.6.6.6. with chorus` | `6.6.12. with Chorus` — the same 24 syllables, analysed twice |
| 616 | `6.5.6.5.D.` | `6.5.6.5.D. with Chorus` — two stanzas, no chorus |
| 738 | `11.11.7.6.11.` | — |

738 was never a disagreement: the index's heading above it reads
`II. II. 7. 6. It.` in the scan, whose trailing `11.` the parser could not
recognise, so the hymn inherited the heading above that one. Both pages print
`11. 11. 7. 6. 11.` and the index does too. (Hymn 391 is the one hymn 1–764 the
metrical index extraction never files at all; its `7.7.7.7.7.7.` is confirmed by
the Chinese page.)

**Fourteen hymns ≤764 had no meter, and now every one does.** Ten print
`Irregular Meter` on the English page (363, 370, 457, 462, 464, 495, 669, 737,
750) or `8. 8. 8. 8.` (749). The other four — 194, 241, 480, 761 — print no meter
at all on the English page, only *This hymn may be sung to the tune of hymn
#467* (or #491) and *Not printed here due to copyright*. **Their Chinese pages
print a meter**, which is what closed them; the index files them under the
borrowed tune's heading, and for 761 that heading, `13. 10. 13. 4. with Chorus`,
is character for character what the Chinese page prints.

After this **759 of the 764 agree with the metrical index**, and the five that
do not are the four above plus 391, all understood. That is what §6a was waiting
for, and §6a is now built.

**The field now holds both editions, and eighteen hymns needed it to.** A
localized meter used to be flattened into one front-matter scalar and cut apart
again by writing system, which a meter is the one field that cannot survive:
its figures belong to no script. It is written as a mapping now — see
[DEVELOPER.md](DEVELOPER.md#why-the-meter-names-its-languages-and-nothing-else-does)
— and two things follow.

`(A)` and `(I)`, anapestic and iambic, are the English edition's alone: the
Chinese pages of 264, 281, 493, 496 and 598 print the figures without them.
Those five now say so.

And **the English edition files 111 hymns as `Irregular Meter` where, on
eighteen of them, the Chinese page prints an actual count.** Both editions'
pages were read for all 111, and the eighteen are 64, 175, 194, 241, 274, 363,
370, 457, 462, 464, 480, 495, 564, 669, 680, 720, 727 and 737. A count is a
better statement than a refusal to count, so it is now what both halves carry,
translated by the table the hymnal itself uses — 雙 is `D.`, 和 a chorus, 重 a
repeat. Hymn 175's English page prints no meter at all; hymn 64's prints
`Irregular Meter` over lyrics that count 9.10.11.10 in every verse.

Fifteen of the eighteen scan exactly as the Chinese page says. The three that
do not — 194, 274 and 564 — are the joined half-lines described under D7: 564's
verse is stored as eight lines of 6.5 where the page counts four of 11, and
274's first verse turned out to have two lines in other words than the page's
as well. So the
change also puts three more hymns in front of the one check that can find them.

The cost is that these eighteen no longer agree with the metrical index, which
files them under `Irregular Meters` by construction: 741 of the 764 agree now
rather than 759. That is the index being less specific than the page, not the
two disagreeing.

### D7 — the meter against the lyrics — **done: 139 disagreements down to 63, and the 63 are the hymnal's own**

*(64 since [D20](#d20--the-footnotes-were-two-kinds-of-thing-and-four-were-neither--done-19-inline-notes-classified-7-stay-8-move-4-no-page-prints) wrote out the line 393's eighth stanza prints twice.)*

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
  stands. Hymn 453 is the same thing carried one step further: the English page
  and the index both print `6. 6. 11. 6. 6. 10.` and the Chinese page prints
  `6.6.11.雙`, because the Chinese last line has the syllable the English one
  does not. Neither is an error, and `data/` now carries **both** — see *The
  two editions state two meters* below, which is where this finally landed.
- **Some Chinese verses were transcribed with two printed lines joined into
  one.** Hymn 69's page reads `6.6.6.5.雙.和` and prints eight half-lines two to
  a row; `data/` has four lines of 12.11.12.11 and a meter to match. Hymn 824,
  re-lineated in D5, was the same thing, and 774 (`7.6.7.6.D.` against lyrics
  that count `13.13.13.13.`) is another. This is a lineation question rather
  than a meter one, and the meter is how to find the rest of them.
- **`data/777.md`'s meter was `.8.6.8.6.6.6.7.5.`**, with a leading dot that was
  simply a typo. Its page prints `8.6.8.6.6.6.7.5. 和`; fixed, along with 772,
  whose page prints `8.8.8.8.7.` and which `data/` had as `8.8.8.8.8.`.

**Nothing goes unchecked.** The 93 hymns the hymnal calls irregular used to be
skipped, because `Irregular Meter` names no lengths to count against; their
verses are now counted against *each other*. And every chorus a hymn prints is
sung to the same strain, so the choruses of one hymn have to scan alike — one
hymn's do not, 480, and reading its page to find out whose the odd syllable was
turned up D14. `pixi run meter-report --shape` prints the counts.

**D13 changed what these are evidence of.** 108 of them are hymns ≤764, and
**89 of those carry a meter the book's own metrical index independently
confirms**; of the rest, 18 are the hymns whose count comes from the Chinese
page against an index that only says `Irregular Meters`, and one is 616, where
the index adds a chorus the two pages and the hymn itself deny. On the 89 the
meter is right twice over, so the disagreement is a finding about the
**lyrics** — a dropped character, or a lineation the transcription joined — not
about the meter.

#### The check was asking one question where there are two

139 hymns disagreed, and the report called all 139 the same thing. They are
not. A verse and a meter are two readings of one run of syllables, and they can
differ in two ways that want quite different work:

- they can hold **different syllables**, which is a finding about the text and
  the only kind a page can settle in our favour;
- or they can hold the same syllables and **cut them in different places**,
  which is often no finding at all.

The second is common because a meter names the lines of the *tune* and a page
prints the lines of the *stanza*, and where the tune's lines are short the page
prints two of them to a row. **The hymnal does this both ways.** 617's page
states `7.6.7.6.雙` over rows of thirteen characters; 137's states
`13.13.13.13.` over exactly the same shape. Neither is wrong, and `data/`
follows the row on some hymns (847, 617) and the sung line on others (685) —
which is itself only visible because the meter disagrees.

So a verse is now compared on its **total** first and its **line breaks**
second, and the report names five kinds:

| kind | what it means | hymns |
|---|---|---|
| syllables are missing or added | the totals differ — the text finding | 54 |
| one verse, one syllable out | the classic dropped character | 1 |
| the meter counts a break the lines do not print | the page prints two of the tune's lines to a row | 29 |
| the lines print a break the meter does not count | the reverse | 12 |
| a line break is in a different place | the whole verse is there, cut where it cannot be sung | 6 |

**Three kinds of false positive went with it.** A stanza the Chinese edition
does not have is not a verse that lost its syllables — 789, 813 and 840 print
more English stanzas than Chinese ones, and 840's English page says so. A
meter ending in `重` asks for the last line, or the last phrase, to be sung
twice and states the lengths once, so the ten hymns that write the repeat out
came out longer than their own meter. And a Pandoc inline note is the hymnal's
direction printed beside the verse, not words sung in it: twelve hymns carry
one, and eleven of those verses were among the longest disagreements the report
had. Where a doubled meter is only satisfied by a verse and its chorus and
every verse holds exactly half, the report now prints the two together, because
what does not scan is the one chorus and not the six verses.

#### What that left, and what it settled

**Nineteen misplaced line breaks, fixed without adding or taking away a
character.** A verse breaking differently from its own siblings *and* from the
meter is fixed by both of them at once: the whole verse is present, and the
lengths every other verse agrees on say where its lines end. The pages confirm
it wherever the odd verse is printed as text rather than sung under the music —
711's second and third and 673's fifth print exactly the break the count
predicts, and 673's page also has the comma the old break had swallowed. The
nineteen are 43, 107, 109, 229, 243, 323, 459, 469, 498, 599, 618, 624, 650,
673, 685, 706, 709, 711 and 723.

**Nine characters the transcription had dropped**, each confirmed on the
Chinese page:

| hymn | verse | the page prints | what `data/` had |
|---|---|---|---|
| 122 | 2 | 以色列**民**被選族類 | 以色列被選族類 |
| 270 | 4 | 隨同**所有**歡樂聖眾讚美 | 隨同歡樂聖眾讚美 |
| 298 | 2 | 寶血**爲**我擔過、祂血曾**爲**我們流過 | both 爲 gone |
| 632 | 4 | 勝利終必**要**得到 | 勝利終必得到 |
| 685 | 3 | 原本藏在天**上**父的心懷 | 原本藏在天父的心懷 |
| 755 | 1 | 這些東西**就**都要加給你們 | 這些東西都要加給你們 |
| 834 | 4 | 纔使撒冷對我**能**成爲盼望 | 纔使撒冷對我成爲盼望 |

122's is confirmed twice over: its twin 123 prints the same line under the
other tune and has always had the 民.

**And four lines that were not the page's at all**, found by eye while reading
a page the count had sent us to — the same way D14 was found, and invisible to
any count because each is the same length as what it replaces:

| hymn | verse | the page prints | what `data/` had |
|---|---|---|---|
| 599 | 2 | 賜我裝備，抵擋仇敵 | 賜我裝備，戰勝敵軍 |
| 599 | 2 | 向祂，我投倚 | 祂有信心 |
| 632 | 3 | 用十架對付“己，” | 應用十架在“己，／”單靠… |
| 813 | 3 | 處處**跟主**走窄路 | 處處行走窄路 |

813's was the chorus's line standing in the verse's place; its second verse
does the same thing with 時時 and its fourth with 一直.

#### The two editions state two meters, and `data/` was holding one twice

The 48 were one mistake made 48 times. A localized meter holds two statements,
and the transcription had made them one: **every one of the 382 localized
meters carried the English figures on both sides**, with only the qualifier
translated — `13.13.13.14. with chorus` beside `13.13.13.14. 和` where the
Chinese page prints `8.5.8.5.雙.和`. The collapse also swapped the Chinese
edition's own marks for the English ones: no Chinese page in the book writes
`D.`, it writes `雙`, and 50 zh halves had a `D.` no page prints.

So the check now reads the **Chinese** half — it counts Chinese lyrics, and
only the Chinese page's meter describes them — and `printed()` understands
`雙` as it understands `D.`. **43 hymns were given the meter their Chinese page
prints**, read off `scan/zh/` in nine strips of five:

| what the Chinese page says | hymns |
|---|---|
| different figures altogether | 3, 45, 49, 54, 75, 115, 145, 166, 174, 199, 279, 304, 332, 334, 388, 389, 450, 453, 553, 555, 592, 594, 601, 616, 779, 784, 790, 795, 802, 809, 815, 820, 823, 841 |
| the same figures plus a `重` the English does not have | 16, 20, 86, 239, 433, 732 |
| one more line than the English counts | 10 |
| `特` where the English states figures | 116 |
| the verse and its chorus counted as one run | 399 |

Some of these are the same shape stated two ways — 453's `6.6.11.雙` against
`6. 6. 11. 6. 6. 10.`, 616's `6.5.6.5.6.5.雙` against `6.5.6.5.D.` — and some
are a different reading of the tune: 45's `8.5.8.5.雙.和` cuts into halves what
the English counts as `13. 13. 13. 14.`. Either way the Chinese figures are the
ones the Chinese lyrics answer to, and the report went from 102 hymns to 65.

**274 also had the collapse the other way round**: `data/` gave its English
half `6.6.6.6.6.D. with repeat`, the Chinese page's figures in English dress,
where `en/301` prints `Irregular Meter`.

#### Four more findings in the text, and one in the counting

- **722's third verse was missing two whole lines** — `若沒有救主，雖暫能活着，`
  and `但到要死時，將要怎辦？`, both on `zh/780` — and four of its remaining
  lines were broken in half. Nineteen syllables restored.
- **274's first verse had two lines in other words than the page's**:
  `並改進人才幹，` for `“他連得，”再去賺；` and `藉盼望的忍耐和愛心的勤勉，`
  for `因盼望，而忍耐；在愛中，樂勤勉，`. Same lengths, so no count could ever
  have caught them — the third instance of the D14 pattern. It also carried a
  direction, `(Repeat the last line of each stanza)` / `（每節重唱最後一行）`,
  that **neither page prints**: both write the repeat out instead, the English
  under every verse and the Chinese under the music, so `data/` now does too.
- **532, 533 and 761 had their choruses running on inside the verse.** All
  three are sung to 491's tune, and 491 was already right: the page sets the
  chorus apart under a `（和）`, and the responsive `（姊妹）/（弟兄）/（全體）`
  lines belong to it. Split out, all three verses count `13.10.13.4.` exactly,
  which is what both pages say.
- **533's third chorus was in the wrong order and two words out**: the
  `（全體）` line belongs third, not fifth, and reads `神聖性質從我們顯出；`
  where `data/` had `神聖性質從人身上顯出；`. `en/576` settles the order — it
  prints the chorus as two five-line blocks, `Everyone:` last in each — and
  supplied the English line `data/` had lost with it.
- **The speaker of a responsive line is not sung.** `（姊妹）` is two Han
  characters and was being counted as two syllables in all four hymns that use
  the form. Stripped, like a Pandoc note.
- **A repeat lets each verse choose.** `重` offers several runs of lengths, and
  the check used to demand that every verse of a hymn take the same one. 274's
  page writes its repeat out under the music and leaves it to the singer in the
  verses printed as text, and is right both times.

#### What is left, and why it will stay

63 hymns are still reported — 64 since D20:

| | hymns | what settles it |
|---|---|---|
| the lines are not the meter's lines | 56 | a lineation question; every syllable is present |
| every verse agrees and all differ from the meter | 4 | 48, 112, 329, 799 — the translation sits differently on the tune |
| the verses genuinely differ from each other | 2 | 476 and 477 |
| a line the meter does not count | 1 | 805 |
| a stanza the book gives one line more | 1 | 393's eighth, printed with its last line twice on both pages; see D20 |

**The four are the limit of what a syllable count can decide.** 329's two pages
*both* print `9.7.10.7.和` over lyrics that count 9.7.9.7 in all three verses;
112's print `8.7.8.7.7.7.8.7.` over seven verses that end `阿利路亞，阿們！`,
six syllables, which is simply what the words are (`zh/117` confirms it); 799
and 48 are the same. A meter is a statement about the *tune*, and a translation
may sit a syllable differently on it without anything being wrong.

**476 and 477 are the score, not the text.** Both print
*1. First Vs. Ends Here – Repeat 2nd Verse Only* over a first and second
ending, so their two verses are different lengths by design and the check's one
remaining assumption — that an irregular hymn's verses agree with each other —
fails honestly. Nothing in `data/` records a first ending; if it ever should,
this is the hymn pair that would want it.

**533 now joins 480 in the chorus check**, because its third chorus really does
count 6.8.**9**.6.8.7 where its first two count 6.8.**10**.6.8.7 — the page's
own arithmetic, read at four hundred percent to be sure of it.

### D14 — half of hymn 480's Chinese was not the text on its page — **fixed**

480 is the one hymn the chorus check reports: its first chorus counts
`10.15.10.14` where its other two count `10.14.10.14`. Reading the Chinese page
(`zh/506`) to see whether that syllable was ours or the book's answered a
larger question — **twelve of the hymn's twenty-four Chinese lines were not
what the page prints.**

| stanza/line | `data/` had | the page prints |
|---|---|---|
| 1 L2 | 藉此祂作我主人，並且**內住於我** | 藉此祂作我主人，並且**內住我心** |
| 1 L4 | 故祂這榮耀**主人，取代了我** | 故祂這榮耀**的人，安家我心** |
| 1-chorus L2 | 我接受**你作我主人，作我的完全真體** | 我接受**你，以你為主，從我活出你自己** |
| 2 L2 | 作為那說話的靈，**祂不停地說話** | 作為那說話的靈，**祂今說話不停** |
| 2 L3 | **祂的說話如水在裡面將我沖刷** | **祂說話如水將我裡面洗滌無瑕** |
| 2 L4 | 清除我所有老舊，**並分賜祂** | 清除我所有老舊，**並來更新** |
| 2-chorus L1 | 哦主，哦主，**儘量**向我說話 | 哦主，哦主，**求你**向我說話 |
| 2-chorus L3 | 哦主，哦主，**說、洗我的各部** | 哦主，哦主，**說話洗我各部** |
| 2-chorus L4 | **藉新陳代謝的變化**，安家在我心裡 | **藉這新陳代謝變化**，安家在我心裡 |
| 3 L2 | **藉從我們裡面將教會榮耀發表** | **從我們裡面出來使教會得榮耀** |
| 3-chorus L1 | 哦主，哦主，**借著你的經營** | 哦主，哦主，**藉著你的運行** |
| 3-chorus L2 | 將你榮耀**徹底滿溢**、浸透我們全人 | 將你榮耀**滿溢我們**、浸透我們全人 |

**Every pair has the same syllable count**, which is why nothing else in the
collection could have found this. The meter is a checksum, and all twelve lines
pass it both ways.

The temptation was to read the divergence as a *different printing* rather than
a defect: `data/480.md`'s English matches `en/516.txt` word for word, and its
Chinese tracks that English more closely than the page's Chinese does — 經營 is
"economy", where the page's 運行 is not. But this repository's rule is that the
page wins, and the page is the only Chinese witness there is. The twelve lines
are now the page's, in the collection's own orthography: `data/` writes 你 and
著 on all 848 hymns and 祢 and 着 on none, so the page's 祢 and 着 are left as
the typographic variants they are, and only the wording changed.

**The odd syllable was the book's after all.** The page prints fifteen in the
first chorus's second line (我接受你，以你為主，從我活出你自己) and fourteen in
the other two, so 480 is still the one hymn `meter-report` reports for its
choruses — but the three verses now scan `13.13.13.11` against the
`13.13.13.11. 和` its page prints, which they did before only by coincidence.

Whether other hymns have drifted the same way is **not known**, and cannot be
settled cheaply: the Chinese PDF's text layer is too noisy for automated line
matching — the median hymn matches it 91.9% character for character even where
the text is surely identical, 778 of the 848 have at least one line the matcher
cannot pair, and 480 ranks 311th of 847 on line similarity, squarely mid-pack.
Finding others means reading pages by eye. This is the one defect class in the
collection with no cheap detector.

### D15 — the author index disagrees with the hymn pages on 17 hymns — **done: the fuller printing wins, and three rows say why**

**A second source turned up after §5 was called sourceless.** The English
preface says author and composer names are in the index at the back "except for
copyright-bearing songs" — and it is exactly those songs that carry the names
*over the hymn instead*, above the first staff. That is a second printing of
the same fact. It does not cover the collection: reading the top of all 605
hymns that begin their own page finds a credit for only 71 cells, most pages
printing neither. But those 71 are a real check, and 21 agree outright.

**The page does not have the index's shape, and that is the whole defect.**
Reading the eleven page images the two printings disagree on finds three
layouts, not one:

| layout | left margin | right margin | hymns |
| --- | --- | --- | --- |
| split | the author | the composer | 144, 286, 363, 378, 430, 439, 492 |
| joint | *empty* | the whole credit | 11, 54, 118, 128, 216, 234, 266 |
| joint, stacked | *empty* | two names, one per line | 219, 505 |

The right margin means the composer on a split page and the whole credit on a
joint one. **Position alone does not say which**, and the index — having two
columns to fill — resolves a joint credit by writing it into both. 110 of the
764 rows carry the same name twice, and every joint-credit page above is one of
them. `data/authors.tsv` keeps that convention: it is the book's own, and the
alternative is a third representation for a hundred hymns to serve fifteen.

**Which is also how the first reading of these pages went wrong.** The column
this defect was first recorded from came from a coordinate heuristic over the
text extraction — it takes the bottom line on each margin, having removed the
subject heading, the meter and the number — and that is right for a split page
and silently halves a stacked one. It reported `Tommy Coomes` for 219 and lost
`Morris Chapman`; `Randy Rigby` for 505 and lost `Danny Daniels`; and on 144 it
read `Jennie Hussey` off a page that plainly prints `Jennie E. Hussey`. Three
of the seventeen rows were artefacts of the reader. **A coordinate heuristic
over a text layer finds candidates; only a page settles them.**

**Settled by taking whichever printing carries more.** Ten rows keep the
index's name:

| hymn | the index — kept | the hymn's own page |
| --- | --- | --- |
| 144 | `Jennie E. Hussey` | `Jennie E. Hussey` — not a disagreement at all |
| 216 | `Graham Kendrick and Chris Rolinson` | `Graham Kendrick` |
| 286 | `Alfred H. Ackley`, `Bentley D. Ackley` | `A. H. Ackley`, `B. D. Ackley` |
| 363 | `George O. Webster`, `Charles H. Gabriel` | `Geo. O. Webster`, `Chas. H. Gabriel` |
| 430 author | `A. B. Simpson` | `A. Simpson` |
| 492 | `John W. Peterson, Alfred B. Smith` | `Alfred B. Smith` |
| 571 | `Jean Sibelius, arr. for The Hymnal` | `Jean Sibelius` |

and seven take the page's, for the same reason:

| hymn | the index | the hymn's own page — kept |
| --- | --- | --- |
| 11 | `F. M. Lehman` | `Frederick M. Lehman` |
| 54 | `Nalda Hearn` | `Naida Hearn` — the index's `Nalda` is a misprint |
| 118 | `Unknown`, `Dave Fellingham` | `David Fellingham`, joint — a name beats *Unknown* |
| 128 | `Jack Hayford` | `Jack W. Hayford` |
| 219 | `Morris Chapman and Tom Coomes` | `Morris Chapman and Tommy Coomes` |
| 234 | `Debby Kerner` | `Debby Kerner Rettino` |
| 505 | `Danny Daniels` | `Danny Daniels and Randy Rigby` |

**439 was the one that cost something, and the page wins both cells.** `data/`
had `Thomas O. Chisholm` from the hymn's own page — one of D2's four — and
applying the table had replaced it with the index's `Thomas D. Chisholm`. The
same index prints `Thomas O. Chisholm` at hymn 397, so it contradicts itself as
well as the page; and the page's own copyright line repeats the `C. Harold
Lowden` it credits, where the index prints `Carl H.`. A printing that
corroborates itself beats one that contradicts itself.

**On three the two name different people, and there the table says so.** A
fourth column carries a note, which reaches the hymn as `credit-note` — beside
the credit and not inside it, so the front matter still answers *who wrote
this* in the field that question is asked of:

| hymn | the page | the index | `data/` |
| --- | --- | --- | --- |
| 266 | `Dale Garratt` | `Michael Ryan` | both, page first |
| 430 composer | `George Stebbins` | `I. H. Meredith` | both, page first |
| 378 composer | `W. H. Hammontree` | `Homer Hammontree` | the index's, as the fuller name |

Combining asserts a co-authorship that is probably false — one printing is
simply wrong, and nothing in the book says which — so the note is what makes
the row honest rather than a decoration on it. It is shown on the hymn page and
on the deck's title slide, italic in both, being the only line in either
heading the hymnal does not print. It is also the first cell in `data/` that is
not read off a page, which is why it is confined to three rows: everything else
here is one person written two ways, and this table is the record of that.

**What is still a floor, and how deep.** Every row the heuristic *did* report
has now been read off `scan/en/`, except 571, where the index is a strict
superset either way. What it never looked at is larger than what it did:

| never compared | hymns | why |
| --- | --- | --- |
| begin below another hymn | 159 of 1–764 | the reader looked above the first staff of a page, which is not where a mid-page hymn's credit sits |
| the supplement | 45 present in English | the index stops at 764, so there is nothing to compare against — and `data/` therefore credits none of them |
| cells it discarded | ~30 | scan speckle (`r--,`, `13\o/`) or the wrong line (`chorus`, `First tune.`), dropped rather than reported as unknown |

**The first of those was sampled, and it is not empty.** Of the 159 shared-page
hymns, the 20 whose index row is a joint credit — the signature of a modern
copyrighted song, which is the kind of page that prints one — were read by eye.
Ten print a credit and ten print none. Of the ten, seven agree and **three
disagree**:

| hymn | the page | the index | settled |
| --- | --- | --- | --- |
| 19 | `Jimmy & Carol Owens` | `Jimmy Owens` | the page — the index dropped a person |
| 64 | `Tommy Coomes` | `Tom Coomes` | the page — as at 219 |
| 329 | `Elton Roth` | `Elton M. Roth` | the index, already there |

19 and 64 are corrected. The rate — three disagreements in ten pages that print
anything — is about what the original comparison found, which says the
unexamined 139 are unexamined rather than clean. They are enriched for older
public-domain hymns, whose pages print nothing, so the yield there will be
lower; it will not be zero. **Closing this means reading page tops by eye, and
the count is 159 plus the supplement's 45, not the 605 already done.**


### D16 — neither edition's page annotations are carried — **partly done**

D3 and D4 both ran into the same thing from different sides. Besides the
subject, the meter, the number and the scripture reference, a page can carry a
short parenthetical line — how to sing it, which tune to borrow, what a word
means, how the other edition's text differs. `data/` carried 25 of these as
`note` when this was written (37 on 34 hymns since D20), and D4 showed that set is neither complete nor sourced. **Both editions
print a great many more, and the two editions' sets are different.**

A sweep of the text layer of all 848 pages of each edition finds, at minimum:

**English** — about twenty, in Times-Italic under the last staff or beside the
meter, in four families:

- *"This hymn may be sung to the tune of hymn #467"* — ten pages, plus
  *"Alternate: Tune of hymn #624 without chorus"* and one that names a tune
  rather than a number, *"Pass It On"*;
- *"(Repeat the last two lines of each stanza)"* on three pages — hymns 242,
  666 and 678, none of which has a `note` in `data/`;
- *"(Do not repeat chorus)"*, and *"(Do not repeat chorus after the last
  verse.)"*;
- glosses: *"Meaning, married (Isa. 62:4)"*, *"(“Truth” in the first stanza
  refers to Christ)"*, and seven of *"(The Chinese version has 5 stanzas)"* in
  the supplement.

**Chinese** — about thirty, in fullwidth parentheses, and mostly *not* the same
hymns:

- 調用第四百九十一首 — borrow another hymn's tune — on seven pages;
- 第四節末兩行重唱一遍, 回頭再唱正歌一遍, 第二節不唱和歌, and the long one on
  `zh/152`, 唱第二調時第二至六節，每節首行末句重唱一遍，次行末句重唱兩遍;
- 英詩無第二節 and 英詩僅有一、二、五等三節 — the mirror of the English
  edition's *"The Chinese version has 5 stanzas"*, and pointing the other way;
- glosses and provenance: 蓋恩夫人獄中之詩 (Madame Guyon's prison poem),
  第四節「靉靉」意思是雲層籠罩的樣子, 基督，可唱作耶穌, 第二節的明亮晨星指基督.

(Those are PDF page numbers, not hymn numbers; the sweep did not resolve them
to hymns.)

**Why this is worth doing, and why it is not small.** Three of the four families
are checkable against something `data/` already holds — a stanza count, a tune
name, a chorus rule — so they are verification, not just decoration; the
*"Chinese version has N stanzas"* lines in particular are a printed statement
about exactly the thing D5 and D6 were about. But it is a two-edition
transcription of about fifty short lines in two scripts, positioned all over
the page rather than in one slot, which is why the text layer can only give a
lower bound. Realistically it is a §-sized piece of work like §5 or §6, and it
should decide at the same time what the existing `note`s are and where they
came from.

**[D20](#d20--the-footnotes-were-two-kinds-of-thing-and-four-were-neither--done-19-inline-notes-classified-7-stay-8-move-4-no-page-prints)
did the first slice**, and settled the shape the rest can be poured into:
`note` is a list of the book's own directions, a gloss stays in the lyric line
where the page anchors it, and `pixi run check-notes` reads both back against
the hymn. Eight of the annotations listed above are now carried — 129, 242,
394, 460, 717, 757, 769 and 813 — every one of them read off the image rather
than off a text layer, and every gloss already in `data/` was corrected against
its page. What is left of this section is the tune-borrowing family (about ten
English pages, about seven Chinese ones), the provenance notes, `zh/152`'s long
instruction, and the copyright lines; and the nineteen bilingual notes
inherited from `data.yml`, whose English wording is still unsourced.

### D17 — `data/` was in a different orthography from the book — **done bar `你`/`祢`**

**How it surfaced.** §8 item 10 noticed that both Chinese indexes call V.6
神的醫治 while `data/` called it 醫病, and first recorded it as an
index-against-page disagreement of D15's kind. It was not one. Hymns 279 and
280 print 神的醫治 over themselves — `scan/zh/296.png`, `scan/zh/297.png` — so
all four printed witnesses agreed and 醫病 was printed nowhere. It came from
`../selected-hymns/data.yml`.

That was the whole defect in miniature. The English half of every category was
read off the English subject index in §4; **the Chinese half never was, and
neither were the lyrics.** Both were carried from the publisher's YAML on the
assumption — written into `categories.py` — that `data/N.md` is the authority
on what the Chinese page says. The YAML is cleaned OCR, so it is a reading like
any other, and tested against the pages it did not hold.

**What the book prints.** Seven characters, each verified on a page image
rather than on the extraction's text layer, which is wrong about several of
them:

| `data/` had | the book prints | verified at |
| --- | --- | --- |
| 著 | 着 | 570 (因着主的照顧), 12 (白白得着) |
| 裡 | 裏 | 455 (在祂的愛裏) |
| 為 | 爲 | 214 (爲全地禱告), 14 (甘爲我擔罪) |
| 借著 | 藉着 | 446 (藉着祢的救贖) |
| 真 | 眞 | 11 (我眞愛祢) |
| 教 | 敎 | 32 (指敎我們) |
| 啟 | 啓 | 28 (啓示我的救贖主) |

The text layer had to be checked rather than believed. It reads 爲 as 為 more
often than not, and 裏 as 裹 in four cases out of five, so its own counts would
have argued for leaving `為` alone.

**Two exceptions, and they are the point.** A blanket substitution would have
been wrong twice, and both were caught by looking:

- Hymn 458 prints 比晨星更**著** — *zhù*, conspicuous, not the particle. It is
  the one 著 left in `data/`.
- Hymn 556's 何必先**借**明天憂 is *borrow*. The other 24 借 are 借著 for the
  book's 藉着, and only those were changed.

**What was done.** 704 hymn files and `data/categories.tsv`, together, since
the table is keyed by the Chinese string. Hymns 279 and 280 are 神的醫治. The
round trip through YAML is still byte-exact, all four `check-` tasks pass, and
the build is unchanged at 848 decks and pages. `data/preface.zh.markdown` was
**not** touched: the Chinese preface is a modern publisher's note set in modern
forms, and its page prints 為, so it is right as it stands.

**What is left: `你` for `祢`.** The book distinguishes 你 from 祢, the
reverential second person, and reserves 祢 for God. `data/` has 你 4,547 times
in 557 files and 祢 not once, and the page images show 祢 wherever the text
layer reads 妳 — hymn 55's 神在**祢**身顯着 among them. This is the only one of
the eight that is not a glyph substitution: it turns on who is being addressed,
line by line. The layer settles it per hymn only where it finds no plain 你 and
its count matches ours exactly, which is **100 of the 557**; 253 more have only
祢 but a count that disagrees, and 204 have both. So it needs a reading pass,
and it is the largest single correction left in `data/`.

**Still unchecked: the rest of the Chinese text.** Comparing every hymn's
category against its page heading found six subjects where the two named
different things, not different glyphs — 70, 162, 415, 618, 807 and 279/280,
of which the subject index confirms 162 (祂作我們的平安祭) and 618 (奮勇前進).
Those are not corrected here: a different subject moves a hymn in the tree, and
that is D8's and §4's business rather than an orthographic sweep's. And the
comparison itself reached only 327 of 848 pages, because the other 521 put
something other than the heading on the first line the reader recovered.

### D18 — a variant dictionary, and where normalising is allowed to win — **done: the search folds, and the data does not**

D17 corrected `data/` **towards** the book: 着 not 著, 裏 not 裡, 爲 not 為, 藉
not 借, 眞 not 真, 敎 not 教, 啓 not 啟. That is the right default and it should
stay. But it is not the whole answer, because two questions are left over that
a table of variant pairs would settle, and neither is answered by "the page
wins".

**The stake, which is that the category is an identifier and the lyrics are
not.** Everything else `data/` holds is a quotation: a lyric, a meter, a
scripture reference are only ever displayed, so the page's spelling is simply
the right one. The category is the exception — it is a **key**.
`categories.read_mapping` builds the Chinese-to-English correspondence keyed by
the Chinese string and refuses a string that appears twice;
`subjects._filed` groups the index page by that same string and refuses a hymn
whose category is not in the table. So two spellings of one subject are two
subjects: the tree splits, the English half cannot be found, and the build
stops. **Consistency has to beat the literal page there, and only there.**

That is already how one row works, and it should be written down as a rule
rather than an exception. Hymn 822's page prints 因着祂足**彀**的恩典 —
confirmed on `scan/zh/884.png`, not an extraction artefact — while the other
four hymns under that subject print 足**夠**. `data/` carries 足夠 for all
five, because a reader searching one spelling should not be shown four of the
five. The book is inconsistent with itself there, and we follow its dominant
form. The same character is left alone where it is a quotation: 814 and 817
keep 彀 in their lyrics, as printed.

**The inconsistency was worse before D17, and its shape says where it came
from.** `data/categories.tsv` used to spell one word two ways, and the split
fell along section boundaries:

| the same phrase | one section | another |
| --- | --- | --- |
| 在信心裏 / 在信心裡 | 禱告 | 屬靈的爭戰 |
| 在主的名裏 / 在主的名裡 | 禱告 | 屬靈的爭戰 |
| 住我裏面 / 住在祂裡面 | 聖靈 | 經歷主 |
| 在祂裏面喜樂 / 在主裡喜樂 | 讚美和敬拜 | 安慰與鼓勵 |

Seven subjects used 裏 and thirteen used 裡, and 禱告, 聖靈, 救恩的喜樂 and
尋求主 took one form while 經歷主, 屬靈的爭戰, 榮耀的盼望 and 安慰與鼓勵 took
the other. That is what a text assembled section by section from several
sources looks like. None of the four pairs actually collided, because each pair
sits under a different parent — but they are one phrase printed two ways, and
nothing but luck kept them from being one key printed two ways.

**The second question: a modern-form reading of the whole text — settled, in
`site/search-fold.html`.** The book's orthography is `data/`'s, which is right
for fidelity and awkward for a reader: **2,698 of the 6,906 search entries**
carry at least one of these characters, and none of them is what a modern IME
produces. Someone typing 裡面 or 教會 was told the hymnal did not contain them.

The folding belongs in **both** the index and the query, and that turned out to
be the answer rather than a compromise. Quarto's search is fuse.js over
`search.json`, and both ends of it pass through one object — `Fuse.prototype.add`
takes each indexed document and `Fuse.prototype.search` takes each query — so a
single include patches the pair and folds both into the form `data/` carries.
Folding the query alone would have been cheaper and would have broken the
eleven places the site *does* print the other form: the Chinese preface's 為,
hymn 458's 更顯著, and 814 and 817's 彀. Folded on both sides, each of those is
now found by either spelling.

Nothing stored moves. `data/` and every rendered page keep the book's spelling;
the only visible effect beyond finding more is that a result's snippet shows
the folded form, in **19 characters across 12 of the 6,906 entries**.

**And the fold is allowed to be more lenient than `data/` is**, which is the
part worth stating as a rule. A search result is an offer of candidates, not an
assertion about the page, so the include carries a *second* table: 你, 妳, 祢
and 袮, the four ways the hymnal writes *nǐ*, folded to the undifferentiated 你.
`data/` may not do that — which of them a line takes is a reading of who is
addressed, and hymn 109's Psalm 45 daughter and hymn 105's Church are correctly
妳 — but nobody recalls a line by its pronoun, and all four are one word said to
a different hearer. Keeping it out of the search because the *data* question is
unsettled was the wrong inference, and the two tables now say so: `VARIANTS` is
checked against `data/` by `tests/test_search_fold.py`, `PRONOUNS` is checked
only for its shape, because no count in `data/` can confirm or refute a claim
about what a reader remembers.

A modern-spelling *edition* remains possible and remains unwanted; what the
fold does is make one unnecessary for the reader who only wants to find a line.

**What the dictionary would hold.** Seven pairs are settled, each read off a
page image rather than off the extraction's text layer, which is wrong about
several of them:

| the book | the modern form | verified at |
| --- | --- | --- |
| 着 | 著 | 570, 12 |
| 裏 | 裡 | 455 |
| 爲 | 為 | 214, 14 |
| 藉 | 借 | 446 |
| 眞 | 真 | 11 |
| 敎 | 教 | 32 |
| 啓 | 啟 | 28 |
| 祢 | 你 | 55, 446 |
| 夠 | 彀 | 822 (the book's own minority form) |

**And two entries that prove the dictionary cannot be a plain substitution
table.** Both were caught only by looking at the page:

- Hymn 458 prints 比晨星更**著** — *zhù*, conspicuous — not the particle. Fold
  it and the line changes meaning.
- Hymn 556's 何必先**借**明天憂 is *borrow*, not 藉. The other twenty-four 借 in
  `data/` were 借著 for the book's 藉着.

So the pairs are not symmetric: 著→着 and 借→藉 are safe only in the contexts
D17 checked, and any dictionary has to record the exception beside the rule.

**Caveats, which are most of the work.**

- **Coverage is a floor, not a census.** The heading comparison that found all
  this reached 327 of 848 pages, because on the other 521 the first line the
  reader recovered was not the heading. The lyrics have never been swept page
  by page at all — D17's seven pairs were verified at nine places and then
  applied everywhere, which is sound for a glyph but proves nothing about a
  pair nobody has looked for.
- **The text layer cannot be believed on exactly this question.** It reads 爲
  as 為 more often than not, 裏 as 裹 four times in five, and 祢 as 妳 always.
  Any candidate pair it suggests has to be confirmed on an image, and its
  counts must never be used to decide a pair on their own.
- **One candidate was the layer's, and is closed.** 冼 appears 70 times in the
  layer against 洗 51, which had the shape a real eighth pair would have. It
  is not one: `data/` holds 洗 116 times in 71 hymns and 冼 not once, and
  `zh/506` prints 480's 洗滌 and 洗我 with 洗. `data/` descends from an OCR
  independent of the layer, so the two disagreeing is the layer misreading.
- **`你`/`祢` is not a glyph question**, and there are four of them, not two:
  你 neutral, 妳 feminine, 祢 for God and 袮 a second shape of 祢. `data/`
  carries 4,547 你 and 8 妳 — hymn 109's Psalm 45 daughter and hymn 105's
  Church, both correct — and no 祢 or 袮 at all. Choosing between them is a
  reading of who is addressed, so this cannot go in the orthographic table; it
  has its own, and it is folded in *search* only. See D17.
- **The preface is exempt.** `data/preface.zh.markdown` is a modern
  publisher's note, and `zh/001` prints 為. Any dictionary applied across
  `data/` has to know that not all of `data/` is the 1960s typesetting.

**Size.** It was small as a table and as a search change, and both are done.
What is left under this heading is the sweep of the lyrics, which is really
D17's outstanding half and belongs to whoever does 你/祢 — and the caveats
above say what such a sweep would have to establish before it moved a
character.

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

### D12 — the book names its hymns, and we had none of those names — **done**

`title` was empty on all 848 hymns, and this document said that was correct
because the hymnal prints no title over a hymn. True of the *page* — the scan
of hymn 8 carries the running-head subject, the meter, the number, the credit
and the music, and nothing else. Not true of the *book*.

**How the book defines a name.** Its own back-matter index is headed *Index of
First Lines and Choruses* — "first lines are in lower case type; choruses in
small caps" — which is the book saying a hymn is known by its opening line and
by its chorus. The one place it names each hymn *once* is the **subject
index**: 764 entries in the main index and 45 more in the supplement's own, all
in one lower-case face, nothing marking which are names and which are opening
lines. Against the line each hymn opens with: 373 the same (49%), 148 that line
cut short to fit the column (19%), **243 another name altogether (32%)** — the
tune (`Abba`, `Higher ground`, `Spirit song`, all verbatim in the Alphabetical
Index of Tunes), the chorus (`Up from the grave He arose`), or what the hymn is
plainly called (`How great Thou art`, `Leaning on the Everlasting Arms`).

**The other source had nothing.** `ccbiblestudy.org/Topics/H8Hymnary` — the
same brother's site, the lineage `data/` descends from — heads every hymn and
every index entry with a truncated Chinese first line: 008 is 【當我思念，我主】
/ *O Lord my God, when I in awesome wonder*, not *How great Thou art*. Same
convention we already had, so no title information. It does carry
`H8preface-T.pdf`, which is §3.

**What was built.** `data/titles.tsv`, 778 rows, and `apply-titles` /
`check-titles` beside the category pair. The words come from `data/`, not from
OCR: 719 of the 778 match a span of their own hymn's English text, and because
the span is matched against the *printed extent* the book's truncations survive.
The other 59 were read off the rendered index pages by eye. Where the index and
the hymn page disagree on a word, the page won, as it does everywhere here.

`slides.title()` now fills a title **per language** — the book's English name
where there is one, the first line where there is not, the Chinese first line
always — so hymn 8 reads *How great Thou art* beside *當我思念，我主，你創造大工*
on its deck, its page and the subject index.

**It confirmed D6 from a second direction.** The supplement's subject index
lists 45 of the 48 supplement hymns `data/` gives English text to. The three it
omits are 779, 789 and 840 — exactly the three named on the book's own *Hymns
Available In Chinese But Not In English* page, and exactly the three D6 says
carry English the book does not print.

**And it found a dropped word.** Hymn 365 was indexed *Love Divine, all loves
excelling* while `data/` had *all love excelling*. Its page
(`scan/en/397.png`) prints `all loves ex-cel-ling`, so the lyric was a
character short; corrected. The name now resolves from the hymn's own text like
the other 719, leaving 58 read off the page by eye.

This is the third check of its kind. The meter counts syllables against the
Chinese text; the subject index's hymn lists cross-check the subject order; and
a name that disagrees with the line it is supposed to be finds a dropped word
in the English. Each was built for something else and caught a defect on the
way past.

### D10 — fixed in passing

`DEVELOPER.md` still said the category table had 290 rows; it had 286 by then
and has 285 now. Corrected, and it names subjects rather than rows.

### D20 — the footnotes were two kinds of thing, and four were neither — **done: 19 inline notes classified, 7 stay, 8 move, 4 no page prints**

[Issue #6](https://github.com/ickc/selected-hymns-ng/issues/6). `data/` used
Pandoc's inline footnote, `^[...]`, nineteen times over sixteen hymns, and
`slides.py` called every one of them a singing instruction — its comment said
so: *"in this collection these are singing instructions rather than annotations
of the text"*. Seven of the nineteen are annotations of the text, four are on
no page at all, and the field that should have held the rest was a single
scalar that could hold only one.

**What the pages actually print.** Two conventions, and they belong to the two
kinds of thing:

| the book prints | where | example |
| --- | --- | --- |
| a **gloss** — a word about a word | at the page foot, keyed by an asterisk in the line or by quoting the word and naming its stanza | `en/353`: `* Meaning, married ( Isa, 62:4).` over `*Beulah Land`; `zh/523`: `(第四節“靉靆”意思是雲層籠罩的樣子)` |
| a **direction** — how to sing it, or what the other edition has | under the last stanza, in parentheses, set apart from it | `en/266`: `(Repeat the last four lines )`; `zh/258`: `(第四節末兩行重唱一遍)` |

So the two are told apart by where they are written, and nothing has to guess:
a direction is front matter, under `note`; a gloss stays in the lyric line,
anchored after the word it is about. `note` is now a **list**, because the book
prints more than one on a hymn — 355 prints one under each of its two stanzas,
and 242 prints a repeat direction under its last stanza and a word about its
tune over its first.

**The six that stay inline, all corrected against the page.** Every one had
lost something in transcription: `data/` wrote the quoted word in `「」` where
both editions print `“”`, and dropped the stanza the Chinese note names.

| hymn | page | `data/` had | the page prints |
| --- | --- | --- | --- |
| 324 | `en/353` | `Meaning, married (Isa, 62:4.)` | `Meaning, married (Isa, 62:4).` |
| 433 | `zh/454` | `「基督」可唱作「耶穌」` | `“基督”可唱作“耶穌”` |
| 496 | `zh/523` | `「靉靆」意思是…` | `第四節“靉靆”意思是…` |
| 558 | `zh/596` | `「明亮晨星」指主基督` | `第二節的“明亮晨星”指主基督` |
| 766 | `zh/822` | `「實際」指基督` | `第一節的“實際”指基督` |
| 768 | `zh/824`, `en/834` | `「眞」指基督` / `"truth" denote Christ` | `第一節“眞”指基督` / `(“Truth” in the first stanza refers to Christ)` |

768's English half was not a transcription of anything: the page prints a
sentence, `data/` had three words of its own.

**The four no page prints.** The same shape D7 found on 274 — a direction
invented to stand in for something the hymnal writes out.

- **393** carried `Repeat last line` and `重唱最後一句` under its eighth
  stanza. Both pages (`en/426`, `zh/416`) print that stanza's last line
  **twice**, and neither prints a note. The line is now written out, as the
  book writes it, which is why the meter report is 64 and not 63: 393's eighth
  stanza has a line its other seven have not, and that is what the page says.
- **830** carried `重唱「求你快回來」兩次。`. `zh/895` writes the phrase out
  three times under the music and prints no note; the `重` already in its meter
  is where the repeat is recorded. Removed.
- **813** carried `Repeat last line.`. `en/858` and `en/859` print no such
  thing. What `en/859` does print, under the seventh stanza, is
  `(The Chinese version has 4 stanzas only)` — a different statement about a
  different thing, and now the hymn's `note`.

**Eight hymns gained a note the book prints and `data/` had never held.** Found
by asking `data/` where to look rather than by reading 1,776 pages: fourteen
hymns have a different number of stanzas in each edition, and the Chinese
edition remarks on it. Six of the fourteen carry such a note; the other eight
print nothing at the foot of their last page.

| hymn | page | the note |
| --- | --- | --- |
| 129 | `zh/134` | `英詩僅有一、二、五等三節` |
| 460 | `zh/481` | `英詩無第二節` |
| 717 | `zh/773` | `英詩無第四、五節` |
| 757 | `zh/814` | `英詩無此詞` (the page labels the stanza `(第二詞)`, which `data/` already holds as stanza 2) |
| 769 | `en/835` | `The Chinese version has 5 stanzas` |
| 813 | `en/859` | `The Chinese version has 4 stanzas only` |
| 242 | `en/266` | `This hymn may be sung to the tune of “Pass It On” (Not printed here due to copyright)` |
| 394 | `zh/416` | `因中文版權問題，不印樂譜，請參照英文版。` |

The last two are the reason those two hymns have no music on one side, which
`data/` records nowhere else.

**Three more, found afterwards** while reading pages for D4's bare `特`, and
none of them has an English counterpart: `zh/26` prints 394's copyright note
over hymn 21 and `zh/793` prints it over 735, and `zh/26` also prints
`(可換唱第十六首調)` under hymn 20 — the first of D16's tune-borrowing family
to be carried. How many other Chinese pages print the copyright note is not
known; the pages that print it were found by chance, not by a sweep.

**And a check, so it cannot decay.** `pixi run check-notes`
(`src/hymn_projection/notes.py`) reads the prose back against the hymn. A gloss
that reads as a direction; a gloss quoting a word its own line does not hold; a
gloss naming a stanza other than the one it sits in; `英詩無第N節` on a hymn
whose English does have stanza N; `英詩僅有…` naming the wrong set;
`The Chinese version has N stanzas` counting wrongly; a hymn both told to repeat
its last line and printing the repeat already. Every rule was broken somewhere
in `data/` before the two kinds were separated, and none is now — so this is a
gate, not a report. Sixteen tests cover it.

**Two loose ends, both since closed.**

- **355's English half, `Repeat the first eight lines`, was on no English
  page.** `en/387` was read again at the foot: it prints nothing there, and
  what it does carry is *Fine* over the eighth line and *D.C. al Fine* over the
  last, which say the same thing in the notation's own words. The Chinese page
  prints the sentence, `zh/377`'s `(回頭再唱正歌一遍)`.

  **The English half is removed**, and 355 joins the six hymns
  [D4](#d4--six-notes-have-lost-their-english-half--done-the-english-edition-prints-no-note)
  settled the same way — 470, 584, 611, 659, 705, 720 — where the Chinese page
  prints a note, the English page prints none, and the English edition carries
  the same instruction in its *setting* instead. That was the deciding parallel:
  D4 read all six English pages and found the repetition written into the music
  or stated as `with repeat` in the meter, and 355's `D.C. al Fine` is exactly
  that. `note` is now a quotation throughout — no half of it is anybody's
  translation of a thing the other edition prints.

  It cost something, and the cost is worth stating: on an English-only view of
  355's deck the note is empty, as it already was on those six. The direction is
  not lost, it is where the English edition puts it. This is *not* the same
  question as the nineteen inherited bilingual notes, whose English is unsourced
  but whose provenance is unknown and which D16 still holds: 355's English half
  was known to have been written by hand into an inline footnote, and its page
  has now been read.

- **42's `\[glorious claim\]` was a Markdown escape doing nothing.** `en/56`
  prints `The Father only [glorious claim]!` with literal square brackets, and
  `data/` had escaped them. Both spellings were tested against the codec and
  **both are stable** — Pandoc reads and writes either unchanged, they parse to
  the same text, and the built HTML and `search.json` already showed plain
  brackets either way. A bracket that cannot begin a link needs no escape, so
  the escape was noise in a file meant to read like the page.

  **The backslashes are removed**, which leaves `data/` with **no backslash in
  any of its 848 files**. That is now a test in `tests/test_conversion.py`, and
  a code-point assertion of the kind
  [D19](#d19--the-punctuation-is-not-one-convention-but-several--done-386-lines-corrected-in-eight-classes-and-check-punctuation-keeps-them)
  wants: a backslash anywhere in `data/` means something is in the source that
  the page does not print.

**What is still open**, and belongs to
[D16](#d16--neither-editions-page-annotations-are-carried--partly-done): the tune-borrowing
notes (*"may be sung to the tune of hymn #467"* on about ten English pages,
`調用第四百九十一首` on about seven Chinese ones), the provenance notes
(`蓋恩夫人獄中之詩`), the long instruction on `zh/152`, and the copyright lines
under the copyrighted settings (`en/426` carries one). Those need a sweep of
the pages themselves, and the PDF text layer that made D16's estimate is not
checked out beside this repository any more. The nineteen bilingual `note`s
inherited from `data.yml` were **not** re-verified against pages here; their
English wording varies in a way an invention would not (`Repeat the last 2
lines` beside `Repeat the last two lines`), and a mechanical check — does any
hymn told to repeat its last line already print the repeat? — clears all
twenty-five.

### D19 — the punctuation is not one convention but several — **done: 386 lines corrected in eight classes, and `check-punctuation` keeps them**

*(This was the dependency [D21](#d21--a-repeat-is-written-three-ways-and-read-none--done-28-hymns-say-which-lines-and-check-repeats-keeps-the-three-statements-together) named. It was met, and D21 is now done.)*

Every mark in `data/` was counted, English lines and Chinese lines apart, and
then read against the pages. Punctuation is not sung, so nothing that counts
syllables can see it: the meter report stood at 64 before this work and at 64
after, which is the proof that none of it moved a syllable, and also the reason
it survived D7, D14 and every check built since.

**What the count found**, and what the pages said about each: 386 lines in
145 hymns, eight classes, one commit apiece.

| what was there | how many | what it is now | decided by |
|---|---|---|---|
| `,` `!` `﹕` `﹔` in Chinese lines | 7 | `，！：；` | the count alone — one halfwidth or presentation form against thousands |
| `'` and `‘` for an elision or a possessive | 173 | `’` | the words themselves, then `en/847` |
| `"` in 22, `–` in 1 | 7 | `“”`, `—` | `en/35`, `en/16` |
| `－` and a lone `—` for the Chinese dash | 89 | `——` | `zh/49` and `zh/500`, measured |
| a Chinese line beginning `——` | 5 | moved to the line before | `zh/49`, `zh/265` |
| ideographic and multiple spaces padding a line | 41 lines | one space, or none | `zh/647` |
| a line beginning `”`, or opening with it | 7 | moved, or `“` | `zh/32`, `zh/170`, `zh/488`, `en/40`, `en/44`, `en/606`, `en/712` |
| `「」` | 112 | `“”` | `zh/748`, `zh/756`, `zh/776` |

**Three of those classes were not in the survey**, and the check found them
because the alphabet rule does not know in advance what it is looking for.

- **35 apostrophes were set backwards**, as `‘`, not straight: `‘Tis`,
  `‘Neath`, `‘gainst`, `‘Twas`. The survey had counted `’` against `'` and not
  asked what the `‘` were. Every one is an elision and none is a quotation, so
  they join the 138.
- **98 ideographic spaces padded 41 lines out to a column.** `zh/647` prints
  607 in two columns and `data/` wrote each pair as one line, padding the gap
  — three spaces after a six-character half-line, one after a seven. A run
  whose length is a function of what precedes it is the page's column width,
  not text.
- **112 corner brackets are not the book's mark.** They sat in nineteen hymns,
  all between 670 and 768, which looked like a section set in its own style.
  It is not: `zh/776` prints 720's `“主，祢已經有九十九，難道還嫌不夠？”`,
  `zh/756` prints 700's `“幾乎”甚爲不妥，`, `zh/748` prints 692's
  `“你們必須重生！”`. The Chinese edition quotes with `“”` throughout.

**The dash was the one question a count could not settle**, and the pages did.
`data/` spelled it three ways and position did not sort them: both the doubled
`——` and the fullwidth `－` appeared at the end of a line and in the middle of
one. So the printed marks were measured against the glyph pitch of the line
they sit on. `zh/49`, where `data/` spelled them `——`, gives 0.53, 0.49, 0.53
and 0.50 of a character width; `zh/500`, where `data/` spelled them `－`, gives
0.43 to 0.68 across six hymns. One mark, about half an em, in a face that sets
all its punctuation narrow. One mark, so one spelling — the doubled one, which
is the Chinese convention and what two-thirds of the collection already had.

**Two marks stay for one line each, and each names its page.** 418 ends
`不知如何方能重新…`, and `zh/439` prints the three dots, though Chinese usually
sets an ellipsis as six. 797 sets `Thy way – Thy chosen way,` with a spaced en
dash, and `en/847` prints exactly that: the later material, 765–848, is
typeset in a modern face with conventions of its own, where everywhere else the
English dash is an unspaced em dash. That same page settled the apostrophe,
printing `’Tis` with the curly mark.

**Two things fell out that are not punctuation**, and are recorded here because
this is where they were seen.

- **`zh/439` prints `主阿,憐憫!` where `data/` had `主阿憐憫！`** — a comma the
  transcription had dropped. It is restored. The check cannot find the others
  of its kind, because it asks *which* mark and not *whether* one; finding
  those is a page-reading pass, and belongs with [D16](#d16--neither-editions-page-annotations-are-carried--partly-done).
- **`zh/647` shows 607's lines are two half-lines**, and `data/` writes them as
  one joined by a space. 23 hymns do that. Whether they should instead be two
  lines is a lineation question, which is [D7](#d7--the-meter-against-the-lyrics--done-139-disagreements-down-to-63-and-the-63-are-the-hymnals-own)'s
  and not this one's; the space is kept because it records the break, and the
  padding is gone because it recorded the page's width.

**What is now asserted**, by `punctuation.py` and `pixi run
check-punctuation`, and by 14 tests:

- **the alphabet.** A Chinese lyric line holds Han and `，。、；：！？“”（）——…`;
  an English one holds Latin, a space and `,.;:!?-—()[]“”’`. Every class above
  falls out of this one rule, and it stays true afterwards without anyone
  watching it. **The English is not normalised toward ASCII**: `PANDOC_MARKDOWN`
  is `markdown-smart`, and `smart` would read a leading `'` as an opening quote
  and set `'tis` as `‘tis` where the page prints `’tis`.
- **the line boundary**, which the D7 re-lineations were done under and which
  nothing until now stated: a closing mark stays with the line it closes and an
  opening mark goes with the line it opens. The dash counts as closing, because
  it breaks off from what precedes it and the pages set it there.
- **the pairing**, strict in Chinese and loose in English. English sets a
  speech running through several stanzas by opening each of them and closing
  only the last — 345 does — so there the rule is only that a quotation is
  never closed before it is opened, which found three lines that had opened one
  with `”`. The strict half found 720's unclosed quotation, and 720 found the
  corner brackets.

**The fixer is not kept.** Each class was a one-off script and a commit
somebody can read; what is kept is the assertion, which is the half that has
work left to do.

---

### D21 — a repeat is written three ways and read none — **done: 28 hymns say which lines, and `check-repeats` keeps the three statements together**

The hymnal states a repeat in three places and relates none of them: written
out in the lyrics, ordered in a `note`, or marked `重` / `with repeat` in the
meter. Counted over 848 hymns:

| | hymns |
|---|---|
| the lyrics write a repeat out | 47 |
| the meter carries `重` / `with repeat` | 35 |
| a `note` orders one | 26 |

**Nothing acted on any of it.** A deck whose hymn says *Repeat the last line of
each stanza* printed that sentence on the title slide and then showed each
stanza once; the congregation had to remember. That gap is now closed the way
`chorus_sources()` closes its own: the source states the structure once, and
the two projections differ — the slide **sings the repeat**, on a slide
labelled `Repeat 重唱` beside the chorus's `Chorus 副歌`, and the page keeps the
book's shape and prints the note.

#### The three statements reduce to twenty-eight hymns

The survey's three-way overlap made this look like a reading of 44 pages. It is
not, and the reduction is worth setting out, because every step of it is a
statement about where the book has already said the thing.

| what asks for a repeat | hymns | where the answer is |
|---|---:|---|
| the lyrics write it out, and nothing else asks | 36 | in `data/` already — nothing to add |
| the lyrics write it out and the meter is marked | 11 | likewise |
| the meter is marked and a `note` orders one | 17 | the note |
| a `note` orders one and no meter is marked | 9 | the note |
| the meter is marked and nothing else says anything | 7 | the pages |

Of the last seven, **four write the repeat out in a shape the tail rule cannot
see**, and finding that was the first of the two things this pass turned up.
122 sets `Let angels prostrate fall,` twice in the *middle* of every stanza and
`en/135` prints it twice in stanzas 2, 3 and 4 as well as under the music; 534
sets `Or on this earthly ball, Or on this earthly ball.` on one line; 650 sings
its third and fourth lines again with a fifth interposed; 678 writes the whole
repeat out as `1-chorus`.

So three hymns had to be read off their pages — 54, 57 and 575 — and 25 had a
direction printed under them. Five of those twenty-five still needed their
music looked at, for a reason given below, and 355's is a shape the field does
not hold: 28 in the end.

#### `repeat`, and what reading 57's page did to the spec

The spec this section previously proposed was `{stanzas: all, lines: 1}`: a
count of trailing lines, per language. `en/71` says it will not do.

Hymn 57 is `8.6.8.6. with repeat`, and the music under its first stanza sings
`And drives away his fear, / And drives away his fear. / It soothes his sorrow,
heals his wounds, And drives away his fear.` — the fourth line twice, then the
third and fourth again. That is no tail of anything. It is also, exactly, the
four lines hymn 678 writes out as its chorus, under the same meter. So
`with repeat` on an `8.6.8.6.` tune is a refrain built out of the stanza's own
lines, its shape belonging to the tune and not to the notation, and half the
collection's instances of it are written out while half are not.

`repeat` therefore holds **a sequence of the stanza's own line numbers, in the
order they are sung**:

```yaml
repeat:
  lines: [5, 6, 7, 8]
  stanzas: [4]
```

`stanzas` is every stanza unless it names some, and 242 is the only hymn that
names any. `lines` is 57's `[4, 4, 3, 4]`, 575's `[7, 8]`, and 54's
`[1, 2, 3, 4]` — the whole stanza, which `en/69` prints as an *Optional Repeat*
over a first ending and which the English meter records as the `D.` of
`7.8.7.8.D.` over four written lines.

#### It is not per language, and 242 is why not

The second thing this pass turned up contradicts what this section used to
argue. 242 was the reason a repeat "must be per language": `en/266` prints
*Repeat the last four lines* and `zh/258` prints `第四節末兩行重唱一遍`, and
those looked like four lines against two.

They are the same statement. **The Chinese page sets its stanzas in two
columns**, so two of its printed rows are four of `data/`'s lines — the same
typographic fact D19 found under 607 on `zh/647`. Both pages print the
direction under the fourth stanza and both mean that stanza alone, which is
what `stanzas: [4]` says.

With 242 gone there is no counter-example left: **every stanza of every hymn
that carries a repeat has the same number of lines in both editions**, so the
line numbers mean the same thing on either side and the field is a single
statement about the hymn. It also settles which half of a bilingual note the
check should read — the English one, because an English page sets one line to
a row.

#### Where the twenty-eight values came from

**Twenty are the English half of a direction the book prints**, taken at its
word and then asserted: `check-repeats` reads *the last N lines* out of the
English half and requires the field to hold N. That is not a derivation the
data could drift away from silently.

**Eight had no English half to read**, and were read off the music instead:

| hymns | what `data/` had | what the page sings |
|---|---|---|
| 470 | `重唱每節最後一行` | `zh/492` sings `榮耀中的生命，成了我生命。` again — one printed row of a two-column stanza, and two lines |
| 584, 611, 659, 720 | `最後一句唱兩遍` | one line, on each of their four pages |
| 575 | nothing but `with repeat` | `en/622` sets the last two lines again |
| 57 | nothing but `with repeat` | `en/71` sings `[4, 4, 3, 4]` |
| 54 | nothing but `重` | `en/69` marks *Optional Repeat* over the whole stanza |

470 is the one that shows why the Chinese half could not simply be counted:
`一行` there is a printed row and means two lines, where 211's `一行` on a page
that is also two-column means one, and only the music says which.

#### What the check asserts

`pixi run check-repeats` (`src/hymn_projection/repeats.py`) is a gate, not a
report. A meter marked `重` must have its repeat somewhere; so must a note that
orders one; a repeat written down must not also be written out, or it would be
sung twice over; a repeat must have something asking for it; and the English
direction's count must match the field's. A repeat naming a line or a stanza
the hymn has not is refused by the model before the check runs. Nineteen tests
cover it.

**What accounts for a repeat that is not written down** is the tail rule
`notes.writes_the_repeat_out` — now public — plus four hymns named with their
reasons, and naming them rather than ruling them is the honest half of this
section. 534 sets `Or on this earthly ball, Or on this earthly ball.` on one
line and 321 sets `Full salvation! Full salvation!` on one line. Those are the
same shape and only one of them is a repeat. **Text identity cannot tell a
repeat the book chose to write out from words that simply repeat** — which is
what this section argued when it argued against compression, and it is just as
true in the other direction.

#### What the meter got out of it

`meters.repeats()` admits every tail a `重` might mean, because the mark does
not say which. Where a hymn now carries a `repeat`, that one run is offered and
the guessing stops.

**The report is unchanged, to the byte** — still 64. That was named here as the
prize and it did not materialise, and the reason is worth writing down: the
hymns whose verses actually needed one of those extra runs are exactly the
eleven that *write* the repeat out, and there the tail is in the lyrics rather
than in a field. A hymn that leaves its repeat to the meter has verses that
scan as the meter prints it. So what this buys is not a settled hymn but a
closed door: a repeat entered wrongly will now fail to scan instead of being
absorbed by whichever tail happens to fit.

#### The proposal that still does not work is compression

Deriving the direction from the lyrics — finding the written-out repeats and
folding them away into a `note` — remains wrong, and each reason was measured
rather than guessed.

1. **It would replace what the page prints with prose the page does not.** The
   book does both: some hymns it writes out, some it notes, and `data/` is a
   transcription of the page. Compressing 734, whose stanzas `en/802` prints in
   full, into a direction `en/802` does not carry is precisely the defect
   [D20](#d20--the-footnotes-were-two-kinds-of-thing-and-four-were-neither--done-19-inline-notes-classified-7-stay-8-move-4-no-page-prints)
   removed from 393, 830 and 813.
2. **A written-out repeat is not a property of the hymn.** Of the 31 that write
   one out by exact match, **18 write it in only some of their stanzas** and
   **25 have the two editions disagreeing about where**. 274 writes it under
   the music and leaves it to the singer in the stanzas printed as text; 393
   writes it in the eighth stanza and in none of the other seven.
3. **Detection is decided by punctuation.** Hymn 82 writes its last line twice
   in every stanza of both editions and closes the first copy with `，` and the
   second with `！`. Matching exactly finds that repeat in three of its eight
   stanza-halves; folding the trailing punctuation away takes the collection
   from **31 hymns to 47**. And the differing mark is not noise — it is the
   same line said again with more force. That fold is what
   `notes.writes_the_repeat_out` does, and D19 is what made it a statement
   about the text rather than about the transcription.

   Hymn 8's chorus shows the other side of it: `Then sings my soul… / How great
   Thou art… / Then sings my soul… / How great Thou art…` is not a compressible
   repeat, it is the words of the chorus, and only a punctuation difference
   (`Thee:` against `Thee,`) keeps the detector from claiming it.

The direction this section did take is the mirror image: the *note* is the
source and the *structure* is derived from it, which is checkable in the one
place it matters and never rewrites a page.

#### Two things it does not hold, and one it moved

**355's *da capo* is named rather than held.** `zh/377` prints
`(回頭再唱正歌一遍)` and `en/387` prints *Fine* over the eighth line and
*D.C. al Fine* over the last: the whole verse again, after the chorus. `repeat`
holds lines of a stanza sung where the stanza ends, and that is a different
shape; `check-repeats` names the *da capo* so that 355 is an exception on
purpose rather than a hole.

**745's is a repeat, and is held.** `en/812` and `zh/802` both mark *Fine*
after the third line and *D.C.* at the end, and say so nowhere else: the hymn is
sung A B C C A, where A is the three lines to *Fine*. 745 is one stanza with no
chorus, so going back to the top sings A's own words again, and that is
`repeat: {lines: [1, 2, 3]}` exactly. `check-repeats` names it in
`SCORE_ASKS`, the hymns whose repeat only the score asks for, beside
`WRITES_IT_OUT`.

Getting there took the Chinese lyrics apart first. `data/` had written the
*da capo* out as two extra Chinese lines no page prints, and had joined two
pairs of lines the English keeps apart, so both halves came to twelve lines and
nothing counted a difference — but every pair from line 5 on stood against the
wrong line. The Chinese page sets the text continuously under the music, so the
lines now break where the English breaks, as 824's did under D5, without a
character moving.

**How many more, as a guess.** Searching the text layer of both editions for
*Fine* and *D.C.* (not read against the images) finds the marks on the pages of
nine hymns besides 355 and 745: **167 or 168** (`en/184` holds both), **234**,
**456**, **505**, **518** (`D.C. Chorus`), **742** and **753**, and in the
Chinese layer alone `zh/176` and `zh/248` (167/168 and 234 again). The Chinese
layer missed 745's own marks, which `zh/802` plainly prints, so this is a floor.
Each is a hymn to read before anything is written down: a *D.C.* on a hymn with
several stanzas may be 355's case — the score's way of sending the next stanza
back to the verse — rather than a repeat of words at all.

**The repeat slides are kept out of the search index.** They hold lines the
stanza before them has already sung, so indexing them would put the same hymn
in the results twice for no new match — the reason `pages.py` already gives for
indexing the decks and not the pages. The count is 6,907 before and after.

**`data/` gained no lyrics.** Every one of the 28 is front matter; not a
syllable moved, and the meter report and the chorus report are both unchanged.

**Dependencies.** D19 was the one, and it was met before this began.

---

## 3. The preface — **done**

**Source.** Two pages, one each: `en/001` (English *PREFACE*, ~2.6 kB of OCR)
and `zh/001` (Chinese *編者的話*, ~1.1 kB).

**They are not translations of each other.** The English preface is about how
764 hymns were chosen out of three centuries of English hymnody, who is
represented, and what the indexes are. The Chinese 編者的話 is about how the
Chinese edition was assembled *afterwards* — existing Chinese translations
sought out and revised to match the English tune, meter and stanza count, the
missing ones newly translated, and hymns 765–848 added because good Chinese
hymns had no English counterpart. It even asks bilingual meetings to avoid
choosing from that appendix. Two documents, one book. They are presented as
two, not as a bilingual pair.

The Chinese preface is, incidentally, the primary-source explanation of the
whole 765–848 structure this project keeps running into. It also dates the
Chinese edition — 一九九五年一月 — and names the publisher both editions share,
生命樹出版社 / Tree of Life Publishers.

**Why an LLM was the right tool.** The OCR is legible but corrupt in ways only
a reader can repair: `aud` for `and`, `fonnat` for `format`, `sainL~.` for
`saints,`, `·111e` for `The`, `Tree of Lite Publishers` for `Tree of Life
Publishers`. Every one of those is unambiguous *in context* and unfixable by
rule.

**What was built.** `data/preface.en.markdown` and `data/preface.zh.markdown`
— plain Pandoc Markdown, edited like a hymn — and `preface.py`, which stacks
them into `site/preface.md`, English above Chinese, each edition's prose in a
div carrying its language so a reader's font stack and a screen reader both
switch at the boundary. The sources are the data; the page is generated,
git-ignored and rebuilt in CI, like every other projection. It is in the
navbar as **Preface 編者的話**. The English preface keeps the paragraph on the
book's own indexes, which is the book describing the back matter §4, §5, §6a
and §6b reproduce.

**It turned up a bug on every page but five.** The navbar entries used to name
the Markdown they come from — `href: preface.md`. Quarto rewrites a `.md` href
to its output only where that document is one of the *project's* render
targets, and `build_site.py` gives the five collection-wide pages to worker 1
alone; so on every page the other workers render — which is nearly all 1,696 of
them — the href survived into the HTML as written and handed the reader the
source file. A two-worker build over four hymns shows it plainly: hymn/1 and
hymn/3 linked `../preface.html`, hymn/2 and hymn/4 `../preface.md`. All five
entries now name the `.html`, which is made relative to the page it is on
either way, and the active-page marking still lands.

**Provenance is not recorded, and cannot be checked here.** The sources carry
no front matter saying which PDF page they were read off or how. That is worse
than it sounds for these two pages in particular: `en/001` and `zh/001` are
front matter, and **front matter is not in `scan/`** (see §7), so unlike every
hymn there is nothing in this repository to check the transcription against.
This is the strongest case yet for §7's option 2 — carry the front and back
matter in `scan/` too.

**~~Still open: the TABLE OF CONTENTS.~~ Done — as a check, not a table.**
*TABLE OF CONTENTS* (`en/002`, `zh/002` 分類目錄) is the eighteen sections
against the hymns filed under each, and nothing else. It was read on both
pages and used to check the level‑1 assignment of all 848 hymns, which it
confirms; §4's tree now states each section's hymn numbers, computed from the
hymns rather than stored, so the two cannot drift apart. See §4 and
`DEVELOPER.md`. *INDEX OF INDEXES* (`en/003`) is about the paper book's page
numbers and is worthless here.

**Cost, as it turned out.** As advertised — two pages, one reading pass each —
plus the navbar bug the pass exposed, which was not free and was worth the
finding.

---

## 4. A subject index page — **done**

`site/subject.md`, written by `md-to-site` from `data/categories.tsv` and the
category on every `data/N.md`, and reachable from the navbar. 18 sections, 232
subheadings, 57 third-level subjects, 848 hymn numbers each appearing exactly
once, in the order the book prints them. (201 subheadings since D3 folded the
31 scripture passages into their section.)

**A third source now checks it.** Both editions' *TABLE OF CONTENTS* pages
(`en/002`, `zh/002`) print the eighteen sections against the hymns filed under
each. They were read after the fact and agree with `data/` on all 848 hymns,
and on the nine subheadings the pages expand — the only independent
confirmation the supplement's 84 sections have. The page's heading strip now
carries those ranges, computed from the hymns so they cannot drift from the
entries below. See item 10 of §8.

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
   prints*, alongside a note that the book orders them by name. The second
   table remains an option, not a plan.

Each hymn is its number and what the book calls it, in both languages, set in
columns as the book's index is. Checking that name against the line we had been
inferring is what turned up D12, and the names now come from D12's table.

**What the page does not do.** No collapsing: 303 headings and 848 entries make
a long page (244 KB), but it is one document — the browser's find works on it,
it prints, it needs no JavaScript, and it is in the search index one entry per
section, so a subject can be searched for by name in either language.

## 5. Index of authors and composers — **done**

**Source.** `en/879`–`en/894`, sixteen pages, printed 821–836. Three columns:
`Hymn | Author, Translator, Source | Composer, Arranger, Source`, one row per
hymn 1–764.

**What was built.** `data/authors.tsv`, 764 rows — 704 authors, 708 composers,
747 hymns that gain at least one name where `data/` had four — plus
`authors.py`, `apply-authors` / `check-authors` under the same contract as the
categories, the titles and the tunes, and a `composer` field on the hymn, which
is new. Both names show on the hymn page at the end of the meta line, marked 曲
for the music and 詞 for the words, because two personal names side by side are
the first pair on that line a reader could not tell apart.

**The plan expected a reading pass, and got a parse plus a proofread.** The
premise was right that `en/879.txt` extracts as a bare list of hymn numbers
with both text columns dropped, and that two more pages do the same. What it
missed is that the `.json` beside each page carries every line's x and y, which
say which column a line is in and which row it is on. That recovered the whole
table's structure — 764 rows, 1 to 764, no gaps, no duplicates — and left only
the characters to read. The readers then proofread a page each against its
scan, correcting rather than transcribing, which is a far more reliable job.

**The numbering is positional, not transcribed.** Five printed numbers are
corrupt — `IOI`, `Ill`, `I 16`, `I 17`, `31 I` — so each page's first hymn is
decided by a vote among its legible ones, and a corrupt one is outvoted instead
of believed. Every page's start then landed on the previous page's end plus one
unprompted: sixteen independent agreements.

**A reader caught a bug in the parser.** The page-881 reader reported the
composer column shifted a row against the page. It was: cells were matched to
the *first* row within tolerance rather than the *nearest*, with a tolerance of
4 against a row pitch of 8.5, so a cell falling between two rows went to the
upper one. Fixing it moved nine cells across four more pages, and the readers
of two of those confirmed the correction without being told what it was. This
is the single best thing the reading pass bought, and it argues for giving a
reader a draft to attack rather than a blank page.

**Self-verification, which had to be built.** §5's own worry was right — there
is no twin index the way the tunes had two. Four checks were built instead:
every hymn appears exactly once in ascending order, guaranteed by the parse;
page starts agree with the previous page's ends; the characters were read off
the images; and a name appearing once that is a letter from a name appearing
often was looked at by eye. That last found five of 509 one-off names. Four are
the book's own inconsistencies, kept as printed — `G. C. Martin` beside `W. C.
Martin`, `Williams G. Tomer` beside `William G. Tomer`, `E. Mary Grimes` beside
`E. May Grimes`, `Thomas D. Chisholm` beside `Thomas O. Chisholm` — and one was
a misreading, now fixed.

**A fifth check turned up that this section said did not exist**, and it is
D15: the copyright-bearing songs print their credits over the hymn, which is a
second printing of the same fact. It reaches only 71 cells of the 764 rows, but
21 of those agree outright and the fifteen that disagree are now settled by
taking whichever printing carries more — which makes this table a reading of
two sources rather than a transcription of one.

**Two marks of the book's own.** A blank is not a gap in the reading — the
index heads itself *(Blanks indicate untraceable sources)* — and 17 hymns have
neither name. `†` stands where an author would be on 34 hymns; its legend is
printed once, under the table on the last page, and reads *(† indicates
compiler)*. The table keeps the mark; a hymn file gets the word `compiler`,
because a dagger belongs to no writing system and `auto-lang` has nothing to
tag it as. The book supplies that wording itself: hymn 473's author is printed
`vv.2-5, compiler`.

**The supplement has none, as expected.** The English back matter's supplement
carries a table of contents, a first-lines index, a subject index and the list
of Chinese-only hymns, and no authors. The Chinese back matter is a first-line
stroke-count index and nothing else. So credits run 1–764, they are
English-only, and `apply-authors` removes any a supplement hymn acquires.

**Cost, as it turned out.** Far less than budgeted. The estimate assumed
sixteen dense pages read cold; the bounding boxes did the structure for the
cost of one script, and the sixteen readers spent their attention on characters
instead of columns. What the estimate got right is that the verification is the
hard part and had to be deliberate.

---

## 6. Indexes of tunes — **done, both of them**

**6b is done**: `data/tunes.tsv` carries 765 (hymn, tune) pairs over hymns
1–764, applied into a `tune` field on every one of them, and `site/tune.md` is
the alphabetical index generated back out of the hymns. What follows is the
proposal as it stood, with what happened marked in it.

**We did not have the data.** This was worth saying plainly, because the plan
depended on it. The book's metrical index is three-level — meter, then **tune
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

**6a. Metrical index of tunes** — **done.** `site/metrical.md`, the fifth
projection, generated from the hymns alone: 247 meters, 692 entries, all 848
hymns filed exactly once except 146, which is printed to two tunes and appears
under both. It needed no new table — both levels were already fields on the
hymn — and what had blocked it was that 30 of the 764 did not agree with the
book about their meter and would have been filed wrong.
[D13](#d13--the-metrical-index-against-both-editions-pages--done-59-meters-settled)
settled them.

**The order was the work.** A meter is filed by its figures read as a
sequence, not as a number and not as text: `10.` after `9.`, a shorter run
before the run extending it, and where the figures are equal the plain form,
then `(A)`/`(I)`, then `with Repeat`, then `with Chorus`, then the doubled form
with that whole run again under it, and `Irregular Meter` last. The check is
that the printed index's own 212 headings, read off `en/899`–`en/904` in
sequence and sorted by that key, come back in the printed order with none out
of place.

**It is filed by our data, not by the book's, which makes it three things more
than the printed index** — each stated on the page:

- **848 hymns rather than 764.** The book's index stops where the tune indexes
  do; every hymn now carries a meter, so the 84 supplement hymns file under
  theirs with the word *supplement* where a tune name would be. A metrical
  index exists to say what a text can be sung to, and that answer does not stop
  at 764.
- **Eighteen hymns under a count rather than under a refusal to count**, from
  D13. 93 are left under `Irregular Meter`, where the book files 101.
- **Both editions in the heading**, since a meter is the one field whose halves
  this collection names separately.

The disagreements with the printed index are therefore the ones D13 already
documents, and they are visible on the page: hymn 616, for one, sits under
`6.5.6.5.D.` beside Evelyns and Longstaff, where the book files it under
`6.5.6.5.D. with Chorus` — a chorus its two pages and its own two stanzas deny.

**6b. Tune names** — **done.** An extraction, and a good one. Sources:

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

**And it held.** 632 hymns got the same tune name from both indexes outright.
132 came back with the two scans disagreeing, and every one of those turned out
to be the scan misreading a name the two indexes print alike — settled by
cropping the printed line off both pages and reading it. What came out covers
exactly hymns 1 to 764, no hymn missing and none past the end, which is a shape
neither index states. The meter half of the cross-check is [D13](#d13--the-metrical-index-against-both-editions-pages--done-59-meters-settled).

It also pays for D1 for free: `Irregular Meters` is a heading in the metrical
index (`en/904`), so that index says which hymns are irregular, and D7's meter
audit gets a third opinion. **It did**: 101 hymns are filed under `Irregular
Meters`, and the comparison against `data/` is D13.

**Scope limits, again worth stating rather than hiding.** Tunes are English
edition only, hymns 1–764. One tune serves many hymns — `Beecher` is 1, 106,
226 and 365 — and the book sometimes prints one text twice under two tunes as
two hymn numbers (122 and 123 are both *All hail the pow'r of Jesus' name*, to
*Diadem* and to *Coronation*). Whether any single hymn number carries two tunes
is not knowable until the index is read; the model should not assume a scalar
`tune` until it is.

**Where it lives.** `data/tunes.tsv` — `hymn` and `tune`, one row per pair,
applied into a new `tune` field on the hymn under the same preprocessing
contract. **Not** `meter` as a third column: the meter belongs to the hymn and
is already in `data/N.md`, and a second copy would be a second thing to keep
true. The cross-check was done once, during the extraction, and what it found
is written down as D13.

**Cost, as it turned out.** Ten pages read, 132 printed lines cropped and read
by eye, and one model change (`tune` is a name or an ordered list of names, for
the one hymn the book prints to two). Far more tractable than §5, exactly
because of the double source.

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
consistent answer. §3 has since made this concrete rather than hypothetical:
both prefaces are transcribed, committed and on the site, and there is nothing
in this repository to check either of them against.

**The model will need changes.** At minimum: `meter` must accommodate
`Irregular Meter` / `特`, which breaks the shared-prefix representation (D1);
`composer` and `tune` are new fields, and `tune` may be plural (§6b). None is
hard, but each touches the codec, the round trip, and the tests, and they are
better done as one considered change than as three drive-bys. **All three
are made**: the meter fallback (D1), `tune`, which is indeed plural —
`str | list[str]`, for hymn 146 and no other — and `composer` (§5).

**Extraction protocol.** What worked for the categories should be the rule:
prefer a relation that can be checked against a second source; extract with
bounding boxes and verify by reading the page image; never let OCR text be the
final authority on a digit; and record what could not be resolved in the
committed table itself rather than in a commit message.

---

## 8. Suggested order

1. ~~**D5** — transcribe the missing English for 797, 824, 845.~~ Done; it also
   turned up a whole-hymn swap between 797 and 798.
2. ~~**D1**~~ Done: every hymn in the collection now carries a meter, the last
   45 read off the page in the D13 pass. ~~**D7**~~ is done as a syllable
   audit: the check now separates a verse that has lost syllables from one
   that only breaks its lines elsewhere, and reads the meter the **Chinese**
   page prints rather than the English figures the transcription had copied
   onto both halves. 139 disagreements are down to **63** — 64 after D20 —
   and none of them
   is a syllable this project can put back: 56 are a lineation question, four
   are a translation sitting a syllable differently on its tune, two are a
   score's first and second endings, one is a line the meter does not count.
3. ~~**§3 preface** — two pages, high value, nearly free.~~ Done:
   `data/preface.*.markdown` and `site/preface.md`. It also exposed a navbar
   bug on every page but five, and left the *TABLE OF CONTENTS* still
   untranscribed — since done, as item 11.
4. ~~**D9 + §4** — widen the category table with levels and printed numbering,
   then generate the subject index page.~~ Done; it also turned up D11.
5. ~~**§6 tunes**~~ Done, both halves: `data/tunes.tsv`, 765 pairs over hymns
   1–764, applied to `data/`, with `site/tune.md` and `site/metrical.md`
   generated back out. §6b turned up **D13**, which unblocked §6a.
6. ~~**§5 authors** — biggest, weakest verification, most valuable per hymn.~~
   Done: `data/authors.tsv`, 764 rows, applied to `data/`, with `composer` as
   a new field. It cost far less than budgeted, because the text extraction's
   bounding boxes gave the table's structure and left only the characters to
   read. It turned up **D15**, and it did not need `scan/` extending after all
   — though item 9 still stands on its own argument.
7. ~~**D3/D4/D6** — the small consistency fixes~~ Done, and they were not
   small in the way the section expected. **D3** turned out to be thirty
   missing references rather than eleven inconsistent ones: `ref` is now on 41
   hymns, both halves wherever both editions print one, and the field names its
   two languages the way a meter does. **D4**'s premise was wrong — the English
   edition prints no note on any of the six, and none of the nineteen bilingual
   notes is on an English page either. **D6** is kept and documented, and 840's
   English turned out to be hymn 720's. Between them they turned up **D16** and
   one dropped `.重` on hymn 470's Chinese meter. ~~D2~~ is closed by §5.
8. ~~**D12 titles**~~ Done: `data/titles.tsv`, 778 names, applied to `data/`.
9. **§7's option 2 — carry the front and back matter in `scan/`** (~70 pages,
   ~1.7 MB). Every extraction so far — the categories, the titles, the tunes,
   both prefaces — was read off pages this repository does not hold, so none
   of them can be checked here the way a hymn can be checked against
   `scan/{en,zh}/N.png`. §5 is the largest of them, and D15 shows the shape of
   the problem twice over: the check that found the index disagreeing with the
   hymn pages could only run because the *hymn* pages are here — and settling
   it meant reading eleven of them by eye, which is exactly what could not be
   done for the index's own sixteen pages. Every D15 row is now confirmed on
   one side and taken on trust on the other.
10. ~~**D18's variant dictionary**~~ Done, and it was as small as advertised:
    `site/search-fold.html` patches the two fuse.js methods Quarto's search
    passes every indexed document and every query through, and folds both into
    the form `data/` carries. Two tables: eight orthographic pairs, and the
    four shapes of *nǐ* — 你 妳 祢 袮 — which `data/` may not fold and a search
    may, because a result is an offer of candidates rather than a claim about
    the page. Folding *both* ends rather than only the query is what keeps the
    places the site prints the other form — the Chinese preface, 458's 更顯著,
    814 and 817's 彀, 105 and 109's 妳 — findable, by either spelling. Nothing
    stored moved.
11. ~~**The TOC** (`en/002`, `zh/002`)~~ Done, and cheap as advertised. It is
    not a table: the ranges it prints are exactly what the hymns already say,
    so §4's tree computes them and the two pages became a check instead. All
    eighteen sections agree in both editions, and the nine subheadings the
    pages expand agree too — which is the only independent confirmation the 84
    supplement hymns' sections have, those having rested on the Chinese
    subject index alone. It turned up the Chinese contents page printing its
    eighteenth range against no heading at all, and — by way of one subject
    name that looked like an index-against-page disagreement and was not —
    **D17**, which is not small.

**What is next.** Three things are open and each is a different size. **D17**'s
orthography is corrected; what remains of it — 你 for 祢 across 557 files — is
a reading pass and the largest single correction left in `data/`, and it is now
the only part of D18 still standing.
**D7** is done: the Chinese edition's meter is recorded on the 43 hymns where
it is not the English one's, and the 64 hymns still reported are the hymnal's
own — 56 a lineation question, and eight the report should keep making.
**D19** is done: 386 lines corrected across 145 hymns in eight classes, and
`check-punctuation` now asserts that each edition of the hymnal is written with
its own. **D21** is done on top of it: 28 hymns now say which lines they sing
twice, the decks sing them, and `check-repeats` holds the hymnal's three
statements of a repeat together. **D16** is the largest, a two-edition transcription of the page
annotations, and it is what would finally settle what the notes inherited from `data.yml` are. Also still open and unchanged: **D8**, item 9's argument
for carrying the front and back matter in `scan/`. **D17** would want it too:
the Chinese subject index is one of its witnesses and is not in this
repository.
