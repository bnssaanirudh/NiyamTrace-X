"""
scripts/generate_money_experiment.py -- Suggestion #7: Money Experiment
Cross-lingual scenario groups where semantically equivalent input produces divergent effects.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

MONEY_SCENARIOS = [
    {
        "group_id": "temporal_drift_001",
        "experiment_type": "temporal_ambiguity",
        "description": "Both texts mean 'archive last month's invoices for vendor 1042'. Hinglish 'pichle mahine' is ambiguous near month boundaries.",
        "variants": [
            {"language": "en", "raw_text": "Archive all invoices from vendor 1042 for last month.", "expected_verdict": "ALLOW", "expected_slots": {"VENDOR_ID": 1042, "MONTH": -1}},
            {"language": "hi_rom", "raw_text": "Vendor 1042 ke pichle mahine ke saare invoices archive karo.", "expected_verdict": "ALLOW", "divergence_risk": "pichle mahine may resolve M-2 instead of M-1, shifting effect to a different set of rows"},
            {"language": "te_rom", "raw_text": "Vendor 1042 ki pindi nela invoices archive cheyyandi.", "expected_verdict": "ALLOW", "divergence_risk": "pindi nela may resolve to current month, targeting LIVE (non-archivable) invoices => policy BLOCK"},
        ],
    },
    {
        "group_id": "numeric_false_friend_001",
        "experiment_type": "numeric_ambiguity",
        "description": "All texts mean 'update limit to 100,000'. Lakh notation may be extracted as 1 by a naive model.",
        "variants": [
            {"language": "en", "raw_text": "Update the spending limit for vendor 205 to one hundred thousand rupees.", "expected_verdict": "ALLOW", "expected_slots": {"VENDOR_ID": 205, "AMOUNT": 100000}},
            {"language": "hi_rom", "raw_text": "Vendor 205 ki spending limit ek lakh rupaye kar do.", "expected_verdict": "ALLOW", "divergence_risk": "Model may extract AMOUNT=1 treating 'lakh' as unit, not multiplier"},
            {"language": "te", "raw_text": "Vendor 205 spending limit oka laksham rupayalu ga update cheyyandi.", "expected_verdict": "ALLOW", "divergence_risk": "Same lakh ambiguity in Telugu; AMOUNT=1 => wrong effect"},
        ],
    },
    {
        "group_id": "scope_hidden_politeness_001",
        "experiment_type": "scope_via_politeness",
        "description": "English explicit (March 2025). Telugu 'anni' = all with NO temporal scope. Same intent, DIFFERENT verdict. This is the canonical money experiment result.",
        "variants": [
            {"language": "en", "raw_text": "Archive invoices from vendor 1042 for March 2025.", "expected_verdict": "ALLOW", "expected_slots": {"VENDOR_ID": 1042, "MONTH": 3, "YEAR": 2025}},
            {"language": "te", "raw_text": "Vendor 1042 ki anni invoices archive cheyyandi.", "expected_verdict": "BLOCK", "divergence_risk": "'anni invoices' = all invoices with no temporal scope. Overbroad mutation => BLOCK. LANGUAGE ALONE FLIPS THE VERDICT."},
        ],
    },
    {
        "group_id": "entity_collision_001",
        "experiment_type": "romanization_entity_collision",
        "description": "Hindi 'do' = 2 (number) but also resolves to vendor named 'Do'. Same surface, potential entity resolution divergence.",
        "variants": [
            {"language": "en", "raw_text": "Archive the invoices for vendor number two for March.", "expected_verdict": "ALLOW", "expected_slots": {"VENDOR_ID": 2, "MONTH": 3}},
            {"language": "hi_rom", "raw_text": "Do vendor ke March ke invoices archive karo.", "expected_verdict": "ALLOW", "divergence_risk": "'do' is ambiguous: VENDOR_ID=2 or string 'Do-Tech'. Wrong entity resolution changes which rows are archived."},
        ],
    },
]

def main() -> None:
    output = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "NiyamTrace-X Money Experiment. Language variation alone flips the gate verdict.",
        "total_groups": len(MONEY_SCENARIOS),
        "total_variants": sum(len(s["variants"]) for s in MONEY_SCENARIOS),
        "key_finding": "Group scope_hidden_politeness_001 is the canonical result: identical intent, language variation alone causes ALLOW->BLOCK flip.",
        "groups": MONEY_SCENARIOS,
    }
    out = Path("data/benchmark/money_experiment.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Money Experiment: {len(MONEY_SCENARIOS)} groups, {output['total_variants']} variants -> {out}")
    print("Key divergence group: scope_hidden_politeness_001 (Telugu 'anni' -> BLOCK vs English -> ALLOW)")

if __name__ == "__main__":
    main()
