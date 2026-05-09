#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

import sys
sys.path.insert(0, str(SCRIPTS))

from benchmark_lib import median, percentile, summarize_micro, summarize_symfony  # noqa: E402


class BenchmarkAnalysisTests(unittest.TestCase):
    def test_median_and_percentile(self) -> None:
        self.assertAlmostEqual(median([1, 3, 2]), 2.0)
        self.assertAlmostEqual(median([1, 2, 3, 4]), 2.5)
        self.assertAlmostEqual(percentile([1, 2, 3, 4, 5], 95.0), 5.0)

    def test_micro_summary(self) -> None:
        summary = summarize_micro(
            [
                {"benchmark": "scalar_args", "variant": "baseline", "ns_per_op": "10"},
                {"benchmark": "scalar_args", "variant": "baseline", "ns_per_op": "12"},
                {"benchmark": "scalar_args", "variant": "with_ext", "ns_per_op": "15"},
                {"benchmark": "scalar_args", "variant": "with_ext", "ns_per_op": "18"},
            ]
        )
        self.assertEqual(len(summary), 1)
        self.assertAlmostEqual(float(summary[0]["baseline_median_ns_op"]), 11.0)
        self.assertAlmostEqual(float(summary[0]["with_ext_median_ns_op"]), 16.5)
        self.assertAlmostEqual(float(summary[0]["slowdown_percent"]), 50.0)

    def test_symfony_summary(self) -> None:
        summary = summarize_symfony(
            [
                {"endpoint": "/", "concurrency": "4", "variant": "baseline", "rps": "200", "latency_median_ms": "6", "latency_p95_ms": "10", "latency_max_ms": "20", "error_rate": "0"},
                {"endpoint": "/", "concurrency": "4", "variant": "baseline", "rps": "180", "latency_median_ms": "7", "latency_p95_ms": "12", "latency_max_ms": "25", "error_rate": "0"},
                {"endpoint": "/", "concurrency": "4", "variant": "with_ext", "rps": "150", "latency_median_ms": "8", "latency_p95_ms": "15", "latency_max_ms": "30", "error_rate": "0"},
                {"endpoint": "/", "concurrency": "4", "variant": "with_ext", "rps": "140", "latency_median_ms": "9", "latency_p95_ms": "18", "latency_max_ms": "35", "error_rate": "0"},
            ]
        )
        self.assertEqual(len(summary), 1)
        self.assertAlmostEqual(float(summary[0]["baseline_rps"]), 190.0)
        self.assertAlmostEqual(float(summary[0]["with_ext_rps"]), 145.0)
        self.assertAlmostEqual(float(summary[0]["throughput_drop_percent"]), 23.6842105263, places=4)

    def test_cli_summary_generation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ext-bench-test-") as td:
            tmp = Path(td)
            raw = tmp / "raw"
            raw.mkdir(parents=True, exist_ok=True)

            (raw / "micro.csv").write_text(
                "benchmark,variant,iterations,total_ns,ns_per_op,repetition\n"
                "control_loop,baseline,1000,1000,1,1\n"
                "control_loop,with_ext,1000,2000,2,1\n",
                encoding="utf-8",
            )
            (raw / "symfony.csv").write_text(
                "endpoint,concurrency,variant,repetition,rps,latency_median_ms,latency_p95_ms,latency_max_ms,error_rate\n"
                "/,1,baseline,1,100,5,8,11,0\n"
                "/,1,with_ext,1,80,6,10,15,0\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                ["python3", str(SCRIPTS / "summarize_results.py"), str(tmp)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            summary_json = tmp / "summary.json"
            summary_md = tmp / "summary.md"
            self.assertTrue(summary_json.is_file())
            self.assertTrue(summary_md.is_file())

            data = json.loads(summary_json.read_text(encoding="utf-8"))
            self.assertIn("slowdown_percent", data["micro"][0])
            self.assertIn("throughput_drop_percent", data["symfony"][0])
            self.assertIn("# Benchmark Summary", summary_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
