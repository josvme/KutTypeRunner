#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from benchmark_lib import (
    format_micro_markdown,
    format_symfony_markdown,
    read_csv_assoc,
    summarize_micro,
    summarize_symfony,
)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/summarize_results.py <results_dir>", file=sys.stderr)
        return 1

    results_dir = Path(sys.argv[1]).resolve()
    raw_dir = results_dir / "raw"

    micro_records = read_csv_assoc(raw_dir / "micro.csv")
    symfony_records = read_csv_assoc(raw_dir / "symfony.csv")

    micro_summary = summarize_micro(micro_records)
    symfony_summary = summarize_symfony(symfony_records)

    summary = {"micro": micro_summary, "symfony": symfony_summary}
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Benchmark Summary",
        "",
        "## Micro-Benchmarks",
        "",
        format_micro_markdown(micro_summary).rstrip(),
        "",
        "## Symfony Benchmark",
        "",
        format_symfony_markdown(symfony_summary).rstrip(),
        "",
        "## Notes",
        "- Slowdown formula: `(with_ext / baseline) - 1`",
        "- Throughput drop formula: `1 - (with_ext_rps / baseline_rps)`",
    ]
    (results_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {results_dir}/summary.json and {results_dir}/summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
