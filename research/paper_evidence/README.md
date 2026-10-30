# Evidence for the current manuscript

The [reproducibility ZIP](NiyamTraceX_Manuscript_Evidence_2026-10-28.zip) contains the retained records and analysis used to audit the manuscript's frozen, paired, native, control, and historical findings. It preserves the scientific member bytes from `NTX_Papers_Redrafted_2026-10-13_FIXED.zip`; two aggregate files for an unreported private cohort are omitted, and the package-wide hash manifest is regenerated for the curated contents.

## Contents

| Directory inside the ZIP | Evidence |
|---|---|
| `Reproducibility/Frozen/` | 2,000 gold requests and 2,000 saved outputs per large checkpoint |
| `Reproducibility/Paired/` | 4,320 method rows from 720 model-request pairs, paired proposals, and statistics |
| `Reproducibility/Native_Controlled/` | 48 author-generated cases, live Qwen/Granite records, traces, policies, source fingerprints, and synthetic database snapshots |
| `Reproducibility/Controlled_Candidate_Preflight/` | Known-candidate execution control and synthetic snapshots |
| `Reproducibility/Source/` | Evaluated application source snapshot; not an assertion of equivalence to a later branch head |
| `Reproducibility/Historical/` | Symbolic, metamorphic, broker, 152-request open-weight, uncertainty, stateful, and diagnostic records |
| `Reproducibility/External/` | Public-intent job metadata and retained model outputs; original dataset releases remain the source of dataset text |
| `Data/` | Derived case-level metrics and result tables |
| `Analysis/` | Standard-library reproduction scripts and an archived Colab verification notebook |
| `Audit/` | Historical provenance and evidence-selection records |
| `SHA256.json` | SHA-256 of every curated member |

The archive's `Controlled_Candidate_Preflight/cases_PRIVATE.json` is a historical filename for 48 **author-generated controlled** fixtures, not participant requests. Cohort labels were checked before inclusion. Unreported participant-cohort aggregate files, private participant requests, and private NB21/NB22 originals are excluded from this publication package.

## Run the audit

From the repository root:

```bash
python -m zipfile -e research/paper_evidence/NiyamTraceX_Manuscript_Evidence_2026-10-28.zip reproduced_evidence
python -X utf8 reproduced_evidence/Analysis/reproduce_results.py
python -X utf8 reproduced_evidence/Analysis/reproduce_history.py
python -X utf8 research/paper_evidence/verify_ntx24b.py
```

The first two scripts verify hashes and recompute retained-record findings, including synthetic before/after effects. The third recomputes the NTX-24B model/parser/arm counts from the existing [NTX-24B result archive](../../results/NTX24B_results.zip).

No command above runs model inference, exercises a live enterprise connector, repairs the native request-polarity defect, or freshly runs the retained source test suite. The 364 passed tests and one skip reported in the paper are verified as an archived test report, not presented as a new application-test run.

Readable [Data](Data/) and [Analysis](Analysis/) copies are provided for inspection. The analysis scripts rely on the complete extracted ZIP structure; run them from that structure rather than from the lightweight inspection copies.

## NTX-24B and other supporting notebooks

[NTX-24 results](../../results/NTX24_results.zip), [NTX-24B results](../../results/NTX24B_results.zip), and their [supervisor evidence report](../../results/NTX24_NTX24B_Supervisor_Evidence_Report_2026-10-13.md) were already present in the repository. Their notebook sources are linked from the [notebook catalog](../NOTEBOOK_CATALOG.md).

NTX-24B is a typed-parser replay of the original NTX-24 generations. Its zero observed grounded unauthorized effects concern a generated reference SQLite cohort with 26 non-ALLOW families per model, not 104 independent task families or a production safety guarantee. NTX-25's archived failed-generation attempt is not a successful model benchmark.

See [CLAIM_EVIDENCE_MAP.csv](CLAIM_EVIDENCE_MAP.csv), [VERIFICATION_2026-10-28.md](VERIFICATION_2026-10-28.md), and [provenance.json](provenance.json) for the evidence boundaries and verification receipts.
