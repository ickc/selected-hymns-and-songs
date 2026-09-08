#!/usr/bin/env python
"""Fail if the hymnal's three statements of a repeat do not agree."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hymn_projection.repeats import findings, read  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="the directory of hymn Markdown")
    parser.add_argument(
        "--kinds", action="store_true", help="count the findings rather than list them"
    )
    arguments = parser.parse_args()

    paths = sorted(arguments.directory.glob("[0-9]*.md"), key=lambda p: int(p.stem))
    hymns = [read(path) for path in paths]
    found = findings(hymns)
    if not found:
        print(
            f"check-repeats: all {len(hymns)} hymns agree with themselves "
            "about what is sung twice"
        )
        return 0
    if arguments.kinds:
        for kind, count in Counter(finding.kind for finding in found).most_common():
            print(f"{count:4}  {kind}")
    else:
        for finding in found:
            print(f"{finding.number:4}  {finding.kind}: {finding.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
