# NiyamTrace-X: run, navigate and explain

Keep this guide privately. Project the website, not tokens, terminal credentials or speaking notes.

For all six identities, token creation commands, detailed cases, speaking cues and examiner questions, use [Complete identity and demonstration handbook](ALL_ROLES_DEMONSTRATION.md). Current launcher credentials are collected privately in `.workspace-runtime/demo-identities.log`; consult the expiry beside each token.

## Start the project

Open PowerShell:

```powershell
Set-Location 'C:\Users\aniru\Downloads\NYAMTRACE\niyamtrace'
.\.venv\Scripts\python.exe -m scripts.start_workspace
```

Wait for **Services verified ready**. Keep this terminal running. Open:

http://127.0.0.1:8001/#overview

The website uses port 8001; the gateway uses port 8000. If the launcher says a port is occupied, an existing service may already be running: use the site rather than starting a second copy. In a normal foreground launch, Ctrl+C stops the services.

The launcher prints six temporary development tokens. Each token represents one identity. Copy only the token after `TOKEN:` into the site's Connection & evidence form. It expires after eight hours; a launcher restart invalidates previous tokens. Reloading the browser clears the connected identity.

For the service previously launched in the background, retrieve its current tokens privately:

```powershell
Get-Content 'C:\Users\aniru\Downloads\NYAMTRACE\niyamtrace\.workspace-runtime\launcher-current.log'
```

For a new foreground launch, use the tokens printed by that launch, rather than an older log. Do not show tokens on the projector.

## Identity and navigation

| Identity | Use it for |
|---|---|
| admin | Reindex policy evidence, reset synthetic data, review another identity's ticket, suspend vendors |
| procurement_manager | Archive invoices |
| finance_admin | Request credit changes and archive invoices |
| it_admin | Block an ordinary user account for a bounded duration |
| security_officer | Block ordinary users and suspend vendors |
| viewer | Demonstrate denied write authority |

Changing an example does not change identity. Connect the appropriate token yourself.

| Page | What to show |
|---|---|
| Overview | Problem, architecture, retained paper results, manuscript PDF and evidence memorandum |
| Request workbench | Enter an instruction, load one of 19 examples, execute and inspect the actual response |
| Execution traces | Ordered recorded events, proposed contract, checks, certificates and execution outcome |
| Synthetic ERP | Actual current SQLite rows, baseline capture and before/after comparison |
| Approval queue | Pending requests; a different admin can approve or reject, without executing the action |
| Connection & evidence | Connect identity, inspect accessible policies and explicitly reindex the source |

## Prepare before the examiner arrives

1. Open Connection & evidence. Connect **admin**.
2. Click **Reindex synthetic policy source**. Confirm accessible evidence is eligible.
3. Open Synthetic ERP and click **Restore synthetic seed**. This intentionally resets the synthetic business records.
4. Wait about two seconds, then reload ERP. The background worker may restore a past-due seed account; let this finish before capturing a baseline.
5. Connect **procurement_manager**, return to ERP and click **Capture baseline**.
6. Check the configured provider with one rehearsal request. A gateway-ready status alone does not prove model availability. The model chip reports the last observed request; `not checked` is not an availability guarantee.
7. After rehearsal, restore the seed, wait for expiry reconciliation and recapture the baseline.

The provider recently rate-limited extended checks. If `MODEL_RATE_LIMITED` appears, do not repeatedly submit or describe it as successful execution. Resolve provider availability before relying on a live positive example, or identify a retained trace as a prior observation.

## Main demonstration: three controls

### 1. Allowed bounded write

Identity: **procurement_manager**. Request:

> Archive March 2025 invoices for vendor 4421

Open the response's **Inspect execution trace**, then return to ERP and click **Compare current state**. Check the selected vendor/month/year, status changes and reported counts. A fresh seed has three matching open invoices, but read the actual result aloud.

Say:

> This request authorizes one action for one vendor and one month. The model proposes a structured contract. The gate checks that proposal and its predicted effects before the broker commits. Here I am comparing the recorded decision with the actual database rows.

### 2. Explicit prohibition

Connect admin, restore the seed, wait two seconds, reconnect procurement manager and capture a fresh baseline. Request:

> Do not archive March 2025 invoices for vendor 4421

Show `BLOCK / REQUEST_PROHIBITS_WRITE`, the trace and unchanged invoice rows.

Say:

> Having permission to archive does not mean this request authorizes an archive. Direct English prohibitions are refused before model inference. This is a deterministic guard, so I am not presenting this case as evidence of model negation understanding.

### 3. Role boundary

Connect **viewer**, capture a fresh baseline and submit:

> Archive March 2025 invoices for vendor 4421

Show `ROLE_NOT_PERMITTED` and unchanged rows.

Say:

> The request contains complete scope, but this identity lacks write authority. The gateway takes roles from verified token claims. Changing the text or selecting a preset does not grant a role.

## Additional working features

### Independent approval: example 15

1. Connect finance admin and capture a baseline.
2. Submit `Update credit limit for vendor 4421 to INR 600000`.
3. Show ESCALATE and unchanged credit limits. Obtain the pending ticket ID.
4. Connect a different admin identity, inspect the original request and approve its ticket in Approval queue. Approval alone must not change the credit limit.
5. Reconnect the original finance admin. Submit the exact original text with the approved ticket entered under **Use an approval ticket**.
6. Compare ERP and inspect the certificate. Reusing the consumed ticket should be rejected.

Say:

> This proposed financial change requires an independent decision. Approval is bound to the requester and proposal. It does not execute the action by itself, and a consumed ticket cannot be reused.

### Access block: example 16

Identity: **it_admin**. Request:

> Block user USR-PM-001 for 7 days

Show only that account's status and expiry changing. Example 17 requests a block without duration and should clarify; example 18 targets a privileged account and should reject.

Say:

> The restriction has a specific target and duration. An unambiguous explicit duration is grounded in the original request. The lifecycle worker restores timed restrictions after their UTC expiry date and records the change.

### Vendor suspension: example 19

Identity: **admin** or **security_officer**. Request:

> Suspend vendor 4421 for 7 days, justification: Documented compliance review

Show the **vendors** table: only vendor 4421's status, expiry and justification should change. Existing invoices and credit limits remain unchanged.

Say:

> This is a real change to the local vendor account record, with a required reason and bounded duration. External purchasing-system enforcement would require an additional connector.

### Demonstrating automatic expiry now

You do not need to wait seven days. A reproducible isolated verification deliberately prepares past-due temporary records, then observes the actual worker using the real clock:

```powershell
Set-Location 'C:\Users\aniru\Downloads\NYAMTRACE\niyamtrace'
.\.venv\Scripts\python.exe -m scripts.verify_workspace --business-only --known-candidates
```

Say:

> This check supplies structured candidates rather than calling a language model. The SQLite writes and background worker are real. It prepares expired temporary records and verifies automatic restoration; it does not compress seven days or modify the website's active database.

For a real-model version, omit `--known-candidates`; this consumes provider quota. In the website, lifecycle traces identify `automatic_expiry` as the system actor. Dates expire at 00:00 UTC on the stored date; polling is once per second while the gateway runs, with catch-up after restart. Indefinite or malformed restrictions are preserved.

## Fifteen-minute speaking route

| Time | Screen/action | What to say |
|---|---|---|
| 0:00–1:00 | Overview | My project is NiyamTrace-X, a request-grounded authorization system for tool-using AI agents. A user may have permission to use a tool while their particular request authorizes only a small part of its possible effect. |
| 1:00–2:30 | Architecture | The path is request, contract, evidence, gate, broker and ERP. The model interprets language. Deterministic controls decide whether the proposed effect may commit. |
| 2:30–3:30 | Identity and ERP baseline | I first establish the verified identity and the actual database state. This gives us evidence to compare after execution. |
| 3:30–5:30 | Allowed archive | I will verify the requested vendor and period, the authorization trace and the exact rows that changed. Read the observed counts here. |
| 5:30–7:00 | Prohibition | This user has archive capability, but this instruction prohibits the write. Show the correct block and unchanged state. |
| 7:00–8:00 | Viewer rejection | A complete request still cannot override the identity's role restriction. |
| 8:00–10:00 | One additional feature | Choose one rehearsed feature: independent credit approval, bounded access block or vendor suspension. Show its actual effect and trace. |
| 10:00–12:30 | Overview, paper results | The paper evaluates both legitimate task completion and unauthorized effects. Reference replay and native execution are distinct experiments. Explain one result and one failure from the displayed retained evidence, using its cohort and denominator. |
| 12:30–14:00 | Trace and limitations | Synthetic data makes these effects reproducible. Model interpretation, provider availability, broader language coverage and enterprise connectors remain practical limits. The certificate binds a proposal; it does not prove the model understood every request correctly. |
| 14:00–15:00 | Overview/closing | I have shown authorization decisions checked against actual business state, plus reproducible evidence of what passed and failed. The contribution is connecting request scope, policy and measured effects in one inspectable workflow. |

The full spoken script and historical paper figures are in `FINAL_REVIEW_15_MINUTE_PITCH.md`. Do not attempt all nineteen examples in fifteen minutes.

## Short answers to likely questions

- **Is this only a simulation?** The workbench uses a configured model provider and real SQLite mutations on synthetic business records. The architecture video is illustrative. Candidate-only verification skips inference but still exercises real storage and execution.
- **Where is the AI?** The configured language model extracts intent and slots. Typed validation, local evidence retrieval, rule-based evidence classification and authorization checks constrain its proposal.
- **How is this different from RBAC?** RBAC checks whether an identity may use a capability. Request grounding additionally checks which target, period, amount or duration this instruction authorizes.
- **What happens when checks fail?** No permitted commit is reported; the response gives a reason and the trace records the outcome. Execution mismatches trigger rollback. After a lost response, inspect state before retrying.
- **Does a certificate guarantee semantic safety?** No. It binds the checked proposal to its tool, arguments and predicted effects. Interpretation quality still needs evaluation.
- **What did you personally do?** Explain your actual design, implementation, analysis and experiments truthfully, including permitted AI assistance and collaborators.
