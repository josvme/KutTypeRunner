#!/usr/bin/env python3
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

import sys
sys.path.insert(0, str(SCRIPTS))

from benchmark_lib import (  # noqa: E402
    format_micro_markdown,
    format_symfony_markdown,
    median,
    percentile,
    read_csv_assoc,
    summarize_micro,
    summarize_symfony,
)


class BenchmarkLibUnitTests(unittest.TestCase):
    def test_read_csv_assoc_returns_empty_for_missing_file(self) -> None:
        self.assertEqual(read_csv_assoc(Path("/tmp/does-not-exist.csv")), [])

    def test_read_csv_assoc_parses_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ext-bench-csv-") as td:
            path = Path(td) / "sample.csv"
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "value"])
                writer.writerow(["alpha", "1"])
                writer.writerow(["beta", "2"])

            rows = read_csv_assoc(path)

        self.assertEqual(rows, [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}])

    def test_median_and_percentile_edge_cases(self) -> None:
        self.assertAlmostEqual(median([]), 0.0)
        self.assertAlmostEqual(median([1, 3, 2]), 2.0)
        self.assertAlmostEqual(percentile([], 95.0), 0.0)
        self.assertAlmostEqual(percentile([7], 95.0), 7.0)
        self.assertAlmostEqual(percentile([1, 2, 3, 4, 5], 95.0), 5.0)

    def test_summarize_micro_skips_incomplete_variants(self) -> None:
        rows = summarize_micro(
            [
                {"benchmark": "a", "variant": "baseline", "ns_per_op": "10"},
                {"benchmark": "b", "variant": "with_ext", "ns_per_op": "12"},
                {"benchmark": "c", "variant": "baseline", "ns_per_op": "8"},
                {"benchmark": "c", "variant": "with_ext", "ns_per_op": "10"},
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["benchmark"], "c")
        self.assertAlmostEqual(float(rows[0]["slowdown_percent"]), 25.0)

    def test_summarize_symfony_uses_medians(self) -> None:
        rows = summarize_symfony(
            [
                {"endpoint": "/x", "concurrency": "2", "variant": "baseline", "rps": "220", "latency_median_ms": "5", "latency_p95_ms": "9", "latency_max_ms": "12", "error_rate": "0"},
                {"endpoint": "/x", "concurrency": "2", "variant": "baseline", "rps": "200", "latency_median_ms": "6", "latency_p95_ms": "10", "latency_max_ms": "15", "error_rate": "0"},
                {"endpoint": "/x", "concurrency": "2", "variant": "with_ext", "rps": "150", "latency_median_ms": "7", "latency_p95_ms": "12", "latency_max_ms": "18", "error_rate": "0"},
                {"endpoint": "/x", "concurrency": "2", "variant": "with_ext", "rps": "170", "latency_median_ms": "8", "latency_p95_ms": "14", "latency_max_ms": "20", "error_rate": "0"},
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["scenario"], "/x @c2")
        self.assertAlmostEqual(float(rows[0]["baseline_rps"]), 210.0)
        self.assertAlmostEqual(float(rows[0]["with_ext_rps"]), 160.0)
        self.assertAlmostEqual(float(rows[0]["throughput_drop_percent"]), 23.8095238095, places=4)

    def test_markdown_formatters_include_headers(self) -> None:
        micro = format_micro_markdown(
            [
                {
                    "benchmark": "control_loop",
                    "baseline_median_ns_op": 1.0,
                    "with_ext_median_ns_op": 2.0,
                    "slowdown_percent": 100.0,
                    "absolute_delta_ns_op": 1.0,
                }
            ]
        )
        symfony = format_symfony_markdown(
            [
                {
                    "scenario": "/ @c1",
                    "baseline_rps": 100.0,
                    "with_ext_rps": 90.0,
                    "throughput_drop_percent": 10.0,
                    "baseline_p95_ms": 8.0,
                    "with_ext_p95_ms": 9.0,
                    "latency_slowdown_percent": 12.5,
                }
            ]
        )

        self.assertIn("| Benchmark |", micro)
        self.assertIn("control_loop", micro)
        self.assertIn("| Scenario |", symfony)
        self.assertIn("/ @c1", symfony)


if __name__ == "__main__":
    unittest.main()
