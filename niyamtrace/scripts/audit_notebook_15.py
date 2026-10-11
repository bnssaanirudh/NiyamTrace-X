from pathlib import Path
import json
import hashlib
import pandas as pd
import numpy as np
from scipy.stats import binomtest
from statsmodels.stats.proportion import proportion_confint

KIT = Path(__file__).resolve().parent.parent.parent / "NiyamTraceX_Paper_Final_Validation_Kit"
OUT = KIT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

def dump(obj, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

P = KIT / "evidence" / "paired_variant_cases.csv"
meta = json.loads((KIT / "evidence" / "EVIDENCE_PROVENANCE.json").read_text(encoding="utf-8"))
assert sha(P) == meta["sha256"], f"Source data altered: {sha(P)} != {meta['sha256']}"

df = pd.read_csv(P, keep_default_na=False)
assert len(df) == 4320, f"Unexpected {len(df)} rows"

for f in ["safe_completion", "unsafe_case"]:
    df[f] = df[f].astype(str).str.lower().map({"true": True, "false": False})
df["correct"] = df["decision"] == df["expected"]
df["unauthorized_effects"] = pd.to_numeric(df["unauthorized_effects"], errors="raise")

# 1. Summary
rows = []
for (model, variant), g in df.groupby(["direction", "variant"]):
    a = g[g.expected == "ALLOW"]
    rows.append(dict(
        direction=model, variant=variant, n=len(g), correct=int(g.correct.sum()), accuracy=float(g.correct.mean()),
        allow_n=len(a), safe_completion_count=int(a.safe_completion.sum()), safe_completion_rate=float(a.safe_completion.mean()) if len(a) else None,
        unsafe_n=int(g.unsafe_case.sum()), unauthorized_rows=int(g.unauthorized_effects.sum()),
        unsafe_upper_95=float(proportion_confint(int(g.unsafe_case.sum()), len(g), alpha=0.05, method="beta")[1])
    ))
summary = pd.DataFrame(rows).sort_values(["direction", "variant"])
summary.to_csv(OUT / "15_full_cohort_summary.csv", index=False)
print("Cohort summary saved.")

# 2. Paired McNemar
paired = []
bad = []
for direction in sorted(df.direction.unique()):
    d = df[df.direction == direction]
    a = d[d.variant == "anchors"].set_index("id").sort_index()
    f = d[d.variant == "full"].set_index("id").sort_index()
    assert a.index.equals(f.index)
    diff = a.decision != f.decision
    b = int((a.correct & ~f.correct).sum())
    c = int((~a.correct & f.correct).sum())
    mc = binomtest(min(b, c), n=b + c, p=0.5, alternative="two-sided").pvalue if b + c else 1.0
    paired.append(dict(
        direction=direction, n=len(a), divergent_decisions=int(diff.sum()), anchor_only_correct=b, full_only_correct=c, exact_mcnemar_p=mc,
        anchor_accuracy=float(a.correct.mean()), full_accuracy=float(f.correct.mean()), delta_full_minus_anchor=float(f.correct.mean() - a.correct.mean())
    ))
    comp = pd.DataFrame({
        "id": a.index, "group": a.group.values, "language": a.language.values, "kind": a.kind.values, "expected": a.expected.values,
        "anchor": a.decision.values, "full": f.decision.values, "anchor_correct": a.correct.values, "full_correct": f.correct.values,
        "anchor_reason": a.reason.values, "full_reason": f.reason.values, "anchor_safe_completion": a.safe_completion.values, "full_safe_completion": f.safe_completion.values
    })
    bad.append(comp.loc[diff.to_numpy()].assign(direction=direction))

paired = pd.DataFrame(paired)
regressions = pd.concat(bad, ignore_index=True)
paired.to_csv(OUT / "15_paired_significance.csv", index=False)
regressions.to_csv(OUT / "15_regression_case_ids.csv", index=False)
assert len(regressions.query("direction == 'granite_primary'")) == 48
assert len(regressions.query("direction == 'qwen_primary'")) == 0
p_val = paired.loc[paired.direction == "granite_primary", "exact_mcnemar_p"].values[0]
print(f"Granite regressions verified: {len(regressions)} cases. Paired McNemar p: {p_val}")

# 3. Cluster bootstrap
rng = np.random.default_rng(20261011)
boot = []
for direction in sorted(df.direction.unique()):
    a = df.query('direction == @direction and variant == "anchors"').set_index("id").sort_index()
    f = df.query('direction == @direction and variant == "full"').set_index("id").sort_index()
    v = pd.DataFrame({"group": a.group, "delta": f.correct.astype(int) - a.correct.astype(int)})
    means = v.groupby("group")["delta"].mean().to_numpy()
    draws = rng.choice(means, size=(5000, len(means)), replace=True).mean(axis=1)
    boot.append({
        "direction": direction, "n_groups": len(means), "delta_point": float(v.delta.mean()),
        "cluster_bootstrap_low": float(np.quantile(draws, 0.025)), "cluster_bootstrap_high": float(np.quantile(draws, 0.975))
    })
bt = pd.DataFrame(boot)
bt.to_csv(OUT / "15_cluster_bootstrap.csv", index=False)
print("Cluster bootstrap saved.")

# 4. Manifest
report = {
    "source_archive": meta["source_archive"],
    "source_sha256": meta["sha256"],
    "n_case_rows": len(df),
    "paired": paired.to_dict("records"),
    "cluster_bootstrap": bt.to_dict("records"),
    "granite_regression_count": 48,
    "cannot_claim": [
        "independent candidate superiority",
        "production safety",
        "human-labeled multilingual generalization"
    ],
    "conclusion": "Full method does not outperform anchors in October 11 cohort; Granite degrades. Regressions require investigation rather than exclusion."
}
dump(report, OUT / "15_AUDIT_MANIFEST.json")
print("Prompt C complete. Manifest saved successfully.")
