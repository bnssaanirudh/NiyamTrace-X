# Run the actual NiyamTrace workspace

From `C:\Users\aniru\Downloads\NYAMTRACE\niyamtrace`:

```powershell
python -m scripts.start_workspace
```

Open http://127.0.0.1:8001. This is the existing dashboard, connected to the real gateway. The terminal prints temporary local development tokens for procurement manager, finance admin, IT admin, security officer, admin and viewer. They expire after eight hours and become invalid when the launcher restarts. Use `--gateway-only` if the dashboard is already running. When launched as a hidden local service, the private tokens are in `.workspace-runtime/launcher-current.log`.

The launcher now checks for occupied ports and waits for both services to be ready. Existing ERP records survive gateway restarts. Use the explicit admin **Restore synthetic seed** action when you need a clean demonstration state. Model extraction runs outside the gateway event loop so health requests can continue during inference. The header shows the configured model and its last observed state; “not checked” means no request has run since startup.

1. Open **Connection & evidence** and connect the admin token. Inspect evidence age; use **Reindex synthetic policy source** to load the configured source into the process index. The receipt names the source hash and ingestion time. Source contents and revocation are retained.
2. Connect the procurement-manager token. Open **Synthetic ERP** and observe the OPEN March 2025 invoices for vendor 4421.
3. Open **Request workbench**. Submit `Archive March 2025 invoices for vendor 4421`. Inspect the actual response, trace, and ERP state.
4. Connect admin and restore the synthetic seed; reconnect the operator. Submit `Do not archive March 2025 invoices for vendor 4421`. Inspect the blocked execution and unchanged records.
5. Connect the viewer token and submit an archive. The role must be rejected.

The launcher uses the existing configured provider and a separate synthetic runtime database at `.workspace-runtime/erp.db`. It does not fabricate model output. Provider errors remain visible. Tokens are held only in page memory and should not be committed. Approval and source-index operations require admin identity. Self-approval is rejected.

The explicit-prohibition guard covers the documented direct English forms for supported write verbs. It does not establish arbitrary multilingual semantic safety. Historical traces and paper artifacts predate the current source changes and retain their original meaning.

## Observed real-provider verification

After explicit source indexing, the original Gemini-backed pipeline produced:

- Archive: ALLOW; predicted 3, actual 3, fidelity 1.0; ERP changed.
- Explicit prohibition on freshly reset rows: BLOCK, `REQUEST_PROHIBITS_WRITE`; ERP unchanged.
- Viewer archive: BLOCK, `ROLE_NOT_PERMITTED`; ERP unchanged.

Run `python -m scripts.verify_workspace` to repeat these checks against an isolated temporary ERP using the configured provider. This consumes real provider calls.

The verifier exercises the dashboard adapter and gateway in-process with an ASGI transport, a real configured model provider, isolated ERP and isolated traces. It checks exact positive row changes, denial state preservation, clarification, trace retrieval, metrics, the WebSocket feed, and independent approval escalation/consumption. It also rejects self-approval and replay of a consumed ticket. Its machine-readable report is `.test-tmp/workspace-e2e-report.json`. The report is written only after all checks pass; check its timestamp when using a retained report.

The approvals verification inserts eight additional matching rows into its temporary database so the real ten-row threshold is crossed. It does not populate or reset your running workspace database. Ordinary demo seed requests do not necessarily require approval.

If the model provider is unavailable or rate-limited, `python -m scripts.verify_workspace --known-candidates` checks the same execution/approval plumbing with explicit structured candidates and no model inference. It writes `.test-tmp/workspace-e2e-known-candidates-report.json` and does not establish language-model correctness. The live verifier requires the expected denial reasons so extraction failures do not masquerade as successful authorization controls.

## Installation

Use Python 3.11 or newer. From this directory:

```powershell
python -m pip install -e ".[cloud-llm,dev]"
```

Configure the selected provider privately using `.env.example` as the key-name reference. Use `.[local-llm,dev]` for the existing local provider backend, which also requires its model server and configured model. The video encoder is an optional authoring dependency; ordinary site playback does not require it.

## Supported scope

Latest verification: **628 tests passed, one skipped**. The core configured-model verifier passed its complete archive, prohibition, role, clarification, independent approval and feed workflow. Vendor suspension also completed in a real-model run. The final additional model check was rate limited; structured-candidate checks verify the final business-action and lifecycle implementation without inference.

The end-to-end workflow includes bounded invoice archiving, credit-limit changes, timed access blocks and vendor suspension, with identity, evidence, gate, broker, state comparison, approvals and trace analytics. Credit decreases or resulting limits above INR 50,000 require independent review. Access blocks are capped at 365 days; blocks beyond 30 days require independent review, and privileged users are rejected by the ordinary block tool. Vendor suspensions require an explicit 1–365 day duration and justification of at least ten characters, with admin or security-officer identity. The background worker restores expired timed restrictions every second and after startup, with committed-change audit traces. Null/indefinite and malformed expiries remain restricted. Dates are UTC end boundaries, so a deadline expires at 00:00 UTC that day. External purchasing systems are outside scope.

Run `python -m scripts.verify_workspace --business-only` for focused real-model vendor/access and expiry verification. Add `--known-candidates` to check real database and background-worker behavior without consuming model calls. Reports are stored separately as `.test-tmp/workspace-business-report.json` and `.test-tmp/workspace-business-known-candidates-report.json`. The expiry check deliberately prepares past-due temporary records; it uses the real clock and does not compress seven days or modify the running workspace.
