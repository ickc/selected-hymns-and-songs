import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from hymn_projection.environment import _linux_physical_cores, available_cpu_count
from scripts.build_site import _hymn_numbers, _merge, _partition


CPUINFO = """\
processor: 0
physical id: 0
core id: 0

processor: 1
physical id: 0
core id: 0

processor: 2
physical id: 0
core id: 1

processor: 3
physical id: 0
core id: 1
"""


class CpuCountTest(TestCase):
    def test_linux_threads_are_counted_as_one_physical_core(self) -> None:
        self.assertEqual(_linux_physical_cores(CPUINFO), 2)

    def test_linux_count_obeys_the_process_cpu_affinity(self) -> None:
        self.assertEqual(_linux_physical_cores(CPUINFO, {0, 1}), 1)

    def test_virtual_machine_uses_every_allocated_vcpu(self) -> None:
        virtual_cpuinfo = CPUINFO.replace("processor: 0", "processor: 0\nflags: hypervisor")
        with (
            patch("hymn_projection.environment.sys.platform", "linux"),
            patch(
                "hymn_projection.environment.os.sched_getaffinity",
                return_value={0, 1, 2, 3},
            ),
            patch(
                "hymn_projection.environment.Path.read_text",
                return_value=virtual_cpuinfo,
            ),
        ):
            self.assertEqual(available_cpu_count(), 4)


class PartitionTest(TestCase):
    def test_every_hymn_belongs_to_one_balanced_worker(self) -> None:
        hymns = list(range(1, 9))

        partitions = _partition(hymns, 3)

        self.assertEqual([len(partition) for partition in partitions], [3, 3, 2])
        self.assertCountEqual(
            [number for partition in partitions for number in partition], hymns
        )


class ProjectionTest(TestCase):
    """A worker renders one hymn twice, so it needs both projections of it."""

    def _project(self, root: Path, slides: list[int], pages: list[int]) -> None:
        for name, numbers in (("slide", slides), ("hymn", pages)):
            (root / name).mkdir(parents=True)
            for number in numbers:
                (root / name / f"{number}.md").write_text("", encoding="utf-8")

    def test_both_projections_describe_the_same_hymns(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project(root, [1, 2, 3], [1, 2, 3])

            self.assertEqual(_hymn_numbers(root), [1, 2, 3])

    def test_one_projection_lagging_the_other_is_an_error(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            # A half-finished `md-to-site` would otherwise publish a page
            # linking to a deck that was never rendered.
            self._project(root, [1, 2, 3], [1, 2])

            with self.assertRaisesRegex(RuntimeError, r"different hymns.*\[3\]"):
                _hymn_numbers(root)


class MergeTest(TestCase):
    def test_search_indexes_and_disjoint_decks_are_combined(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            outputs = [root / "worker-1", root / "worker-2"]
            for output in outputs:
                (output / "slide").mkdir(parents=True)
                (output / "site_libs").mkdir()
                (output / "site_libs" / "shared.js").write_text("same", encoding="utf-8")
            (outputs[0] / "index.html").write_text("real index", encoding="utf-8")
            (outputs[1] / "index.html").write_text("worker redirect", encoding="utf-8")
            (outputs[0] / "slide" / "1.html").write_text("one", encoding="utf-8")
            (outputs[1] / "slide" / "2.html").write_text("two", encoding="utf-8")
            (outputs[0] / "search.json").write_text(
                json.dumps(
                    [
                        {"objectID": "slide/1.html#v2", "href": "slide/1.html#v2"},
                        {"objectID": "slide/1.html#v10", "href": "slide/1.html#v10"},
                    ]
                ),
                encoding="utf-8",
            )
            (outputs[1] / "search.json").write_text(
                json.dumps([{"objectID": "slide/2.html#v1", "href": "slide/2.html#v1"}]),
                encoding="utf-8",
            )

            destination = root / "combined"
            count = _merge(outputs, destination)

            self.assertEqual(count, 3)
            self.assertEqual((destination / "index.html").read_text(), "real index")
            self.assertTrue((destination / "slide" / "1.html").is_file())
            self.assertTrue((destination / "slide" / "2.html").is_file())
            entries = json.loads((destination / "search.json").read_text())
            self.assertEqual(
                [entry["objectID"] for entry in entries],
                ["slide/1.html#v2", "slide/1.html#v10", "slide/2.html#v1"],
            )

    def test_the_chorus_report_cannot_enter_the_merged_search(self) -> None:
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "worker"
            output.mkdir()
            (output / "index.html").write_text("index", encoding="utf-8")
            (output / "search.json").write_text(
                json.dumps([{"objectID": "chorus.html", "href": "chorus.html"}]),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "chorus report"):
                _merge([output], Path(temporary) / "combined")
