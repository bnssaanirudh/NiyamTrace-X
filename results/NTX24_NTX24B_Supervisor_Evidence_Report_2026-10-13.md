# NiyamTrace-X: Additional Experimental Evidence from NTX-24 and NTX-24B

**Research evidence memorandum for guide/supervisor review**  
**Prepared:** 13 October 2026  
**Status:** Verified against archived outputs; **not yet approved for unconditional manuscript inclusion**  
**Purpose:** Determine which additional results can be included in the current *NiyamTrace-X: Request-Grounded Effect Containment for Multilingual Tool-Using Large Language Model Agents* manuscript, and specify the limits of the claims.

> **Critical provenance distinction:** NTX-24 generated 240 genuine open-weight model outputs in a quick GPU experiment. NTX-24B did **not** run another 240 model inferences: it re-parsed those **same, frozen** responses with a corrected typed parser and replayed them through the same four reference authorization methods. These are *linked stages of a single cohort*, not two independent replication studies. Their trial counts or zero-event counts must not be added together.

## Executive decision for supervisors

**Suitable for inclusion as a qualified exploratory ablation:** Yes, particularly the impact of schema normalization on safety versus legitimate task completion, the paired before/after SQLite effects, and separate fault-injection evidence. **Not sufficient as proof of production deployment safety or general multilingual robustness.** The experiment uses templated requests, a small quick-run cohort, and a stand-alone reference harness rather than the fully integrated native NiyamTrace-X executor.

The strongest supported result is: **After correcting representational mismatches in saved model proposals, the request-grounded reference gate completed 13/16 authorized requests for each of two small models (81.25%) while recording 0/104 unauthorized commits among non-ALLOW requests for each model.** In contrast, with the same corrected proposals, an ungated arm recorded 61/104 unsafe effects for Qwen and 60/104 for Granite. This is a result for *generated, unreviewed reference fixtures*; it is not a production guarantee.

---

## 1. Evidence packages examined and authenticity checks

| Evidence source | Original archive / contents | What it establishes |
|---|---|---|
| NTX-24 | `NTX24_results.zip`: 13 files | Saved GPU model proposals, model revisions and latencies, original strict-parser replay, 4-arm SQLite results, scripted checks, and manifest |
| NTX-24B | `NTX24B_results (2).zip`: 15 files | Frozen-source reanalysis with `TYPED_V2`, paired strict-versus-corrected results, normalization audit, 4-arm database replay, family/language summaries and fault tests |
| Original notebook | `NTX24_Prospective_Effect_Audit.ipynb` | Definitions of fixtures, reference arms, commit checks, and initial strict parser |
| Correction notebook | `NTX24B_Schema_Safety.ipynb` | Defined normalization rules, strict-parser replication, and re-evaluation of preserved generations |

**Integrity audit performed for this report:**

- Both uploaded ZIP files pass internal ZIP CRC inspection.
- NTX-24: **12/12** files listed in `manifest.json` match their SHA-256 and byte-size entries.
- NTX-24B: **14/14** files listed in `ntx24b_manifest.json` match their SHA-256 and byte-size entries.
- `benchmark_cases.jsonl` is byte-identical between the two archives. The NTX-24B embedded source hashes match the original archived `benchmark_cases.jsonl`, Qwen generations, Granite generations, and original manifest.
- The NTX-24B strict-parser results reproduce the NTX-24 original **eight model-by-arm safety/completion totals exactly**.
- `NTX24B_results (2).zip` contains **0 fresh GPU generations**; `source_cohort=ORIGINAL_FROZEN_GPU` for the replays.

**Archive SHA-256 fingerprints:**

```text
NTX24_results.zip       6f43e8b315c03802d9926705267e56869e53090c8d2c2ef248a619618d7ee5f3
NTX24B_results (2).zip 043bd510cd0ce90455bd7bb40ca95c5ef294de52d5823929ba7ba5f6f02fb1ed
```

**Important:** A passing manifest verifies consistency of the archived bytes, **not** truthfulness of the benchmark labels, absence of code bugs, or independent reproduction in the project's production environment.

## 2. Experimental protocol and denominators

### 2.1 Generated benchmark and scope

The complete programmatically generated fixture bank contains **300 task families × four language realizations = 1,200 requests**. The executed NTX-24 quick GPU run selected only the first **120 requests per model**, corresponding to **30 task families** with four language realizations each. The same selected requests were reused by NTX-24B.

| Feature | Recorded scope |
|---|---|
| Models | `Qwen/Qwen2.5-3B-Instruct`; `ibm-granite/granite-3.3-2b-instruct` |
| Frozen model revisions | Qwen `aa8e72537993ba99e69dfaafa59ed015b17504d1`; Granite `707f574c62054322f6b5b04b6d075f0a8f05e0f0` |
| Inference | Genuine recorded GPU inference in NTX-24; no inference errors in the 240 provenance rows; deterministic saved proposals |
| Historical evaluated sample | 120 requests **per model** = 240 total model generations |
| Independent family count | 30 task families overall; only **four authorized** families and **26 non-ALLOW** families |
| Language/script forms | English, Hindi, Telugu, Romanized Telugu; **30 requests per form per model** |
| Tasks | Invoice archival, transfer approval, document sharing; **40 requests per domain per model** |
| Gold outcome distribution per model | **ALLOW 16; BLOCK 68; CLARIFY 36** (= 120); the non-ALLOW denominator is **104** |
| Case-condition distribution per model | ALLOW 16; NEGATED 20; VIEWER 24; WRONG_TENANT 24; MISSING_FIELD 20; AMBIGUOUS 16 |
| Effect instrumentation | Isolated in-memory SQLite databases for each model proposal and method arm; before/after business-state comparisons |
| NTX-24 replay rows | **240 model generations × four arms = 960** arm-level rows |
| NTX-24B replay rows | **240 original generations × two parser settings × four arms = 1,920** arm-level rows; **not 1,920 fresh model inferences** |
| Labels and multilingual evaluation | Generated templates and programmatic reference outcomes; **no independent bilingual annotator adjudication** |

**Four compared reference implementations (not live NiyamTrace-X production deployments):**

1. `MODEL_ONLY`: Executes the model proposal without the additional request-grounded authorization policy; baseline for unsafe effects.
2. `ROLE_SCOPE_REF`: Checks proposal completeness, model negation flag, actor role, resource existence and tenant scope; no independent explicit request-text grounding.
3. `TEXT_GROUNDED_REF`: Adds checks against the original request for action, resource identifiers, critical arguments, explicit negations, and uncertainty cues. Uses a **small hand-defined multilingual cue lexicon and request templates**, not a validated general natural-language entailment system.
4. `TXN_CERT_REF`: Adds an in-process HMAC/request-bound reference certificate plus transaction-effect verification and atomic rollback behavior to the text-grounded arm. Its issuer/executor security boundary is **not** independently verified for production use.

**Definitions:** An **unsafe non-ALLOW effect** is an observed business-state mutation on a `BLOCK` or `CLARIFY` request which does not match the authorized expected state. **Authorized completion** means that a gold-`ALLOW` case produced exactly the expected business state with at least one actual business change. **Exact-effect count** includes both successful ALLOW operations and correctly unmodified non-ALLOW requests; this can overstate utility if reported alone. Parsing failures and no-op responses remain in denominators.

## 3. NTX-24: Original strict-parser experiment

NTX-24 used a strict JSON/action interface requiring integer-like critical fields. Both checkpoints produced many outputs containing typed resource IDs (`INV#23001`, `TRF#...`, `DOC#...`, `USER#...`) or spelled-out month names not accepted by the strict parser.

### 3.1 Original parsing outcomes

| Original strict parsing status | Qwen2.5-3B | Granite-3.3-2B |
|---|---:|---:|
| Parsed complete proposal (`OK`) | **13/120 (10.83%)** | **0/120 (0%)** |
| `BAD_SCHEMA` | 105/120 | 109/120 |
| `NONE` | 2/120 | 11/120 |
| Model inference exceptions | 0/120 | 0/120 |

The original interface substantially confounded **schema compliance** with **semantic understanding and authorization behavior**. Consequently, the original zero-unsafe-effect rates should **not** be presented as an adequate safety demonstration.

### 3.2 Original strict-parser SQLite evaluation

Each cell below is **unsafe commits among 104 non-ALLOW requests / successful executions among 16 ALLOW requests** for that model. All arm-level rows were recorded, including parser failures.

| Arm | Qwen: unsafe /104 | Qwen: authorized /16 | Granite: unsafe /104 | Granite: authorized /16 |
|---|---:|---:|---:|---:|
| `MODEL_ONLY` | 5 | 0 | 0 | 0 |
| `ROLE_SCOPE_REF` | 4 | 0 | 0 | 0 |
| `TEXT_GROUNDED_REF` | **0** | **0** | **0** | **0** |
| `TXN_CERT_REF` | **0** | **0** | **0** | **0** |

**Interpretation:** The reference grounder blocked the five observed Qwen baseline unauthorized effects, but **all methods failed every legitimate task**. Granite's apparent safety was likewise inseparable from having no successfully parsed complete proposals. These initial results revealed an interface-level validity issue rather than persuasive evidence of deployable safety.

## 4. NTX-24B: Defined schema correction and paired replay

### 4.1 What was changed, and what was not

NTX-24B preserved the originally generated texts, test cases, models, initial SQLite fixtures, and authorization-arm code; it changed **only the proposal-interpretation layer** for the paired analysis.

`TYPED_V2` accepts a defined set of representational equivalents:

- Domain-specific typed object identifiers (`INV#...`, `TRF#...`, `DOC#...`) and recipient identifiers (`USER#...`) when the prefix matches the field and requested action.
- Positive decimal numbers as integers or bounded numeric strings (including explicit year and month checks).
- Explicit English/Hindi/Telugu month names converted to their corresponding calendar month, with no fuzzy inference.
- Ignores irrelevant optional fields **with an audit warning** rather than forwarding them to the executor.
- Rejects swapped/wrong ID prefixes, malformed digits, boolean IDs, invalid or missing required fields, duplicate JSON keys, unsupported actions, and ambiguous/extraneous JSON content.
- A missing `negated` flag is **unknown**, not affirmative permission; the text-grounded arm separately checks explicit negation in the original request.

The correction **does not** consult gold decisions, benchmark hidden answer fields, or the database's correct target values to repair a proposal. It is a frozen-source **CPU reanalysis**, not an extra independent model experiment.

### 4.2 Parse recovery

| Parse quality | Qwen2.5-3B | Granite-3.3-2B |
|---|---:|---:|
| Complete under original parser | 13/120 = **10.83%** | 0/120 = **0%** |
| Complete under `TYPED_V2` | **77/120 = 64.17%** | **77/120 = 64.17%** |
| Net additional complete proposals | **+64** / +53.33 percentage points | **+77** / +64.17 percentage points |
| Status change details | 71 previously rejected outputs recovered; **7 previously strict-`OK` outputs became incomplete** under stricter required-field checks | 77 previously rejected outputs recovered; no previous complete outputs to lose |

**Interpretation:** The normalizer recovers explicit structure that was already present in raw generations. It **does not** fix missing parameters or unsupported user intent. Qwen's 7 previously accepted records that now fail the completeness checks are an important audit detail, not a contradiction.

### 4.3 Main corrected replay results (`TYPED_V2`)

| Model | Arm | Unsafe commits /104 non-ALLOW | Unsafe rate | Authorized complete /16 ALLOW | Completion rate | Exact-effect matches /120 |
|---|---|---:|---:|---:|---:|---:|
| Qwen | `MODEL_ONLY` | **61/104** | **58.65%** | 13/16 | 81.25% | 56/120 |
| Qwen | `ROLE_SCOPE_REF` | **25/104** | **24.04%** | 13/16 | 81.25% | 92/120 |
| Qwen | `TEXT_GROUNDED_REF` | **0/104** | **0% observed** | **13/16** | **81.25%** | **117/120** |
| Qwen | `TXN_CERT_REF` | **0/104** | **0% observed** | **13/16** | **81.25%** | **117/120** |
| Granite | `MODEL_ONLY` | **60/104** | **57.69%** | 13/16 | 81.25% | 57/120 |
| Granite | `ROLE_SCOPE_REF` | **25/104** | **24.04%** | 13/16 | 81.25% | 92/120 |
| Granite | `TEXT_GROUNDED_REF` | **0/104** | **0% observed** | **13/16** | **81.25%** | **117/120** |
| Granite | `TXN_CERT_REF` | **0/104** | **0% observed** | **13/16** | **81.25%** | **117/120** |

**Paired safety/utility observation:** For both models, going from the ungated corrected replay to `TEXT_GROUNDED_REF` reduced observed unsafe effects from **61 to 0** (Qwen) and **60 to 0** (Granite), while preserving **13 of 16** authorized completions. Compared with `ROLE_SCOPE_REF`, the text grounder removed **25** unsafe events per model. The extra `TXN_CERT_REF` stage produced **identical outcomes** to `TEXT_GROUNDED_REF` for all saved model proposals; **do not claim an observed incremental model-cohort gain from certification**.

**Remaining legitimate failures:** Each protected arm still failed **3/16** authorized language variants per model (18.75% false-block / noncompletion rate among gold-ALLOW requests). In this generated set, those incomplete requests account for the difference between **117/120** exact-effect matches and **120/120**.

### 4.4 Where the unsafe baseline effects came from

| Case type | Total cases/model | Qwen unsafe, ungated (`TYPED_V2`) | Granite unsafe, ungated (`TYPED_V2`) |
|---|---:|---:|---:|
| `NEGATED` | 20 | 12 | 11 |
| `VIEWER` | 24 | 18 | 18 |
| `WRONG_TENANT` | 24 | 18 | 17 |
| `AMBIGUOUS` | 16 | 13 | 14 |
| `MISSING_FIELD` | 20 | 0 | 0 |
| **Total non-ALLOW** | **104** | **61** | **60** |

The especially high baseline rates on negation, weak-role, cross-tenant and ambiguous generated requests give concrete examples of failure modes exercised by the reference policy. `MISSING_FIELD` generated requests did not yield observable unsafe effects in the ungated replay and therefore cannot be used to demonstrate a reduction for that category.

### 4.5 Per-language evaluation after correction

Each language group has **30 requests/model: four ALLOW and 26 non-ALLOW**. The completion values below are for `TEXT_GROUNDED_REF`; ungated unsafe counts illustrate the safety baseline. `TXN_CERT_REF` gives the same model-cohort completion/unsafe totals as `TEXT_GROUNDED_REF`.

| Model | Language/script | Complete with grounded gate /4 | Ungated unsafe /26 | Grounded-gate unsafe /26 |
|---|---|---:|---:|---:|
| Qwen | English | 4 | 16 | 0 |
| Qwen | Hindi | 3 | 16 | 0 |
| Qwen | Telugu | 3 | 15 | 0 |
| Qwen | Romanized Telugu | 3 | 14 | 0 |
| Granite | English | 4 | 16 | 0 |
| Granite | Hindi | 3 | 13 | 0 |
| Granite | Telugu | 4 | 19 | 0 |
| Granite | Romanized Telugu | 2 | 12 | 0 |

**Parser acceptance by language** (strict `OK` → corrected `OK`, out of 30 each):

| Language | Qwen | Granite |
|---|---:|---:|
| English | 2 → 23 | 0 → 20 |
| Hindi | 9 → 19 | 0 → 17 |
| Telugu | 2 → 18 | 0 → 26 |
| Romanized Telugu | 0 → 17 | 0 → 14 |

These results document the behavior of **four templated language realizations**. They **do not** demonstrate translation robustness over naturally varied user requests or languages beyond the predefined lexicon.

### 4.6 Per-domain legitimate completion in the protected arm

| Domain | Gold-ALLOW variants/model | Qwen completed | Granite completed |
|---|---:|---:|---:|
| Invoice archival | 8 | **8** | **7** |
| Transfer approval | 4 | **1** | **2** |
| Document sharing | 4 | **4** | **4** |
| **Total** | **16** | **13** | **13** |

The completion failures are concentrated in transfer/invoice templates, not evenly distributed across task types. With so few families this pattern is descriptive, not a general domain-ranking conclusion.

## 5. Transaction-integrity and deliberate fault injection (separate from GPU trials)

The archived **48 scripted fault-injection rows** comprise **24 paired task-language probes** from just **six ALLOW families**, each tested under `TEXT_GROUNDED_REF` and `TXN_CERT_REF`. In these tests an otherwise authorized request is intentionally subjected to an unexpected extra database mutation.

| Scripted reference method | Tests | Unexpected effect committed | Rolled back with no business-row change |
|---|---:|---:|---:|
| `TEXT_GROUNDED_REF` | 24 | **24/24** | 0/24 |
| `TXN_CERT_REF` | 24 | **0/24** | **24/24** |

This shows that the *reference transaction-effect verifier* detects and rolls back the specific injected effect mismatch when the text-grounded check alone cannot. The saved notebook also reports passing reference self-tests for replay-nonce uniqueness, original-request signature binding, actor tampering, atomic rollback, and selected negative-case rejection.

**Non-negotiable caveat:** These were **scripted/oracle-selected allow-path proposals**, not additional model-generated inferences and **not native-production proof**. There are only **six unique task families**, not 24 independent attack types. Their counts must be presented in a separate results table and **must not be pooled** with the 240 saved model outcomes.

## 6. Statistical uncertainty and interpretation

- The 120 requests per model are **30 task families with four correlated language realizations each**. Treating all 120 language variants as independent gives overstated statistical precision.
- The protected safety assessment has **zero events across 26 independent non-ALLOW families per model**. Under a simplified IID family-event assumption, the exact **one-sided 95% zero-event upper bound is approximately 10.88%** (`1 - 0.05^(1/26)`), **not zero**. Generalization to new users or out-of-distribution prompts is not established.
- The NTX-24B archive includes **family-clustered bootstrap percentile intervals**. For protected authorized completion, the archived intervals are **0.25–1.00 (Qwen)** and **0.50–1.00 (Granite)**, despite the same 13/16 point result. These very wide intervals reflect that only **four ALLOW families** underlie 16 realizations. Family bootstrap intervals of 0–0 for no observed violations do not by themselves bound unseen risk.
- The paired old/new completion tests report **exact case-level McNemar two-sided p = 0.000244** for 0→13 on each model/arm. However, these case-level tests do **not** adjust for sibling language realizations of the same four ALLOW families. **Do not present this p-value as conclusive inferential support**; if needed, label exploratory and conduct a properly clustered analysis on a much larger family set.
- Results from Qwen and Granite are not independent across fixtures; both models see identical generated family concepts. Avoid combining them into a purported *n=208 independent safety-opportunity* result, and avoid combining NTX-24 with NTX-24B as independent studies.
- `0/104` is an **observed count** under this particular reference harness and corpus, not a proof that the true unauthorized-commit probability is zero.

## 7. Claims that may / may not enter the manuscript

| Proposed statement | Recommendation | Reason |
|---|---|---|
| “Typed ID and month normalization increased usable complete proposals from 13 to 77 for Qwen and from 0 to 77 for Granite (per 120 generated requests).” | **Include, labeled paired offline replay** | Directly supported by raw-proposal reanalysis |
| “Protected reference arms achieved 13/16 successful ALLOW executions and 0/104 observed unsafe non-ALLOW mutations per model.” | **Include with scope and uncertainty** | Raw effects confirmed; small clustered samples and generated fixtures |
| “Text grounding reduced Qwen ungated unsafe commits from 61 to 0 and Granite from 60 to 0 without changing authorized completion (13/16).” | **Include with reference-harness qualifier** | Same proposals and isolated initial database state; descriptive paired contrast |
| “Certificate enforcement improved model-driven safety over text grounding.” | **Do not claim** | Model cohort outcomes identical between these two arms |
| “Transaction-bound reference checking rolled back 24/24 intentionally injected extra-mutation tests.” | **Include as separate scripted test** | Valid isolated mechanism test; only six source families |
| “NTX-24B is a separate independent model replication with another 240 GPU inferences.” | **Incorrect — exclude** | Same original 240 raw outputs; zero new inference |
| “The method guarantees 100% safe live ERP execution / complete mediation.” | **Unsupported — exclude** | Native live execution path and independent deployment security unverified |
| “Multilingual robustness is validated across real-world Hindi/Telugu user populations.” | **Unsupported — exclude** | Templated phrases and no independent human adjudication |
| “NTX-24B shows full 1,200-case-per-model performance.” | **Incorrect — exclude** | Only 120 cases/model were historically evaluated |
| “Safety is statistically proven because 0/104 violations were observed.” | **Incorrect — exclude** | Family-level uncertainty and model/corpus shift unresolved |

## 8. Draft results paragraph for faculty review (not automatically submission-ready)

> **Schema-corrected paired execution audit.** We examined two open-weight language models, Qwen2.5-3B-Instruct and Granite-3.3-2B-Instruct, on 120 generated multilingual requests each, representing 30 task families in four language/script forms. The initial strict parser accepted 13/120 complete Qwen proposals and no complete Granite proposals, largely due to typed resource identifiers and nonnumeric month representations. A predefined, label-independent typed normalizer applied retrospectively to the *same frozen raw outputs* increased complete proposal acceptance to 77/120 for each model. We replayed every proposal through four reference authorization methods using isolated SQLite database states. With corrected parsing, ungated execution produced unauthorized database effects in 61/104 non-ALLOW Qwen requests and 60/104 Granite requests, whereas request-grounded checking produced zero observed unauthorized effects in each 104-request cohort while completing 13/16 authorized requests per model. Adding a transaction-bound certificate produced no further improvement in this model-generated replay. In a separate six-family scripted fault-injection test, however, the transaction-effect verifier rolled back all 24 injected unexpected-mutation realizations, compared with 24 committed unexpected effects without it. These findings isolate schema compatibility, request grounding, and reference-level transaction verification as distinct mechanisms. They do not establish general multilingual authorization reliability or security of the native deployed executor, as the evaluated requests were generated from fixed templates and independently adjudicated or official gate-in-path benchmarks were not used.

**Suggested subsection title:** *Schema Normalization, Safety–Utility Trade-offs, and Transaction-Effect Verification*.

**Suggested table organization:**

- **Main table:** Corrected `TYPED_V2` four-arm comparison for both models (unsafe /104; authorized /16; exact effects /120).
- **Supplementary Table S1:** Original strict parser vs typed parser, including status-transition details.
- **Supplementary Table S2:** Per-language and per-domain outcomes; distinguish model results from template-based labels.
- **Supplementary Table S3:** Separate scripted fault-injection experiment (24 paired trials, six families).
- **Supplementary provenance:** Model checkpoint revisions, sample IDs, raw generations, notebook/parser revision, input and output hashes, and all quality-gate flags.

## 9. What the supervisor should request before upgrading these claims

1. **Independently create and adjudicate a new held-out request corpus**, including natural paraphrases, rare negation scopes, code-switching and unseen resource/name formats. Report bilingual agreement and adjudicated disagreements.
2. **Run the planned full cohort** (1,200 requests/model as originally configured), and clearly separate newly generated outputs from the 240 frozen quick-run outputs.
3. **Integrate the gate into the actual NiyamTrace-X native tool-to-database execution path** and demonstrate mediation, tamper/replay resistance, failure handling, and atomicity under realistic concurrency and storage faults.
4. **Evaluate official external agent benchmarks with the gate genuinely on the action path**; do not treat un-gated agent-only benchmark scores as authorization evidence.
5. **Expand independent task families and legitimate ALLOW scenarios** enough to estimate safety and utility with appropriately clustered uncertainty rather than relying on four ALLOW families.
6. **Freeze parser policy and statistical analysis before the next held-out evaluation**, to reduce bias from iterative tuning on the same generated templates.

## 10. Bottom-line evaluation

**Research value:** The two notebooks form a coherent **diagnosis → controlled correction → paired effect-level validation** chain. Their most important contribution is **not a headline zero-violation rate**, but evidence that the original apparent safety was partly due to catastrophic interface rejection. After restoring typed parameter compatibility, the reference request-grounding mechanism rejects actually executable unsafe proposals **while preserving most legitimate executions** on the saved quick-run templates. The additional transaction-bound verifier demonstrates a distinct rollback capability only in separate scripted injection tests.

**Recommended manuscript treatment:** Add as an **exploratory controlled ablation or supplementary execution audit**, subject to supervisor inspection of code and fixtures. Do **not** claim it represents a new independent test set, a production-hardening validation, an official agent benchmark result, or a top-journal-grade generalization study.

---

### Reproducibility map (precise archive members)

- NTX-24 `manifest.json`, `inference_provenance.csv`, `metrics.csv`, `replay_case_level.csv`, `generations_Qwen2.5-3B-Instruct.jsonl`, `generations_granite-3.3-2b-instruct.jsonl`, `reference_fault_injection_separate.csv`, `integrity_checks.json`, `research_quality_gates.json`.
- NTX-24B `ntx24b_manifest.json`, `original_input_manifest.json`, `original_embedded_input_sha256.json`, `normalizer_audit.csv`, `case_level.csv`, `metrics.csv`, `paired_delta.csv`, `per_language.csv`, `scripted_faults_SEPARATE.csv`, `quality_gates.json`.
- Original request definitions and programmatic labels: `benchmark_cases.jsonl` (same SHA-256 in both archives: `46e6d221e8c6df899dd496dd750595e4808ad33cc378f1c46b948cb882f3682a`).

**Approval line for guide/supervisor (to complete):** Include in main text / Include only as supplementary exploratory evidence / Defer pending native validation / Exclude; reasons: ________________________.
