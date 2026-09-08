#!/usr/bin/env python3
"""Check that every lyric line is written with the marks the hymnal sets.

The two editions are set in different typography and `data/` holds both in one
file, so this reads each line against its own edition's alphabet: Han and the
Chinese marks, or Latin and the English ones. It also states the rule the
re-lineations were done under and nothing until now wrote down -- a closing
mark stays with the line it closes -- and checks that quotation marks pair off.

See `src/hymn_projection/punctuation.py` for what each rule is a statement
about, and in particular for why the English is not normalised toward ASCII.
This is a gate, not a report: every one of these was wrong somewhere in `data/`
before the check existed, and none is now.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hymn_projection.converter import numbered_markdown_files
from hymn_projection.punctuation import findings, read


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=Path("data"))
    parser.add_argument("--kinds", action="store_true",
                        help="count the findings by kind instead of listing them")
    arguments = parser.parse_args()

    files = numbered_markdown_files(arguments.data)
    found = findings([read(path) for path in files])
    if arguments.kinds:
        kinds: dict[str, list[int]] = {}
        for finding in found:
            kinds.setdefault(finding.kind, []).append(finding.number)
        for kind, numbers in sorted(kinds.items(), key=lambda item: -len(item[1])):
            print(f"{len(numbers):>4} in {len(set(numbers)):>3} hymns  {kind}")
    else:
        for finding in found:
            print(f"{finding.number:>3}  {finding.kind}\n     {finding.detail}")
    if found:
        print(f"\n{len(found)} findings in {len(files)} hymns")
        raise SystemExit(1)
    print(f"check-punctuation: all {len(files)} hymns are written "
          "with the marks the hymnal sets")


if __name__ == "__main__":
    main()
