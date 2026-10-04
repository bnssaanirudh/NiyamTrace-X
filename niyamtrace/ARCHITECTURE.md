# NiyamTrace-X Architecture & Repository Map

## Canonical Source Tree
- `apps/`: Entrypoints for the system (gateway, benchmark runner).
- `packages/`: Core libraries (auth, contracts, gate, nlp, policy).
- `tests/`: Unit, integration, and security regression suites.

## Frozen Evidence & Provenance
- `data/`: Frozen synthetic data and benchmarks.
- `provenance/`: Final reproducibility manifests and claim evidence matrix.
- `reports/`: Offline benchmark results.
- `results/`: External benchmark result records.
- `traces/`: Captured pipeline trace events.

## Historical 
- `scripts/`: Miscellaneous scripts for running analysis or external benchmarks.

## Data Flow
The canonical request flows through:
1. `apps/gateway/pipeline.py` (Orchestrator)
2. `packages/nlp/intake.py` (Multilingual normalization)
3. `packages/evidence/retriever.py` (Evidence gathering)
4. `packages/gate/gate.py` (8-Check Authorization Gate)
5. `packages/gate/simulator.py` (Shadow Simulation)
6. `packages/gate/broker.py` (Verified Execution Broker for committing state)
