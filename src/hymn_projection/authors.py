"""Give each hymn the author and composer the English edition credits.

Most pages carry no name at all: a page has the subject, the meter, the number
and, on a copyrighted song, its copyright line, and who wrote the words and who
wrote the tune is in the back matter, in the *Index of Authors and Composers*,
``en/879``-``en/894``.

**A second printing, on the songs that are under copyright.** Those pages do
carry the credit, above the first staff, and in three layouts rather than one:
*split*, with the author on the left margin and the composer on the right;
*joint*, with one name on the right and nothing on the left; and *joint
stacked*, with two names on the right and nothing on the left. The right margin
therefore means the composer on a split page and the whole credit on a joint
one, and position alone does not say which. The index, having two columns to
fill, resolves a joint credit by writing it into both -- 110 of these rows have
the same name twice -- and this table keeps that convention, because it is the
book's own and because the alternative is a third representation for a hundred
hymns.

**Where the two printings disagree, this table is a reading of both.** It was a
transcription of the index alone until D15 compared the two; the fifteen rows
where they differ are settled by taking whichever printing carries more, which
is the index on ten of them and the page on the rest. On three the two name
different people, and there the note column says so rather than letting a
choice pass for a transcription. ``PLAN.md`` holds the full comparison.

**How the index was verified.** Every other table in ``data/`` had something to
check itself against -- the categories against the table of contents, the
titles against the index of first lines, the tunes against a second printed
index that lists the same relation. The index of authors is printed once. The
verification had to be built rather than found, and it was built out of four
things: the row structure comes from the extraction's bounding boxes, so the
hymn numbers are positional and cannot drift; the numbering was checked page
against page, each page's first hymn agreeing with the previous page's last;
the characters were read off the page images afterwards; and a name appearing
once that is a letter away from a name appearing often was looked at by eye.
That last check found five, of which four are the book's own inconsistencies --
``G. C. Martin`` beside ``W. C. Martin``, ``Williams G. Tomer`` beside
``William G. Tomer``, ``E. Mary Grimes`` beside ``E. May Grimes``, ``Thomas D.
Chisholm`` beside ``Thomas O. Chisholm`` -- and one a misreading, now fixed.

**Scope, which the hymn pages state.** The index covers hymns 1 to 764. The
supplement has none: the English back matter's supplement carries a table of
contents, a first-lines index, a subject index and the list of Chinese-only
hymns, and no authors. So these names are the English edition's, they stop at
764, and they are not localized -- the Chinese edition credits nobody.

**Two marks of the book's own, kept as printed.** A blank is not a gap in this
reading: the index heads itself *(Blanks indicate untraceable sources)*, so a
blank cell is the book saying it could not trace one. And ``†`` stands where an
author would be on 34 hymns; the legend is printed once, under the table on the
last page, and reads *(† indicates compiler)*. The hymnal's compiler wrote
those texts, and one row says so in words rather than by the mark -- hymn 473's
author is ``vv.2-5, compiler``.

Applying it is a preprocessing step over ``data/``, not part of building the
site, exactly as ``categories``, ``titles`` and ``tunes`` are.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from itertools import repeat
from pathlib import Path

from .environment import available_cpu_count
from .model import Hymn, LocalizedText


HEADER = ("hymn", "author", "composer", "note")
#: What the index prints where an author would be when its own compiler wrote
#: the text. The legend is on the last page of the index.
DAGGER = "†"
#: What the legend says the dagger means, which is also how the index words it
#: on the one row that spells it out instead of marking it -- hymn 473's author
#: is `vv.2-5, compiler`. The table keeps the page's mark; a hymn file gets the
#: word, because a dagger belongs to no script and `auto-lang` has nothing to
#: tag it as. The meter had the same problem and was given a mapping; here the
#: book supplies the wording itself, so there is no need to invent one.
COMPILER = "compiler"


def read_authors(path: Path) -> dict[int, tuple[str, str, str]]:
    """Read the hymn-to-credits table as (author, composer, note) per hymn.

    One row per hymn, blanks included, because that is the shape the page has:
    a row with two empty cells is the index saying it traced neither, which is
    not the same as the hymn being absent from the index. The note is blank on
    all but the three hymns whose two printings name different people, and it
    is the one cell here that is not read off a page.
    """

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or tuple(field.strip() for field in lines[0].split("\t")) != HEADER:
        raise ValueError(f"{path} must begin with the header {chr(9).join(HEADER)}")
    credits: dict[int, tuple[str, str, str]] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("\t")]
        if len(fields) != len(HEADER):
            raise ValueError(
                f"{path}: line {line_number} is not {len(HEADER)} fields"
            )
        number, author, composer, note = fields
        if not number.isdecimal():
            raise ValueError(f"{path}: line {line_number} is not numbered by a hymn")
        if int(number) in credits:
            raise ValueError(f"{path}: line {line_number} names hymn {number} twice")
        if note and not (author or composer):
            raise ValueError(
                f"{path}: line {line_number} annotates a credit it does not give"
            )
        credits[int(number)] = (author, composer, note)
    if sorted(credits) != list(credits):
        raise ValueError(f"{path} must be in hymn order")
    return credits


def write_authors(credits: Mapping[int, tuple[str, str, str]], path: Path) -> None:
    """Write the table, for regenerating it rather than editing it by hand."""

    body = "".join(
        "\t".join((str(number),) + tuple(credits[number])) + "\n"
        for number in sorted(credits)
    )
    path.write_text("\t".join(HEADER) + "\n" + body, encoding="utf-8")


def credited(hymn: Hymn, names: tuple[str, str, str] | None) -> Hymn:
    """Return the hymn credited to these names, or to none where it has none.

    The three cells are independent: the index traces one credit and not the
    other often enough -- 60 hymns have no author, 56 no composer -- that a
    blank in either has to clear that field alone, and the note is cleared the
    same way, so that deleting it from the table takes it back out of the hymn.
    """

    author, composer, note = names or ("", "", "")
    if author == DAGGER:
        author = COMPILER
    return replace(
        hymn,
        author=LocalizedText({"en": author}) if author else None,
        composer=LocalizedText({"en": composer}) if composer else None,
        credit_note=LocalizedText({"en": note}) if note else None,
    )


def _recredit(
    path: Path, credits: Mapping[int, tuple[str, str, str]]
) -> tuple[Path, str, str]:
    """Return one hymn's file and its text before and after."""

    source = path.read_text(encoding="utf-8")
    try:
        hymn = Hymn.from_markdown(source)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return path, source, credited(hymn, credits.get(int(path.stem))).to_markdown()


def rewrites(
    files: Iterable[Path],
    credits: Mapping[int, tuple[str, str, str]],
    jobs: int | None = None,
) -> list[tuple[Path, str]]:
    """Return the files whose text the table changes, with their new text.

    Every row has to name a hymn that exists, so a row cannot go stale
    unnoticed; a hymn the table skips -- every one of the 84 in the supplement
    -- has its credits removed rather than left behind, which is what makes a
    second run over the first run's output a no-op even after a row is deleted.
    """

    paths = list(files)
    if not paths:
        raise ValueError("no hymns to credit")
    numbers = {int(path.stem) for path in paths}
    unknown = sorted(set(credits) - numbers)
    if unknown:
        raise ValueError(
            f"{len(unknown)} row(s) name a hymn that is not there, "
            f"beginning with {unknown[0]}"
        )
    workers = min(jobs or available_cpu_count(), len(paths))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_recredit, paths, repeat(credits)))
    return [(path, text) for path, source, text in results if text != source]


def apply(
    files: Iterable[Path],
    credits: Mapping[int, tuple[str, str, str]],
    jobs: int | None = None,
) -> list[Path]:
    """Write each hymn's credits into its file; return the files that changed."""

    changed = rewrites(files, credits, jobs)
    for path, text in changed:
        path.write_text(text, encoding="utf-8")
    return [path for path, _ in changed]
