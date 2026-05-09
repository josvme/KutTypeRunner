#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


class ScriptsIntegrationTests(unittest.TestCase):
    def test_summarize_results_generates_summary_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ext-bench-int-") as td:
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
            self.assertEqual(len(data["micro"]), 1)
            self.assertEqual(len(data["symfony"]), 1)
            self.assertIn("slowdown_percent", data["micro"][0])
            self.assertIn("throughput_drop_percent", data["symfony"][0])
            self.assertIn("# Benchmark Summary", summary_md.read_text(encoding="utf-8"))

    def test_summarize_results_requires_path_argument(self) -> None:
        proc = subprocess.run(
            ["python3", str(SCRIPTS / "summarize_results.py")],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(proc.returncode, 1)
        self.assertIn("Usage:", proc.stderr)

    def test_parse_k6_summary_supports_values_style(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ext-k6-values-") as td:
            path = Path(td) / "summary.json"
            path.write_text(
                json.dumps(
                    {
                        "metrics": {
                            "http_reqs": {"values": {"rate": 123.4}},
                            "http_req_duration": {"values": {"med": 7.8, "p(95)": 12.3, "max": 20.5}},
                            "http_req_failed": {"values": {"value": 0.01}},
                        }
                    }
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                ["python3", str(SCRIPTS / "parse_k6_summary.py"), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stdout.strip(), "123.4,7.8,12.3,20.5,0.01")

    def test_parse_k6_summary_supports_flat_style(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ext-k6-flat-") as td:
            path = Path(td) / "summary.json"
            path.write_text(
                json.dumps(
                    {
                        "metrics": {
                            "http_reqs": {"rate": 99},
                            "http_req_duration": {"med": 6, "p(95)": 9, "max": 14},
                            "http_req_failed": {"value": 0},
                        }
                    }
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                ["python3", str(SCRIPTS / "parse_k6_summary.py"), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stdout.strip(), "99.0,6.0,9.0,14.0,0.0")


if __name__ == "__main__":
    unittest.main()
