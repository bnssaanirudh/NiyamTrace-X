"""
apps/gateway/main.py — NiyamTrace FastAPI Gateway

Single endpoint: POST /invoke
  - Accepts a raw text utterance + actor context
  - Runs the full pipeline (parse → gate → execute)
  - Returns a decision + trace_id + diagnostics

The gateway instantiates the pipeline once at startup (singleton ERP conn).
In Week 5+ this will support session-scoped connections for multi-turn.

Status: IMPLEMENTED (Week 2)
"""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from data.synthetic.erp import DEFAULT_DB_PATH, init_schema, reset_to_seed, seed_fresh

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

_erp_conn: sqlite3.Connection | None = None
_pipeline: NiyamPipeline | None = None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global _erp_conn, _pipeline
    _erp_conn = seed_fresh(DEFAULT_DB_PATH)
    _pipeline = NiyamPipeline(erp_conn=_erp_conn)
    yield
    if _erp_conn:
        _erp_conn.close()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NiyamTrace Gateway",
    description=(
        "Local-first NLP-first assurance platform for multilingual LLM agents. "
        "Week 2 implementation: single canonical English scenario, deterministic pipeline."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class InvokeRequest(BaseModel):
    raw_text: str = Field(
        ...,
        description="The raw user utterance.",
        examples=["Archive March invoices for vendor 4421"],
    )
    actor_id: str = Field(..., description="Unique identifier for the requesting user.")
    actor_role: str = Field(..., description="Role of the requesting user.")
    task_id: str | None = Field(None, description="Optional external task ID.")


class InvokeResponse(BaseModel):
    trace_id: str
    task_id: str
    verdict: str
    reason_code: str
    detail: str
    predicted_record_count: int
    actual_record_count: int | None
    simulator_fidelity: float | None
    trace_path: str
    event_types: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0", "week": "2"}


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(req: InvokeRequest) -> InvokeResponse:
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized.")

    pipeline_req = PipelineRequest(
        raw_text=req.raw_text,
        actor_id=req.actor_id,
        actor_role=req.actor_role,
        task_id=req.task_id,
    )

    result = _pipeline.run(pipeline_req)

    fidelity: float | None = None
    if result.actual_delta is not None:
        from apps.gateway.pipeline import _compute_fidelity
        fidelity = _compute_fidelity(result.predicted_delta, result.actual_delta)

    return InvokeResponse(
        trace_id=result.trace_id,
        task_id=result.task_id,
        verdict=result.gate_decision.verdict,
        reason_code=result.gate_decision.reason_code,
        detail=result.gate_decision.detail,
        predicted_record_count=result.predicted_delta.estimated_row_count,
        actual_record_count=result.actual_delta.estimated_row_count if result.actual_delta else None,
        simulator_fidelity=fidelity,
        trace_path=str(result.trace_path),
        event_types=result.gate_decision and [e.event_type for e in result.events],
    )


@app.post("/admin/reset-erp")
async def reset_erp() -> dict[str, str]:
    """Reset ERP to seed state (for testing/demo — not exposed in production)."""
    if _erp_conn is None:
        raise HTTPException(status_code=503, detail="ERP not initialized.")
    reset_to_seed(_erp_conn)
    return {"status": "reset", "message": "ERP restored to seed state."}
