# Final Code / Paper Audit

## Alignment Audit

- **Authentication path:** Verified. `Principal` and `AuthorizationContext` separate user-provided strings from verified identities.
- **RBAC, scopes, tenant isolation:** Verified. Implemented and enforced centrally.
- **Semantic authorization:** Verified. Uses NLIEngine on extracted slots.
- **Evidence retrieval:** Verified. Rule-based retriever fetches the right chunks.
- **Policy checks:** Verified. The 8-check deterministic gate enforces all conditions.
- **Simulation:** Verified. Predicted State Deltas accurately capture rows to be mutated.
- **Per-tool authorization:** Verified. Each tool generates independent contracts and simulated deltas.
- **Composition authorization:** Verified. Entire pipeline enforces atomicity across all tools in a single request.
- **EffectCertificate:** Verified. Contains cryptographic hash and immutable actor context.
- **Transaction-first broker:** Verified. Integrated tightly into the `pipeline.py`.
- **Replay resistance:** Verified via timestamps and jti.
- **Stale-state handling:** Verified. The broker demands predicted rows match executed rows perfectly.
- **Rollback:** Verified. Enforced by `SessionManager.transaction()`.
- **Actual-vs-predicted effect check:** Verified. Enforced by `VerifiedExecutionBroker`.
- **Complete mediation boundary:** Verified. No path to environment execution exists outside `pipeline.py`.
- **External benchmark integration:** Modified claim. Tau-Bench, AgentDojo, and BFCL currently face infrastructure failures due to missing environment packages; this is documented in limitations.

## Action Items
- Adjusted manuscript limitations to clarify that third-party integrations (tau3, AgentDojo, BFCL) failed to run due to absent dependencies in the execution environment, preventing broad empirical generalization claims.
