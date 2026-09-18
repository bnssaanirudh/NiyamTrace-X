# NiyamTrace-X

**NiyamTrace-X** is a local-first, NLP-first assurance platform for tool-using LLM agents operating in multilingual (English, Hinglish, Telugu, Romanized Telugu) enterprise environments.

## Problem Statement

Semantically equivalent requests in different languages/scripts can cause an LLM agent to retrieve different protected evidence or trigger different (and unsafe) real-world tool effects. NiyamTrace-X makes this measurable and enforceable through a production-grade execution-gating platform.

## Current Status

> **Production Hardening Phase** — We have completed comprehensive benchmarking across major model families (Gemini, Qwen, Llama, Pixtral) and external benchmarks (BFCL, AgentDojo, τ³). The core assurance pipeline (Intake → Contract Extraction → Evidence Retrieval → Gate Evaluation → Execution) is fully implemented.

## Quick Start

```bash
# Configure environment variables
cp niyamtrace/.env.example .env
# Edit .env and add your API keys (e.g., GEMINI_API_KEY, GROQ_API_KEY)

# Run the docker compose environment
docker compose up -d

# Or run locally
cd niyamtrace
pip install -e ".[dev]"
python data/synthetic/erp.py
python -m pytest tests/ -v
uvicorn apps.gateway.main:app --reload
```

## Supported Production Surface

NiyamTrace-X currently supports:
- **Languages:** English, Hinglish, Telugu, Romanized Telugu. (Hinglish/Romanized Telugu are supported via transliteration/heuristic models).
- **Tool Actions:** Only deterministic tools mapped to ERP endpoints are truly executable. For instance, `archive_invoices`, `block_user_access`, `update_credit_limit`, and `suspend_vendor`. Other tools are simulated or blocked.
- **Fail-Closed Behavior:** Applies strictly to code paths and tools guarded by the NiyamGate evaluation. 
- **Models:** Supported via explicit configuration (e.g., Gemini 1.5 Pro, Qwen 2.5 3B, GPT-4o, Mixtral) rather than marketing copy.

## Honest Claims

- "Deletion" in this system means **retrieval-layer tombstoning only** — records are not physically removed from the database.
- Benchmark Failures: We prominently acknowledge that some benchmarks highlight over-blocking or model drift. Currently, certain local model benchmarks achieved ~35% on specific transfer tasks, which cannot justify unmonitored production deployment without human-in-the-loop recovery.
- No fabricated benchmark numbers. Numbers only appear after the code that produced them is committed.

## Documentation

- **Architecture:** See [`docs/architecture.md`](docs/architecture.md) for a full module map.
- **Implementation Status:** See [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) for readiness of each module.
- **Repository State:** See [`docs/REPOSITORY_STATE.md`](docs/REPOSITORY_STATE.md) for codebase layout.
