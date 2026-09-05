"""Stream hymns between one YAML sequence, numbered Markdown files and the site."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from pathlib import Path

import yaml

from .environment import PRODUCTION, available_cpu_count, build_mode
from .model import Hymn
from .pages import Collection, to_markdown as page_markdown
from .scans import missing_images, read_editions
from .slides import (
    LINES_PER_SLIDE,
    chorus_report_markdown,
    to_markdown as slide_markdown,
)


# The projection writes into a Quarto project and takes the one thing it cannot
# work out -- where `data/` is browsable -- from that project's configuration,
# rather than repeating a repository URL that has already been renamed once.
SOURCE_REPO = "source-repo"
# What each projection writes, relative to the Quarto project.
SLIDE_DIRECTORY = "slide"
PAGE_DIRECTORY = "hymn"


def hymns_from_yaml(path: Path) -> Iterator[Hymn]:
    """Yield validated hymns from a YAML sequence."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a list")
    for number, value in enumerate(data, start=1):
        try:
            yield Hymn.from_dict(value)
        except ValueError as error:
            raise ValueError(f"{path}: hymn {number}: {error}") from error


def write_yaml(hymns: Iterable[Hymn], path: Path) -> None:
    """Write hymns as the canonical YAML sequence."""

    data = [hymn.to_dict() for hymn in hymns]
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def numbered_markdown_files(directory: Path) -> list[Path]:
    """Return N.md files in order, rejecting non-numeric names and gaps."""

    files = list(directory.glob("*.md"))
    if not files:
        # Every caller goes on to describe the collection as a whole -- its
        # range, its choruses -- and would otherwise fail somewhere further in,
        # naming anything but the directory that was empty.
        raise ValueError(f"no N.md files in {directory}")
    if any(not path.stem.isdecimal() for path in files):
        raise ValueError(f"all Markdown files in {directory} must be named N.md")
    files.sort(key=lambda path: int(path.stem))
    numbers = [int(path.stem) for path in files]
    if numbers != list(range(1, len(files) + 1)):
        raise ValueError(f"Markdown file numbering in {directory} must start at 1 without gaps")
    return files


def hymns_from_markdown(directory: Path) -> Iterator[Hymn]:
    """Yield validated hymns from a numbered Markdown directory."""

    for path in numbered_markdown_files(directory):
        try:
            yield Hymn.from_markdown(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ValueError(f"{path}: {error}") from error


def yaml_to_markdown(source: Path, destination: Path) -> None:
    """Write a YAML sequence as numbered Markdown documents."""

    destination.mkdir(parents=True, exist_ok=True)
    for number, hymn in enumerate(hymns_from_yaml(source), start=1):
        (destination / f"{number}.md").write_text(hymn.to_markdown(), encoding="utf-8")


def markdown_to_yaml(source: Path, destination: Path) -> None:
    """Rebuild a YAML sequence from numbered Markdown documents."""

    write_yaml(hymns_from_markdown(source), destination)


def source_repository(project: Path) -> str:
    """Return where `data/N.md` is browsable, from the Quarto configuration.

    A page that shows a typo has to send the reader to the file the typo can be
    fixed in. That is `data/N.md` and never the Markdown the page was rendered
    from, which this module generates and git ignores.
    """

    config_path = project / "_quarto.yml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    url = config.get(SOURCE_REPO) if isinstance(config, dict) else None
    if not isinstance(url, str) or not url:
        raise ValueError(f"{config_path} must set {SOURCE_REPO} to a URL")
    return url.rstrip("/")


def _projection(
    path: Path, limit: int, collection: Collection
) -> tuple[int, Hymn, str, str]:
    """Read one hymn and project it both ways, independently of the others."""

    number = int(path.stem)
    try:
        hymn = Hymn.from_markdown(path.read_text(encoding="utf-8"))
        slides = slide_markdown(hymn, number, limit)
        page = page_markdown(hymn, number, collection)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return number, hymn, slides, page


def _replace_directory(directory: Path, written: dict[int, str]) -> None:
    """Write one projection's files and remove whatever it no longer writes.

    A hymn that leaves `data/` must leave here too. Both renders glob these
    directories, so a file left behind would go on being published while the
    landing page, which knows the collection's range, refused to link to it.
    """

    directory.mkdir(parents=True, exist_ok=True)
    for number, text in written.items():
        (directory / f"{number}.md").write_text(text, encoding="utf-8")
    keep = {f"{number}.md" for number in written}
    for stale in directory.glob("*.md"):
        if stale.name not in keep:
            stale.unlink()


def markdown_to_site(
    source: Path,
    destination: Path,
    scans: Path,
    limit: int = LINES_PER_SLIDE,
    jobs: int | None = None,
) -> None:
    """Write both of each hymn's projections into the Quarto project.

    One pass over `data/` produces the deck a hymn is sung from and the page it
    is proofread on, from the same parsed `Hymn`. Neither can therefore carry a
    word the other does not.
    """

    mode = build_mode()
    destination.mkdir(parents=True, exist_ok=True)
    files = numbered_markdown_files(source)
    editions = read_editions(scans)
    absent = missing_images(editions, scans)
    if absent:
        raise ValueError(
            f"{len(absent)} scanned page(s) named by {scans} are missing, "
            f"beginning with {absent[0]}"
        )
    collection = Collection(
        editions=editions,
        source_url=source_repository(destination) + "/" + source.name,
        highest=len(files),
    )
    if jobs is not None and jobs < 1:
        raise ValueError("jobs must be at least 1")
    workers = min(jobs or available_cpu_count(), len(files))
    hymn_noun = "hymn" if len(files) == 1 else "hymns"
    worker_noun = "worker" if workers == 1 else "workers"
    print(
        f"Projecting {len(files)} {hymn_noun} as decks and pages with "
        f"{workers} concurrent Pandoc {worker_noun}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=workers) as executor:
        projections = list(
            executor.map(_projection, files, repeat(limit), repeat(collection))
        )

    entries = [(number, hymn) for number, hymn, _, _ in projections]
    _replace_directory(
        destination / SLIDE_DIRECTORY,
        {number: slides for number, _, slides, _ in projections},
    )
    _replace_directory(
        destination / PAGE_DIRECTORY,
        {number: page for number, _, _, page in projections},
    )
    # This developer report sits beside the two projections, not inside either.
    # Production omits both its source and anything a stopped render may have
    # left beside that source; other modes write it with the slides so it
    # cannot drift from what they sing.
    report = destination / "chorus.md"
    if mode == PRODUCTION:
        report.unlink(missing_ok=True)
        report.with_suffix(".html").unlink(missing_ok=True)
    else:
        report.write_text(chorus_report_markdown(entries), encoding="utf-8")


def main() -> None:
    """Run one conversion direction from the command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "direction",
        choices=("yaml-to-markdown", "markdown-to-yaml", "markdown-to-site"),
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--scans",
        type=Path,
        default=Path("scan"),
        help="the scanned editions and their page intervals (markdown-to-site)",
    )
    parser.add_argument(
        "--lines-per-slide",
        type=int,
        default=LINES_PER_SLIDE,
        help="lyric lines a slide holds before a stanza is divided",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=available_cpu_count(),
        help="concurrent Pandoc workers (default: all usable CPU cores)",
    )
    arguments = parser.parse_args()
    if arguments.jobs < 1:
        parser.error("--jobs must be at least 1")

    if arguments.direction == "yaml-to-markdown":
        yaml_to_markdown(arguments.source, arguments.destination)
    elif arguments.direction == "markdown-to-yaml":
        markdown_to_yaml(arguments.source, arguments.destination)
    else:
        markdown_to_site(
            arguments.source,
            arguments.destination,
            arguments.scans,
            arguments.lines_per_slide,
            arguments.jobs,
        )


if __name__ == "__main__":
    main()
