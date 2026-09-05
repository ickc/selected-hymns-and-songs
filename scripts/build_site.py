#!/usr/bin/env python3
"""Render the hymn decks and pages in parallel without sharing project state.

Quarto can render one file or directory at a time, but a website render also
writes project-wide files such as ``search.json``, ``index.html`` and
``site_libs``. Concurrent renders in the source project therefore race even
when their input documents are disjoint.

Each worker here gets an isolated copy of the project containing only its
share of ``slide/*.md`` and ``hymn/*.md``. A hymn's deck and its page go to the
same worker: they are two renders of one hymn, and keeping them together makes
a worker's share one contiguous idea rather than two independent partitions.

The resulting sites are combined after every Quarto process succeeds, including
one merged search index. The scanned pages are linked in at the end by
``scans.stage``, which keeps 45 MB of PNG out of every worker's copy.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import filecmp
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Sequence

import yaml

from hymn_projection.environment import (
    DEVELOP,
    PRODUCTION,
    available_cpu_count,
    build_mode,
)
from hymn_projection.scans import stage


# The two projected directories, each rendered to its own format. A worker is
# given one share of the hymns and both projections of it.
PROJECTIONS = ("slide", "hymn")

IGNORED_PROJECT_ENTRIES = {
    ".quarto",
    "_site",
    "site_libs",
    *PROJECTIONS,
    # A stopped Quarto render can leave these generated pages beside their
    # Markdown sources. They must not become input resources in a later build.
    "index.html",
    "chorus.html",
}


def _positive_integer(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _partition(numbers: Sequence[int], jobs: int) -> list[list[int]]:
    workers = min(jobs, len(numbers))
    return [list(numbers[index::workers]) for index in range(workers)]


def _copy_project(
    source: Path,
    destination: Path,
    numbers: Sequence[int],
    first: bool,
    mode: str,
) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = set(names) & IGNORED_PROJECT_ENTRIES
        if mode == PRODUCTION:
            ignored.add("chorus.md")
        return ignored

    shutil.copytree(source, destination, ignore=ignore)
    for projection in PROJECTIONS:
        directory = destination / projection
        directory.mkdir()
        for number in numbers:
            shutil.copy2(source / projection / f"{number}.md", directory / f"{number}.md")

    config_path = destination / "_quarto.yml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    targets = [f"{projection}/*.md" for projection in PROJECTIONS]
    if first:
        targets.insert(0, "index.md")
        if mode == DEVELOP:
            targets.insert(1, "chorus.md")
    config["project"]["render"] = targets
    config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def _render(worker: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["quarto", "render", str(worker), "--quiet"],
        capture_output=True,
        text=True,
        check=False,
    )


def _read_search(path: Path) -> list[dict[str, Any]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"{path} does not contain a JSON array")
    return entries


def _copy_without_project_files(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if relative in {Path("index.html"), Path("search.json")}:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not filecmp.cmp(path, target, shallow=False):
                raise RuntimeError(f"workers produced different versions of {relative}")
        else:
            shutil.copy2(path, target)


def _merge(worker_outputs: Sequence[Path], destination: Path) -> int:
    shutil.copytree(worker_outputs[0], destination)
    search_entries = _read_search(worker_outputs[0] / "search.json")

    for output in worker_outputs[1:]:
        search_entries.extend(_read_search(output / "search.json"))
        _copy_without_project_files(output, destination)

    # Workers own disjoint documents, so duplicate IDs indicate a bad
    # partition or an unexpected Quarto output rather than something to hide.
    object_ids = [entry.get("objectID") for entry in search_entries]
    if not all(isinstance(object_id, str) for object_id in object_ids):
        raise RuntimeError("worker search index contains an invalid object ID")
    if len(object_ids) != len(set(object_ids)):
        raise RuntimeError("worker search indexes contain duplicate object IDs")
    if any(str(entry.get("href", "")).startswith("chorus.html") for entry in search_entries):
        raise RuntimeError("the developer-only chorus report entered the search index")

    # Make the merge deterministic: documents follow the lexical expansion of
    # the render globs, while entries within a document remain in slide order.
    by_document: dict[str, list[dict[str, Any]]] = {}
    for entry in search_entries:
        document = str(entry.get("href", "")).split("#", 1)[0]
        by_document.setdefault(document, []).append(entry)
    search_entries = [
        entry for document in sorted(by_document) for entry in by_document[document]
    ]
    (destination / "search.json").write_text(
        json.dumps(search_entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(search_entries)


def _hymn_numbers(project: Path) -> list[int]:
    """Return the hymns both projections have written Markdown for."""

    written = {
        projection: {int(path.stem) for path in (project / projection).glob("*.md")}
        for projection in PROJECTIONS
    }
    for projection, numbers in written.items():
        if not numbers:
            raise RuntimeError(f"no hymn Markdown found in {project / projection}")
    # One projection lagging the other is a half-finished `md-to-site`, and
    # would publish a page linking to a deck that is not there.
    first, second = PROJECTIONS
    if written[first] != written[second]:
        difference = written[first] ^ written[second]
        raise RuntimeError(
            f"{first}/ and {second}/ describe different hymns: "
            f"{sorted(difference)[:5]}"
        )
    return sorted(written[first])


def build(project: Path, jobs: int) -> None:
    project = project.resolve()
    mode = build_mode()
    slides = _hymn_numbers(project)

    partitions = _partition(slides, jobs)
    started = time.monotonic()
    process_count = len(partitions)
    noun = "process" if process_count == 1 else "processes"
    available_cores = available_cpu_count()
    print(f"Build mode: {mode}", flush=True)
    print(f"Detected {available_cores} usable CPU cores", flush=True)
    print(
        f"Rendering {len(slides)} hymn decks and pages with "
        f"{process_count} Quarto {noun}",
        flush=True,
    )

    with tempfile.TemporaryDirectory(prefix=".quarto-build-", dir=project.parent) as temporary:
        temporary_path = Path(temporary)
        preparation_started = time.monotonic()
        workers: list[Path] = []
        for index, partition in enumerate(partitions):
            worker = temporary_path / f"worker-{index + 1}"
            _copy_project(project, worker, partition, first=index == 0, mode=mode)
            workers.append(worker)
        print(
            f"Prepared {len(workers)} isolated projects in "
            f"{time.monotonic() - preparation_started:.1f}s",
            flush=True,
        )

        render_started = time.monotonic()
        failures: list[tuple[int, subprocess.CompletedProcess[str]]] = []
        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            futures = {
                executor.submit(_render, worker): index
                for index, worker in enumerate(workers)
            }
            for future in as_completed(futures):
                index = futures[future]
                result = future.result()
                if result.returncode:
                    failures.append((index, result))
                else:
                    print(f"  worker {index + 1}/{len(workers)} finished", flush=True)
                    if result.stdout or result.stderr:
                        print(result.stdout, end="", flush=True)
                        print(result.stderr, end="", flush=True)

        if failures:
            for index, result in sorted(failures):
                print(f"\nworker {index + 1} failed:")
                print(result.stdout, end="")
                print(result.stderr, end="")
            raise RuntimeError(f"{len(failures)} Quarto worker(s) failed")
        print(
            f"Rendered worker projects in {time.monotonic() - render_started:.1f}s",
            flush=True,
        )

        merge_started = time.monotonic()
        combined = temporary_path / "combined"
        search_count = _merge([worker / "_site" for worker in workers], combined)
        for projection in PROJECTIONS:
            rendered = len(list((combined / projection).glob("*.html")))
            if rendered != len(slides):
                raise RuntimeError(
                    f"rendered {rendered} of {len(slides)} documents in {projection}/"
                )
        chorus_exists = (combined / "chorus.html").exists()
        if chorus_exists != (mode == DEVELOP):
            raise RuntimeError(f"chorus.html does not match {mode} build mode")

        output = project / "_site"
        if output.exists():
            shutil.rmtree(output)
        combined.replace(output)
        print(f"Merged worker output in {time.monotonic() - merge_started:.1f}s", flush=True)

    # After the output is in place, and outside the Quarto project throughout:
    # the scans are files to publish, not documents to render.
    staged = stage(project.parent / "scan", output)

    elapsed = time.monotonic() - started
    print(
        f"Built {len(slides)} decks and pages, {staged} scanned pages and "
        f"{search_count} search entries in {elapsed:.1f}s",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path("site"))
    parser.add_argument(
        "-j",
        "--jobs",
        type=_positive_integer,
        default=available_cpu_count(),
        help="parallel Quarto processes (default: all usable CPU cores)",
    )
    arguments = parser.parse_args()
    build(arguments.project, arguments.jobs)


if __name__ == "__main__":
    main()
