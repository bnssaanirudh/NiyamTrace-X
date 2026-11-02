# Verification — 28 October 2026

The author-supplied PDF and ZIP are preserved exactly. The supplied PDF matches `paper/current/main.pdf` byte for byte. The LaTeX static audit finds 29 cited bibliography keys, 29 bibliography entries, no undefined citations or cross-reference labels, and no missing figure dependencies.

## Retained-record reproduction

The following checks were executed against the curated publication evidence:

1. `Analysis/reproduce_results.py`: checks the curated member hashes, recomputes frozen and paired findings, verifies native and known-candidate synthetic snapshots/traces, checks public-intent counts, and verifies the archived source-test XML counts.
2. `Analysis/reproduce_history.py`: verifies historical source hashes and recomputes the retained symbolic, metamorphic, broker, stateful, open-weight, and diagnostic summaries.
3. `verify_ntx24b.py`: checks ZIP integrity and recomputes the 1,920 retained NTX-24B method rows across 16 model/parser/arm groups and their language slices.

Machine-readable outputs are in [verification/](verification/). The source snapshot, old test report, and model outputs remain historical artifacts. No fresh language-model inference, application-test suite run, deployment test, parser rerun through the native gateway, or production security repair was performed.

## Publication integrity

The evidence archive's `SHA256.json` covers its curated member files. Repository-relative paths, sizes, SHA-256 digests, and Git blob hashes for this publication addition are recorded in [PUBLICATION_MANIFEST.csv](PUBLICATION_MANIFEST.csv). The manifest excludes itself.

The publication selection omits two unreported private-cohort aggregate files. The native/control case files included in the evidence archive each contain 48 author-generated controlled fixtures. Scientific members were not rewritten or redacted. Prefix-based credential screening, corrected to avoid `task-` identifier false positives, found no matches in the selected text artifacts. This is a bounded scan, not proof of absence of every possible sensitive value.

## Remaining scientific limitations

Reference verdicts, reference effects, and native commits use different cohorts and model configurations. Their denominators remain separate. The native request-polarity failure, four authorized NTX-24B families per model, generated-template dependence, missing independent human gold, and missing official gate-in-path external evaluation remain explicit limitations.
