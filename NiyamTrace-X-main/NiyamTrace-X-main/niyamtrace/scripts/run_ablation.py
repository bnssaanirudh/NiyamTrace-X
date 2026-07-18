"""
scripts/run_ablation.py -- Suggestion #16: Leave-one-in Stage Ablation

Tests which pipeline stage contributes the most safety recovery.
For each ablation config, runs the 20-scenario benchmark and reports accuracy.

Ablation configs (leave-one-in):
  - only_llm          : LLM extraction only, no TypeChecker, no EntityLinker
  - llm_typechecker   : LLM + TypeChecker only
  - llm_entitylinker  : LLM + EntityLinker only (skip TypeChecker)
  - full              : Full NiyamCompiler (baseline)

Usage:
    python scripts/run_ablation.py --limit 20
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

SCENARIOS_PATH = Path("data/benchmark/scenarios_x.json")


def load_scenarios(limit: int) -> list[dict]:
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    return scenarios[:limit]


def run_scenario_ablated(scenario: dict, mode: str) -> tuple[str, float]:
    """
    Run one scenario with a subset of compiler stages enabled.
    mode: 'only_llm' | 'llm_typechecker' | 'llm_entitylinker' | 'full'
    Returns (verdict, latency_ms).
    """
    from packages.nlp.intake import MultilingualIntake
    from packages.nlp.compiler import NiyamCompiler, CandidateIntent

    intake = MultilingualIntake()
    intake_result = intake.process(scenario["raw_text"])

    compiler = NiyamCompiler()
    t0 = time.perf_counter()

    try:
        candidate = compiler._extract_candidate(intake_result.normalized_text)
    except Exception as e:
        return "BLOCK", (time.perf_counter() - t0) * 1000

    if mode == "only_llm":
        # Trust LLM directly, skip all checks
        verdict = "ALLOW" if candidate.intent != "unknown" else "BLOCK"

    elif mode == "llm_typechecker":
        ok, _, _ = compiler._type_check(candidate)
        verdict = "BLOCK" if not ok else "ALLOW"

    elif mode == "llm_entitylinker":
        # Skip TypeChecker, run EntityLinker only
        ok, _, _, clarify = compiler._entity_link(candidate)
        if not ok:
            verdict = "CLARIFY" if clarify else "BLOCK"
        else:
            verdict = "ALLOW"

    else:  # full
        result = compiler.compile(
            actor_id=scenario.get("actor_id", "U-1"),
            actor_role=scenario.get("actor_role", "procurement_manager"),
            raw_text=scenario["raw_text"],
            intake_result=intake_result,
        )
        if result.contract is None:
            verdict = "CLARIFY" if result.clarification_prompt else "BLOCK"
        else:
            verdict = "ALLOW"

    ms = (time.perf_counter() - t0) * 1000
    return verdict, ms


def run_ablation(scenarios: list[dict], mode: str) -> dict:
    correct = 0
    total = len(scenarios)
    total_ms = 0.0

    for s in scenarios:
        verdict, ms = run_scenario_ablated(s, mode)
        total_ms += ms
        if verdict == s["expected_verdict"]:
            correct += 1

    return {
        "mode": mode,
        "accuracy": correct / total if total > 0 else 0,
        "correct": correct,
        "total": total,
        "avg_latency_ms": total_ms / total if total > 0 else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  NiyamTrace-X Stage Ablation Study  (n={args.limit})")
    print(f"{'='*60}\n")

    scenarios = load_scenarios(args.limit)
    modes = ["only_llm", "llm_typechecker", "llm_entitylinker", "full"]
    results = []

    for mode in modes:
        print(f"  Running mode: {mode}...")
        r = run_ablation(scenarios, mode)
        results.append(r)
        print(f"    Accuracy: {r['accuracy']*100:.1f}%  ({r['correct']}/{r['total']})  "
              f"avg {r['avg_latency_ms']:.0f}ms")

    print(f"\n{'='*60}")
    print(f"  {'Mode':<22} {'Accuracy':>10}  {'Correct':>8}  {'Latency':>10}")
    print(f"  {'-'*54}")
    for r in results:
        flag = " <- baseline" if r["mode"] == "full" else ""
        print(f"  {r['mode']:<22} {r['accuracy']*100:>9.1f}%  {r['correct']:>6}/{r['total']:<5}  "
              f"{r['avg_latency_ms']:>7.0f}ms{flag}")

    best = max(results, key=lambda x: x["accuracy"])
    print(f"\n  Most impactful stage: {best['mode']} ({best['accuracy']*100:.1f}%)")
    print(f"{'='*60}\n")

    out = Path("data/benchmark/ablation_report.json")
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Report -> {out}")


if __name__ == "__main__":
    main()
