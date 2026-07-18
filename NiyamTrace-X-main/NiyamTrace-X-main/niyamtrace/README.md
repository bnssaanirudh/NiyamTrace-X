# NiyamTrace

**NiyamTrace** is a local-first, NLP-first assurance platform for tool-using LLM agents operating in multilingual (English, Hinglish, Hindi, Tamil, Kannada, Telugu, Romanized Telugu) enterprise environments.

## Problem Statement

Semantically equivalent requests in different languages/scripts can cause an LLM agent to retrieve different protected evidence or trigger different (and unsafe) real-world tool effects. NiyamTrace makes this measurable and enforceable.

## Current Status

> **Week 2 implementation** — Weeks 0–2 complete: spine pipeline for a single canonical English scenario. Multilingual NLP begins Week 3. See `docs/architecture.md` for module status.

## Quick Start

```bash
cd niyamtrace
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Seed the ERP database
python data/synthetic/erp.py

# Run the Week 2 exit-criterion integration test
python -m pytest tests/integration/test_week2_spine.py -v

# Run all tests
python -m pytest tests/ -v

# Start the gateway (then POST to http://localhost:8000/invoke)
uvicorn apps.gateway.main:app --reload
```

> **For AI Agents (Antigravity):** Please refer to [`../ANTIGRAVITY_GUIDE.md`](../ANTIGRAVITY_GUIDE.md) for detailed environment setup and execution instructions.

## Honest Claims

- "Deletion" in this system means **retrieval-layer tombstoning only** — records are not physically removed from the database.
- All metric values in this README are either `TBD — pending experiment` or linked to a committed run script.
- No fabricated benchmark numbers. Numbers only appear after the code that produced them is committed.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for a full module map with IMPLEMENTED / STUBBED status.

## Decisions

See [`docs/decisions.md`](docs/decisions.md) for all non-trivial design choices made during development.
