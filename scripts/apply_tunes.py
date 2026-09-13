#!/usr/bin/env python3
"""Propagate `data/tunes.tsv` into the tune of every `data/N.md`.

A preprocessing step, not part of the site build: `data/N.md` stays the
authority everything else is built from, and this only fills in the tune the
book's two indexes of tunes name, which no page prints over the hymn itself.
Run it after editing the table; run it with `--check` to prove the two agree.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hymn_projection.converter import numbered_markdown_files
from hymn_projection.tunes import apply, read_tunes, rewrites


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", type=Path, default=Path("data"))
    parser.add_argument(
        "--table",
        type=Path,
        default=None,
        help="the tunes to apply (default: tunes.tsv beside the hymns)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change and exit non-zero, writing nothing",
    )
    parser.add_argument("-j", "--jobs", type=int, default=None)
    arguments = parser.parse_args()

    table = arguments.table or arguments.data / "tunes.tsv"
    try:
        tunes = read_tunes(table)
        files = numbered_markdown_files(arguments.data)
        if arguments.check:
            stale = [path for path, _ in rewrites(files, tunes, arguments.jobs)]
        else:
            stale = apply(files, tunes, arguments.jobs)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    noun = "hymn" if len(stale) == 1 else "hymns"
    rows = sum(len(names) for names in tunes.values())
    if arguments.check:
        if stale:
            raise SystemExit(
                f"{len(stale)} {noun} do not match {table}, "
                f"beginning with {stale[0]}"
            )
        print(f"All {len(files)} hymns match {table}", flush=True)
    else:
        print(
            f"{len(stale)} {noun} rewritten from {rows} rows of {table}",
            flush=True,
        )


if __name__ == "__main__":
    main()
