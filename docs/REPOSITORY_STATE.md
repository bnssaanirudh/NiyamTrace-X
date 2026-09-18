# NiyamTrace-X Repository State

## Canonical Implementation Tree
The **canonical** and only active implementation tree for the NiyamTrace-X project is `niyamtrace/`. All backend services, tools, and the evaluation framework reside in this directory.

## Recent Canonicalization (Phase 0)
- **Duplicate Removal:** Duplicated code trees (such as `NiyamTrace-X-main`) have been deleted to avoid confusion.
- **Workflow & Docker Relocation:** GitHub CI workflows (`.github/workflows`) and the primary `docker-compose.yml` have been relocated to the repository root for better developer experience and standard CI compatibility.
- **Experiments & Notebooks:** All Jupyter Notebooks (`.ipynb`) previously polluting the root directory have been moved into the `experiments/` directory.

## Artifact Policy
- Static benchmarking datasets are kept under `niyamtrace/datasets/`.
- Generated execution traces are stored in `niyamtrace/traces/`.
- Stale HTML benchmark reports should not be committed to the tree unless they are versioned evidence snapshots.
