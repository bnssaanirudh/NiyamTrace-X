# NiyamTrace-Bench — Annotated Scenario Dataset

**Status: STUB — Week 8**

This directory will contain:

- `scenarios/` — 80 canonical scenarios × 4 language forms = 320 paired runs
- `guidelines/` — Annotation guidelines for human-reviewed gold contracts
- `gold_contracts/` — Human-approved gold contract JSONs
- `policies/` — Policy bundles used per scenario
- `workspace_states/` — ERP snapshots for each scenario

## Scenario Categories (to be built in Week 8)

1. Read authorization
2. Bounded write
3. Multi-principal data
4. Deletion/tombstone
5. Cross-lingual variants
6. Conversational carryover
7. Untrusted evidence (prompt-injection-style)
8. Ambiguity

## Language Forms per Canonical Scenario

- English
- Hinglish
- Hindi
- Tamil
- Kannada
- Telugu script
- Romanized Telugu

> [!IMPORTANT]
> Do NOT inflate this dataset with machine-translated-only data.
> Flag anything not reviewed by a language-proficient annotator.
> Numbers only appear after the annotation pipeline has run.
