"""
scripts/run_variance_test.py -- Suggestion #9: Inter-run Variance Analysis

Runs the same N queries K times against the current LLM backend.
Reports per-query verdict stability to separate genuine cross-lingual
divergence from model stochasticity.

Usage:
    python scripts/run_variance_test.py --runs 3 --limit 20
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

SCENARIOS_PATH = Path("data/benchmark/scenarios_x.json")


def load_scenarios(limit: int) -> list[dict]:
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    # Pick a stratified sample: first scenario from each perturbation × language
    seen = set()
    selected = []
    for s in scenarios:
        key = (s["language"], s["tags"][0])
        if key not in seen:
            seen.add(key)
            selected.append(s)
        if len(selected) >= limit:
            break
    return selected


def run_single(scenario: dict) -> str:
    """Run one scenario through the pipeline. Returns the gate verdict."""
    from packages.nlp.intake import MultilingualIntake
    from packages.nlp.compiler import NiyamCompiler

    intake = MultilingualIntake()
    compiler = NiyamCompiler()

    intake_result = intake.process(scenario["raw_text"])
    result = compiler.compile(
        actor_id=scenario.get("actor_id", "U-1"),
        actor_role=scenario.get("actor_role", "procurement_manager"),
        raw_text=scenario["raw_text"],
        intake_result=intake_result,
    )

    if result.contract is None:
        if result.clarification_prompt:
            return "CLARIFY"
        return "BLOCK"
    return "ALLOW"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3, help="Number of repeated runs per query")
    parser.add_argument("--limit", type=int, default=20, help="Number of distinct scenarios")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  NiyamTrace-X Inter-Run Variance Test  (#{args.runs} runs)")
    print(f"{'='*55}\n")

    scenarios = load_scenarios(args.limit)
    print(f"Loaded {len(scenarios)} stratified scenarios\n")

    # verdict_map: scenario_id -> list of verdicts across runs
    verdict_map: dict[str, list[str]] = defaultdict(list)

    for run_idx in range(args.runs):
        print(f"--- Run {run_idx + 1}/{args.runs} ---")
        for s in scenarios:
            try:
                t0 = time.perf_counter()
                verdict = run_single(s)
                ms = (time.perf_counter() - t0) * 1000
                verdict_map[s["scenario_id"]].append(verdict)
                status = "✓" if verdict == s["expected_verdict"] else "✗"
                print(f"  {status} {s['scenario_id'][:45]:45s} {verdict:8s} {ms:.0f}ms")
            except Exception as e:
                verdict_map[s["scenario_id"]].append("ERROR")
                print(f"  ! {s['scenario_id'][:45]:45s} ERROR: {e}")
        print()

    # Stability analysis
    stable = 0
    unstable = []
    for sid, verdicts in verdict_map.items():
        if len(set(verdicts)) == 1:
            stable += 1
        else:
            unstable.append({"scenario_id": sid, "verdicts": verdicts})

    total = len(verdict_map)
    stability_rate = stable / total if total > 0 else 0

    print(f"\n{'='*55}")
    print(f"  Stability Rate : {stability_rate*100:.1f}% ({stable}/{total} queries stable)")
    print(f"  Unstable Queries: {len(unstable)}")
    print(f"{'='*55}")

    if unstable:
        print("\n  Unstable scenarios (stochastic model variance):")
        for u in unstable:
            print(f"    {u['scenario_id']}: {u['verdicts']}")

    # Save report
    report = {
        "runs": args.runs,
        "scenarios": total,
        "stability_rate": stability_rate,
        "stable_count": stable,
        "unstable_queries": unstable,
    }
    out = Path("data/benchmark/variance_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n  Report -> {out}")


if __name__ == "__main__":
    main()
