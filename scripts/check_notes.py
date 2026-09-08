#!/usr/bin/env python3
"""Check the hymnal's own prose about a hymn against the hymn.

`data/` keeps two kinds of prose apart by where it puts them: a direction, which
governs how the hymn is sung, sits in the front matter under `note`; a gloss,
which is a word about a word of the hymn, stays in the lyric line as `^[...]`.
See `src/hymn_projection/notes.py` for why, and what the pages print.

Both say something that can be checked against the hymn: the word a gloss
quotes has to be in the line it hangs off, the stanza it names has to be the
stanza it sits in, a note about what the English edition lacks has to agree
with the stanzas `data/` holds, and a hymn cannot both be told to repeat its
last line and have written the repeat out. This is a gate, not a report: every
one of these was wrong somewhere before the check existed, and none is now.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hymn_projection.converter import numbered_markdown_files
from hymn_projection.notes import findings, read


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=Path("data"))
    arguments = parser.parse_args()

    files = numbered_markdown_files(arguments.data)
    found = findings([read(path) for path in files])
    for finding in found:
        print(f"{finding.number:>3}  {finding.kind}\n     {finding.detail}")
    if found:
        print(f"\n{len(found)} findings in {len(files)} hymns")
        raise SystemExit(1)
    print(f"check-notes: the prose of all {len(files)} hymns agrees with the hymns")


if __name__ == "__main__":
    main()
