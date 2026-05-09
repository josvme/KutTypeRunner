#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


def read_csv_assoc(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def median(values: Iterable[float]) -> float:
    data = sorted(float(v) for v in values)
    if not data:
        return 0.0
    n = len(data)
    mid = n // 2
    if n % 2 == 1:
        return data[mid]
    return (data[mid - 1] + data[mid]) / 2.0


def percentile(values: Iterable[float], p: float) -> float:
    data = sorted(float(v) for v in values)
    if not data:
        return 0.0
    if len(data) == 1:
        return data[0]
    rank = int(-(-((p / 100.0) * len(data)) // 1))
    idx = max(0, min(rank - 1, len(data) - 1))
    return data[idx]


def summarize_micro(records: List[Dict[str, str]]) -> List[Dict[str, float | str]]:
    grouped: Dict[str, Dict[str, List[float]]] = {}
    for row in records:
        benchmark = row.get("benchmark", "unknown")
        variant = row.get("variant", "unknown")
        value = float(row.get("ns_per_op", 0.0) or 0.0)
        grouped.setdefault(benchmark, {}).setdefault(variant, []).append(value)

    out: List[Dict[str, float | str]] = []
    for benchmark, variants in grouped.items():
        baseline = variants.get("baseline", [])
        with_ext = variants.get("with_ext", [])
        if not baseline or not with_ext:
            continue

        baseline_median = median(baseline)
        with_ext_median = median(with_ext)
        slowdown = ((with_ext_median / baseline_median) - 1.0) if baseline_median > 0 else 0.0

        out.append(
            {
                "benchmark": benchmark,
                "baseline_median_ns_op": baseline_median,
                "baseline_p95_ns_op": percentile(baseline, 95.0),
                "with_ext_median_ns_op": with_ext_median,
                "with_ext_p95_ns_op": percentile(with_ext, 95.0),
                "slowdown_percent": slowdown * 100.0,
                "absolute_delta_ns_op": with_ext_median - baseline_median,
            }
        )

    return sorted(out, key=lambda row: str(row["benchmark"]))


def summarize_symfony(records: List[Dict[str, str]]) -> List[Dict[str, float | str]]:
    grouped: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    for row in records:
        endpoint = row.get("endpoint", "/")
        concurrency = row.get("concurrency", "1")
        variant = row.get("variant", "unknown")
        key = f"{endpoint} @c{concurrency}"

        slot = grouped.setdefault(key, {}).setdefault(
            variant,
            {"rps": [], "p50": [], "p95": [], "max": [], "error_rate": []},
        )
        slot["rps"].append(float(row.get("rps", 0.0) or 0.0))
        slot["p50"].append(float(row.get("latency_median_ms", 0.0) or 0.0))
        slot["p95"].append(float(row.get("latency_p95_ms", 0.0) or 0.0))
        slot["max"].append(float(row.get("latency_max_ms", 0.0) or 0.0))
        slot["error_rate"].append(float(row.get("error_rate", 0.0) or 0.0))

    out: List[Dict[str, float | str]] = []
    for scenario, variants in grouped.items():
        baseline = variants.get("baseline")
        with_ext = variants.get("with_ext")
        if not baseline or not with_ext:
            continue

        baseline_rps = median(baseline["rps"])
        with_ext_rps = median(with_ext["rps"])
        throughput_drop = ((1.0 - (with_ext_rps / baseline_rps)) * 100.0) if baseline_rps > 0 else 0.0

        baseline_p95 = median(baseline["p95"])
        with_ext_p95 = median(with_ext["p95"])
        latency_slowdown = (((with_ext_p95 / baseline_p95) - 1.0) * 100.0) if baseline_p95 > 0 else 0.0

        out.append(
            {
                "scenario": scenario,
                "baseline_rps": baseline_rps,
                "with_ext_rps": with_ext_rps,
                "throughput_drop_percent": throughput_drop,
                "baseline_p95_ms": baseline_p95,
                "with_ext_p95_ms": with_ext_p95,
                "latency_slowdown_percent": latency_slowdown,
                "baseline_error_rate": median(baseline["error_rate"]),
                "with_ext_error_rate": median(with_ext["error_rate"]),
            }
        )

    return sorted(out, key=lambda row: str(row["scenario"]))


def format_micro_markdown(rows: List[Dict[str, float | str]]) -> str:
    if not rows:
        return "No micro-benchmark results found.\n"

    lines = [
        "| Benchmark | Baseline median (ns/op) | With ext median (ns/op) | Slowdown % | Delta (ns/op) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {benchmark} | {baseline:.2f} | {with_ext:.2f} | {slowdown:.2f} | {delta:.2f} |".format(
                benchmark=row["benchmark"],
                baseline=float(row["baseline_median_ns_op"]),
                with_ext=float(row["with_ext_median_ns_op"]),
                slowdown=float(row["slowdown_percent"]),
                delta=float(row["absolute_delta_ns_op"]),
            )
        )
    return "\n".join(lines) + "\n"


def format_symfony_markdown(rows: List[Dict[str, float | str]]) -> str:
    if not rows:
        return "No Symfony benchmark results found (skipped or missing).\n"

    lines = [
        "| Scenario | Baseline rps | With ext rps | Throughput drop % | Baseline p95 (ms) | With ext p95 (ms) | Latency slowdown % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {scenario} | {baseline_rps:.2f} | {with_ext_rps:.2f} | {drop:.2f} | {baseline_p95:.2f} | {with_ext_p95:.2f} | {slowdown:.2f} |".format(
                scenario=row["scenario"],
                baseline_rps=float(row["baseline_rps"]),
                with_ext_rps=float(row["with_ext_rps"]),
                drop=float(row["throughput_drop_percent"]),
                baseline_p95=float(row["baseline_p95_ms"]),
                with_ext_p95=float(row["with_ext_p95_ms"]),
                slowdown=float(row["latency_slowdown_percent"]),
            )
        )
    return "\n".join(lines) + "\n"
