#!/usr/bin/env python3
"""Write `data/reverence.tsv` into `data/`, and hold `data/` to it.

The table is the part of the 你/祢 correction a person read off the page
images, because the Chinese edition's text layer would not say. Run it after
adding rows; run it with `--check` to prove the two agree -- which is what CI
runs, together with the two things that can be asserted about every hymn:
that a line printed twice spells its pronouns the same way both times, and
that the feminine 妳 stays in the two hymns it belongs to.

See `src/hymn_projection/reverence.py` for what each rule is a statement
about, and `scripts/reverence_witness.py` for the machine half of the pass.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hymn_projection.converter import numbered_markdown_files
from hymn_projection.reverence import apply, findings, read, read_ledger, rewrites


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=Path("data"))
    parser.add_argument("--table", type=Path, default=None,
                        help="the readings to apply (default: reverence.tsv beside the hymns)")
    parser.add_argument("--check", action="store_true",
                        help="report what would change and exit non-zero, writing nothing")
    arguments = parser.parse_args()

    table = arguments.table or arguments.data / "reverence.tsv"
    try:
        readings = read_ledger(table)
        files = numbered_markdown_files(arguments.data)
        if arguments.check:
            stale = [path for path, _ in rewrites(files, readings)]
        else:
            stale = apply(files, readings)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    noun = "hymn" if len(stale) == 1 else "hymns"
    if not arguments.check:
        print(f"{len(stale)} {noun} rewritten from {len(readings)} rows of {table}",
              flush=True)
        return

    found = findings([read(path) for path in files], readings)
    for finding in found:
        print(f"{finding.number:>3}  {finding.kind}\n     {finding.detail}")
    if stale:
        print(f"{len(stale)} {noun} do not match {table}, beginning with {stale[0]}")
    if found or stale:
        raise SystemExit(
            f"{len(found)} finding(s) and {len(stale)} {noun} that do not match the table"
        )
    print(f"check-reverence: all {len(files)} hymns agree with the {len(readings)} "
          "pronouns read off the pages, and with each other")


if __name__ == "__main__":
    main()
