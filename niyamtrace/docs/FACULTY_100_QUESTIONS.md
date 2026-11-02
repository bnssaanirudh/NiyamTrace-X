# NiyamTrace-X: 100 faculty questions and suggested answers

These answers describe the retained paper and the local research prototype. Rehearse in your own words. Distinguish historical experiments from live observations, and describe your own contributions and any permitted assistance truthfully. Source anchors: `paper/current/main.tex`, its `tables/`, `apps/dashboard/static/paper-results.json`, `docs/END_TO_END_STATUS_2026-10-29.md` and the full pitch. Counts below are cohort-specific.

## Problem and contribution

1. **What problem do you solve?** A tool-using agent can produce effects beyond what a user's particular instruction authorizes, even if the user has a role that permits the tool.
2. **Why is this important?** Agent tools can change business state; an incorrect interpretation can become a real, unintended write.
3. **What is request-grounded authorization?** Checking a proposed action and its predicted effects against the original request, identity and applicable policy before execution.
4. **What is the central example?** Permission to archive invoices does not authorize archiving every vendor or month when the instruction specifies vendor 4421 and March 2025.
5. **How is this different from RBAC?** RBAC grants capabilities to roles; request grounding additionally constrains the target and effects authorized in this instance.
6. **What research question do you ask?** Whether request-grounded constraints reduce unauthorized effects while preserving completion of legitimate tasks, and how this changes across interpretations and execution settings.
7. **What is the paper's contribution?** It defines and evaluates request-grounded controls with both safety and utility measures, and reports failure cases as well as positive results.
8. **What is the implementation contribution?** A local gateway, contract extraction, evidence, gate, broker, SQLite execution, approvals and trace inspection for bounded synthetic workflows.
9. **Why call it a prototype?** The system is local, uses synthetic records, and needs broader evaluation and enterprise integrations.
10. **What is your own contribution?** Describe the design, implementation and experimental work you actually performed, and disclose permitted assistance and collaborators accurately.

## Architecture and contracts

11. **What is the pipeline?** Request → structured contract → retrieved evidence → authorization gate → verified broker → ERP effect → trace and evaluation.
12. **Where does the model fit?** The configured model interprets natural language and proposes typed intent and arguments; deterministic checks govern execution.
13. **Is every component a separate AI agent?** No. The UI labels components by responsibility; most are deterministic services, not independent language models.
14. **What is a contract?** A structured representation of intent, action, target, constraints and relevant scope extracted from a request.
15. **What is a request anchor?** A constraint grounded in the source instruction, such as vendor, month, year, amount, duration or explicit prohibition.
16. **Why retain source spans?** They help connect extracted values to the request; a recorded span alone does not guarantee correct semantics.
17. **What happens when scope is missing?** The system should clarify or block instead of assuming an unrestricted write; inspect the actual reason.
18. **What does the simulator do?** It computes predicted changes before commitment, allowing the gate and broker to compare the proposed effect with authorized scope.
19. **What is the broker's job?** Bind the checked action and predicted delta to execution, and reject or roll back a mismatch.
20. **What is in an execution trace?** Ordered records such as input, contract extraction, retrieval, policy, proposal, simulation, gate decision, execution and final evaluation; early exits can omit stages.

## Identity, policy and controls

21. **What is a demo token?** A short-lived signed JWT carrying a subject, tenant and role claims for the local gateway.
22. **How many demo identities are provided?** Six: procurement_manager, finance_admin, it_admin, security_officer, admin and viewer.
23. **Who verifies the claims?** The gateway verifies the token signature and derives the principal from claims, rather than trusting a role typed in request text.
24. **Do examples switch roles?** No. A preset loads text; a user must connect the appropriate token.
25. **How long are launcher tokens valid?** Eight hours; restarting the launcher generates a new signing secret and invalidates earlier launcher tokens.
26. **Are these production identities?** No. They are local development credentials. A real deployment needs an authenticated identity provider and key management.
27. **What is the role of the evidence index?** It retrieves accessible local policy documents and checks eligibility/freshness for the principal and request.
28. **Is the local evidence classifier another LLM?** The described local evidence classification is rule based; the configured model interprets the user request.
29. **What does reindexing do?** It ingests the configured policy source into the current index and records ingestion time and source hash; it does not itself approve a new policy.
30. **What does fail closed mean here?** If required interpretation, evidence or authorization fails, no permitted write is reported; inspect the precise failure reason and persisted state.

## Effects, certificates and concurrency

31. **What is an effect?** A change in a business-state record, such as an invoice status or a vendor restriction.
32. **What makes an effect authorized?** It must fall within the request and applicable identity/policy constraints and match the checked proposal.
33. **What is a predicted delta?** The rows and fields the tool predicts it will change before committing.
34. **What is an actual delta?** The changes made by execution and measured after the action, subject to the implementation's transaction boundary.
35. **What does a certificate bind?** The checked proposal, tool, arguments, actor/tenant and predicted effects to the execution path.
36. **Does a certificate prove the request was understood?** No. A well-bound certificate can bind an incorrect interpretation; the historical native failure demonstrates this distinction.
37. **Is the prototype certificate a full enterprise trust boundary?** No. Its hash supports binding/tamper evidence in this local design; stronger issuer isolation and signing need further work.
38. **What happens if actual and predicted effects disagree?** The broker rejects the mismatch and the transaction is rolled back in the tested path.
39. **What about concurrency?** Conditional updates protect selected restriction extensions; broader concurrent-writer and distributed-system evaluation remains necessary.
40. **What happens after a lost response?** Inspect the persisted ERP and trace before retrying; a client timeout alone does not prove a transaction failed.

## Live workflow and cases

41. **How do you start it?** From the `niyamtrace` folder run `.\.venv\Scripts\python.exe -m scripts.start_workspace`, wait for readiness, and open localhost port 8001.
42. **What services are running?** The browser dashboard on port 8001 and authenticated gateway on port 8000, with local SQLite and a configured model provider.
43. **What is the allowed archive input?** `Archive March 2025 invoices for vendor 4421`; compare the actual matching rows and trace to the baseline.
44. **How many rows should change?** A fresh seed has three matching open invoices, but state and observed counts must be checked; already archived rows can yield zero changes.
45. **What is the English prohibition input?** `Do not archive March 2025 invoices for vendor 4421`; the direct English guard returns REQUEST_PROHIBITS_WRITE before model inference.
46. **Why is this prohibition example not proof of model reasoning?** The documented guard handles direct English prohibitions before the model is called.
47. **What is the viewer control?** Connect viewer and submit the positive archive request; verify ROLE_NOT_PERMITTED and unchanged data if the proposal reaches the role check.
48. **Does a quota error demonstrate a role denial?** No. MODEL_RATE_LIMITED is a provider failure, not evidence that the role check executed.
49. **How is a baseline used?** Capture ERP before a request, then compare the current state after it; concurrent sessions can also change data, so correlate with the trace.
50. **Why reset the seed between cases?** It restores known synthetic starting records so a previous write does not mask a later effect. It intentionally replaces synthetic state.

## Approvals and business operations

51. **How is independent approval demonstrated?** Request an eligible change, observe escalation without mutation, have a different admin approve, then let the original requester resubmit the exact request with its ticket.
52. **Does approval execute the change?** No. Approval records a decision; the requester still submits through the execution checks.
53. **Can the requester approve their own ticket?** The tested workflow rejects self-approval.
54. **Can a consumed ticket be reused?** The tested path rejects reuse with APPROVAL_NOT_GRANTED.
55. **What credit change example is available?** Finance admin can request `Update credit limit for vendor 4421 to INR 600000`; verify escalation, independent approval and the actual credit record.
56. **What is the access-block example?** IT admin requests `Block user USR-PM-001 for 7 days`; check the one user's status and deadline.
57. **What if block duration is absent?** The example should require clarification rather than silently choosing a duration; inspect the observed outcome.
58. **Can the ordinary block action target a privileged account?** The documented protected-account example is rejected by that tool.
59. **What is the vendor example?** Admin or security officer can request a bounded suspension with an explicit justification; inspect only the intended vendor row and fields.
60. **Does local vendor suspension automatically stop external purchases?** No. External enforcement needs a connector and integration with the purchasing system.

## Expiry, reliability and implementation

61. **What happens when a timed restriction expires?** The gateway worker restores eligible expired user blocks and vendor suspensions and clears the corresponding deadline fields.
62. **When does expiry run?** At startup and approximately once per second while the gateway runs, using stored UTC date boundaries.
63. **What about indefinite or malformed deadlines?** They are preserved rather than automatically lifted.
64. **How do you demonstrate expiry immediately?** The isolated known-candidate verifier prepares explicitly past-due test records and observes the real worker; it does not fast-forward seven days.
65. **Is expiry audit delivery durable?** The current worker logs post-commit trace failures; a durable audit outbox is not implemented.
66. **What backend framework and database are used?** FastAPI services and SQLite for the local synthetic ERP; the browser dashboard talks through the gateway.
67. **What does the dashboard show?** Request input, actual response, traces, business rows, approval queue, identity/evidence readiness and retained paper results.
68. **What does a ready gateway badge establish?** Service readiness, not current model quota or successful interpretation.
69. **How are provider failures handled?** They are surfaced with a reason such as MODEL_RATE_LIMITED; no fabricated successful action is claimed.
70. **What testing has been reported?** The documented prior full run reported 628 passed and one skipped; identify the run date and avoid presenting it as a fresh test without rerunning it.

## Metrics and experimental design

71. **What is verdict accuracy?** The fraction of cases whose predicted authorization decision matches the reference decision, using that study's denominator.
72. **What is an unsafe case?** A case with an unauthorized effect under the study's definition; distinguish an unsafe verdict from an executed unsafe commit.
73. **What is exact completion?** Correct completion of an authorized request with the required effects, measured over authorized requests in the specified cohort.
74. **Why report both safety and utility?** A system that blocks everything may show no unsafe commits but also complete no legitimate work.
75. **What is effect fidelity?** Agreement between intended or predicted and observed effects under the experiment's defined comparison; verify the particular metric definition before quoting a value.
76. **Why use denominators?** Counts without cohort size and case type cannot be compared fairly; different experiments have different denominators.
77. **What is reference replay?** Evaluating saved proposals or constructed reference outputs through a harness, rather than necessarily generating new model outputs and making native writes.
78. **What is native execution?** A model-backed execution path where the experiment observes actual business-state changes for the tested workflow.
79. **What is a known-candidate control?** A supplied structured candidate bypasses inference, isolating the execution and authorization machinery from language interpretation.
80. **Why not combine all results into one accuracy?** The studies differ in task, model, method, data and outcome; pooling would obscure what was measured.

## Paper results and models

81. **What did the frozen Qwen reference report?** Full sequence: 1,997/2,000 correct and zero observed unsafe verdicts; base: 1,891 correct and 80 unsafe verdicts.
82. **What did the frozen GPT-OSS reference report?** Full sequence: 1,996/2,000 correct and zero observed unsafe verdicts; base: 1,994 correct and two unsafe verdicts.
83. **Do frozen verdicts prove executed-write safety?** No. They are reference verdict results, not a native executed-effect safety estimate.
84. **What was the paired Granite utility trade-off?** Anchors completed 152/162 authorized requests; full intersection completed 104/162, a reduction of 48, with zero observed unsafe cases in both arms.
85. **What happened in historical native Qwen execution?** Three prohibited cases committed, affecting five invoice rows; authorized completion was 3/12 in 48 attempts.
86. **What happened in the native Granite arm?** Zero unsafe commits but also 0/12 authorized completion, with 43 output errors in 48 attempts.
87. **What did the known-candidate native control achieve?** 12/12 authorized completion and zero observed unsafe effects in its 48 attempts; it did not test model interpretation.
88. **What is NTX-24B?** Corrected-parser replay of saved NTX-24 generations: 120 per model, comprising 104 non-ALLOW and 16 ALLOW cases, with no new generation in that replay.
89. **What did NTX-24B report for model-only unsafe effects?** 61/104 for Qwen and 60/104 for Granite in the reference replay; text grounding observed 0/104 for each.
90. **What was NTX-24B authorized completion?** Text-grounded reference arms completed 13/16, or 81.25%, for each model; the certificate arm had the same observed outcomes on those proposals.

## Limitations, languages and research defense

91. **Which models appear in the paper?** Retained results include Qwen, GPT-OSS and Granite in different cohorts; do not assume they all occur in every experiment. The local live workspace is configured separately.
92. **What languages were examined?** The corrected language table covers English, Hindi, Telugu and Romanized Telugu; the UI also includes a Hinglish probe.
93. **How large is the language cohort?** Thirty requests per language per model in the replay: four authorized and 26 non-ALLOW; it is the same NTX-24B cohort, not a separate additional study.
94. **Does zero observed unsafe effects mean zero risk?** No. Limited, correlated generated examples cannot establish a zero population failure rate.
95. **What are the data limitations?** Generated templates share task families and lack independent bilingual adjudication in the described replay; they limit diversity and independence.
96. **Why are model output errors important?** They affect usable completion and can make a system appear safe merely because no action was performed.
97. **What is a good next evaluation?** Freeze the implementation, rerun historical negative cases, use independently reviewed multilingual requests and report exact effects and completion with uncertainty.
98. **What ablations would help?** Compare role-only, text grounding, evidence checks, intersection and certificate/broker controls under the same cases and seeds, separating model from executor effects.
99. **What would production deployment still require?** Independent identity issuance, stronger trust boundaries, external connectors, durable audit delivery, concurrency/load testing, monitoring and security review.
100. **What is the most honest conclusion?** Request grounding can constrain and reveal effects in the evaluated settings, while native semantic failures and limited evidence prevent a broad safety guarantee.
