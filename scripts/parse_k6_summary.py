#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def metric_field(metrics: dict, metric_name: str, field: str, default: float = 0.0) -> float:
    metric = metrics.get(metric_name, {})
    if not isinstance(metric, dict):
        return default

    # k6 summary structure differs by version:
    # - older: metrics.<name>.values.<field>
    # - newer: metrics.<name>.<field>
    values = metric.get("values")
    if isinstance(values, dict) and field in values:
        value = values.get(field, default)
    else:
        value = metric.get(field, default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/parse_k6_summary.py <k6_summary.json>", file=sys.stderr)
        return 1

    summary_path = Path(sys.argv[1])
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    metrics = data.get("metrics", {})

    reqs = metric_field(metrics, "http_reqs", "rate")
    med = metric_field(metrics, "http_req_duration", "med")
    p95 = metric_field(metrics, "http_req_duration", "p(95)")
    maxv = metric_field(metrics, "http_req_duration", "max")
    err = metric_field(metrics, "http_req_failed", "value")

    print(f"{reqs},{med},{p95},{maxv},{err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
