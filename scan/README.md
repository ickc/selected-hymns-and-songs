# The scanned hymnal

The authoritative artefact. `data/` is a transcription of these pages, so when
the two disagree the page is right and the transcription is the thing to fix.
That is what `hymn/N.html` puts side by side.

## What is here

`en/N.png` and `zh/N.png` — one image per **PDF page** of the language edition,
`N` being the one-based page number of that edition. Only the pages some hymn
occupies are carried: the front matter and the post-hymn matter are not, so the
numbering has gaps at both ends and nowhere else.

`en.csv` and `zh.csv` — `segment,start_page,end_page`, both bounds inclusive
and one-based. Segment 0 is the front matter, 1–848 are the hymns, and 849 is
the post-hymn matter. Two things about this file decide how a page is shown:

- **An absent hymn has both bounds empty.** `778,,` says hymn 778 is not in
  that edition — 39 hymns are missing from the English one, none from the
  Chinese. Empty means absent, never unknown.
- **Consecutive hymns may share a page.** `41,15,15` before `42,15,16` says
  hymn 42 begins below hymn 41 on page 15. A page is therefore shown whole,
  with its neighbours on it, rather than cropped to one hymn.

The rows for segments 0 and 849 are kept even though their pages are not, so
the file stays the same file that
[`selected-hymns-and-songs-pdf`](https://github.com/ickc/selected-hymns-and-songs-pdf)
generates and can be replaced from it wholesale.

## Where it came from

`pixi run extract-en-page-images` / `extract-zh-page-images` in that project,
which decodes the single CCITT image embedded in each PDF page directly to PNG
— no rendering, no resampling, no DPI choice — and rotates the landscape
rasters a lossless quarter turn upright. The result is 1062×1676, one bit per
pixel, about 25 KB a page. `infer-hymn-pages` in the same project produces the
two CSVs; its `DEVELOPER.md` explains how the boundaries are inferred and what
was checked by hand.

These files are copied in rather than generated here. They change only when
that project re-derives them, which is why they are carried in git: the site
build must not depend on a private working copy being checked out beside it.
