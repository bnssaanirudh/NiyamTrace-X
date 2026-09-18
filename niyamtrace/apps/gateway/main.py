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
from packages.auth import Principal, get_current_principal, require_role
from packages.api.errors import NiyamAPIError, global_exception_handler, api_error_handler
from packages.api.request_context import RequestContextMiddleware
from packages.api.rate_limit import rate_limit_dependency
from packages.config import get_settings
from fastapi import Depends, Request

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

app.add_middleware(RequestContextMiddleware)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(NiyamAPIError, api_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class InvokeRequest(BaseModel):
    raw_text: str = Field(
        ...,
        max_length=5000,
        description="The raw user utterance.",
        examples=["Archive March invoices for vendor 4421"],
    )
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


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    if _erp_conn is None or _pipeline is None:
        raise HTTPException(status_code=503, detail="Service unavailable")
    # In production, check DB, policy bundle, model config
    return {"status": "ready"}


@app.post("/invoke", response_model=InvokeResponse, dependencies=[Depends(rate_limit_dependency)])
async def invoke(
    req: InvokeRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal)
) -> InvokeResponse:
    if _pipeline is None:
        raise NiyamAPIError(status_code=503, code="SERVICE_UNAVAILABLE", message="Pipeline not initialized.")

    # Convert the frozenset to list and get the first role or a default.
    # We will refine this in the pipeline context phase.
    primary_role = next(iter(principal.roles)) if principal.roles else "user"

    pipeline_req = PipelineRequest(
        raw_text=req.raw_text,
        actor_id=principal.subject,
        actor_role=primary_role,
        task_id=req.task_id,
    )

    try:
        result = _pipeline.run(pipeline_req)
        request.state.trace_id = result.trace_id
    except Exception as e:
        raise NiyamAPIError(status_code=500, code="PIPELINE_ERROR", message="An error occurred during pipeline execution.")

    fidelity: float | None = None
    if result.actual_delta is not None:
        from apps.gateway.pipeline import _compute_fidelity
        fidelity = _compute_fidelity(result.predicted_delta, result.actual_delta)

    predicted_count = 0
    if result.predicted_delta is not None:
        predicted_count = result.predicted_delta.estimated_row_count

    trace_path = ""
    settings = get_settings()
    if settings.debug_mode or "auditor" in principal.roles:
        trace_path = str(result.trace_path)

    return InvokeResponse(
        trace_id=result.trace_id,
        task_id=result.task_id,
        verdict=result.gate_decision.verdict,
        reason_code=result.gate_decision.reason_code,
        detail=result.gate_decision.detail,
        predicted_record_count=predicted_count,
        actual_record_count=result.actual_delta.estimated_row_count if result.actual_delta else None,
        simulator_fidelity=fidelity,
        trace_path=trace_path,
        event_types=result.gate_decision and [e.event_type for e in result.events],
    )


@app.post("/admin/reset-erp")
async def reset_erp(principal: Principal = Depends(require_role("admin"))) -> dict[str, str]:
    """Reset ERP to seed state (for testing/demo — requires admin role)."""
    if _erp_conn is None:
        raise HTTPException(status_code=503, detail="ERP not initialized.")
    reset_to_seed(_erp_conn)
    return {"status": "reset", "message": "ERP restored to seed state."}
