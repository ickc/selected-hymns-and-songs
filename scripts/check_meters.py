#!/usr/bin/env python3
"""Report every hymn whose Chinese lyrics do not scan as its meter says.

The meter over a hymn is a syllable count, and Chinese is one syllable to the
character, so it can be counted rather than trusted. A disagreement is a
finding either way round: a missing character in the lyrics, or a meter that
was mistyped on the way into `data/`.

A report, not a gate: 128 hymns still disagree and the hymnal's pages have to
settle them one at a time. On 89 of the 108 that are hymns 1-764 the meter is
confirmed by the book's own metrical index, so what disagrees is the text. `--strict` turns it into a gate for when they do.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hymn_projection.converter import numbered_markdown_files
from hymn_projection.meters import chorus_disagreements, disagreements, read, shape


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=Path("data"))
    parser.add_argument(
        "--kind", help="report only disagreements of this kind (substring match)"
    )
    parser.add_argument(
        "--strict", action="store_true", help="exit non-zero if any hymn disagrees"
    )
    parser.add_argument(
        "--shape",
        action="store_true",
        help="print every hymn's line lengths, chorus included, and stop",
    )
    arguments = parser.parse_args()

    files = numbered_markdown_files(arguments.data)
    if arguments.shape:
        for number, hymn in (read(path) for path in files):
            for name, counts in shape(hymn):
                lengths = ".".join(str(count) for count in counts)
                print(f"{number:>3}  {str(name):>8}  {lengths}")
        return

    found = disagreements(read(path) for path in files)
    if arguments.kind:
        found = [d for d in found if arguments.kind in d.kind]

    kinds: dict[str, int] = {}
    for disagreement in found:
        kinds[disagreement.kind] = kinds.get(disagreement.kind, 0) + 1
        expected = (
            ".".join(str(c) for c in disagreement.expected)
            if disagreement.expected
            else "-"
        )
        print(
            f"{disagreement.number:>3}  {disagreement.kind}\n"
            f"     meter {disagreement.meter!r} expects {expected}; "
            f"the lyrics imply {disagreement.implied or 'no single meter'}"
        )
        for name, counts in disagreement.stanzas:
            if counts != disagreement.expected:
                print(f"     stanza {name}: {'.'.join(str(c) for c in counts)}")

    choruses = chorus_disagreements(read(path) for path in files)
    for finding in choruses:
        printed = "  ".join(
            f"{name} {'.'.join(str(count) for count in counts)}"
            for name, counts in finding.choruses
        )
        print(f"{finding.number:>3}  choruses do not scan alike\n     {printed}")

    print(f"\n{len(found)} of {len(files)} hymns disagree with their meter")
    for kind, count in sorted(kinds.items(), key=lambda item: -item[1]):
        print(f"  {count:>4}  {kind}")
    print(f"{len(choruses)} of {len(files)} hymns have choruses that do not scan alike")
    if arguments.strict and (found or choruses):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
