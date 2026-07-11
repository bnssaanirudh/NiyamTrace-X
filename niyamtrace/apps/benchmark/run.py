"""
apps/benchmark/run.py — NiyamTrace-Bench CLI entry point (Week 8).

Usage:
    python -m apps.benchmark.run
    python -m apps.benchmark.run --scenarios data/benchmark/scenarios.json
    python -m apps.benchmark.run --threshold 0.85 --out data/benchmark
    python -m apps.benchmark.run --quiet

Exit codes:
    0   — all scenarios passed or accuracy ≥ threshold
    1   — accuracy < threshold (CI gate failure)
    2   — unexpected error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Force UTF-8 stdout to handle Telugu/Hindi characters on Windows cmd
sys.stdout.reconfigure(encoding='utf-8')

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="niyamtrace-bench",
        description="NiyamTrace-Bench: offline, deterministic benchmark runner",
    )
    parser.add_argument(
        "--scenarios",
        default=None,
        help="Path to scenarios.json (default: data/benchmark/scenarios.json)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory for reports (default: data/benchmark/)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Minimum accuracy threshold (default: 0.80). Exit 1 if below.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-scenario output",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of scenarios to run",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Write JSON report only (skip HTML)",
    )
    args = parser.parse_args()

    try:
        from packages.bench.runner import BenchmarkRunner
        from packages.bench.report import BenchmarkReport

        print("\n========================================")
        print("       NiyamTrace-Bench (Week 8)      ")
        print("========================================\n")

        runner = BenchmarkRunner(
            scenarios_path=args.scenarios,
            verbose=not args.quiet,
        )
        result = runner.run(limit=args.limit)

        s = result.summary
        report = BenchmarkReport(result, output_dir=args.out)
        json_path = report.write_json()
        print(f"\n  -> JSON report: {json_path}")

        if not args.json_only:
            html_path = report.write_html()
            print(f"  -> HTML report: {html_path}")

        # Summary banner
        print(f"\n{'-' * 46}")
        print(f"  Accuracy  : {s.accuracy * 100:.1f}%  ({s.passed}/{s.total})")
        print(f"  Threshold : {args.threshold * 100:.0f}%")
        print(f"  Latency   : {s.avg_latency_ms:.1f} ms avg")
        print(f"  ALLOW     : {s.allow_correct}/{s.allow_total}")
        print(f"  BLOCK     : {s.block_correct}/{s.block_total}")
        print(f"  ESCALATE  : {s.escalate_correct}/{s.escalate_total}")
        print(f"{'-' * 46}")

        if s.accuracy < args.threshold:
            print(f"\n  [FAIL] BENCH GATE FAILED - accuracy {s.accuracy * 100:.1f}% < {args.threshold * 100:.0f}%\n")
            return 1
        else:
            print(f"\n  [PASS] BENCH GATE PASSED - accuracy {s.accuracy * 100:.1f}% >= {args.threshold * 100:.0f}%\n")
            return 0

    except Exception as exc:
        print(f"\n  ERROR: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
