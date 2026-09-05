#!/usr/bin/env python3
"""Link the scanned pages into an already rendered site.

`pixi run build` does this itself at the end of the parallel build. This is the
same step for the serial `quarto render`, which knows nothing about `scan/`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hymn_projection.scans import stage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path("site"))
    parser.add_argument("--scans", type=Path, default=Path("scan"))
    parser.add_argument("--output-dir", default="_site")
    arguments = parser.parse_args()
    output = arguments.project / arguments.output_dir
    if not output.is_dir():
        raise SystemExit(f"{output} does not exist; render the site first")
    print(f"Staged {stage(arguments.scans, output)} scanned pages", flush=True)


if __name__ == "__main__":
    main()
