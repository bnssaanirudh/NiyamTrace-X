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
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from data.synthetic.erp import seed_fresh_async
from packages.api.errors import NiyamAPIError, api_error_handler, global_exception_handler
from packages.api.rate_limit import rate_limit_dependency
from packages.api.request_context import RequestContextMiddleware
from packages.auth import Principal, get_current_principal, require_role
from packages.auth.models import AuthorizationContext
from packages.config import get_settings
from packages.storage.models import PendingApproval

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

_engine: Any = None
_pipeline: NiyamPipeline | None = None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _pipeline
    from packages.storage.postgres import get_async_engine
    _engine = get_async_engine()
    await seed_fresh_async(_engine)
    _pipeline = NiyamPipeline(engine=_engine)
    yield
    if _engine:
        await _engine.dispose()


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
    approval_id: str | None = Field(None, description="Optional approval ticket ID.")


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
    if _engine is None or _pipeline is None:
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

    # Build the stable authorization context from the verified principal.
    # This is the ONLY source of truth for actor identity, roles, scopes, and tenant.
    # Caller-supplied request text cannot modify this context.
    auth_context = AuthorizationContext.from_principal(principal)

    pipeline_req = PipelineRequest(
        raw_text=req.raw_text,
        actor_id=principal.subject,
        actor_role=auth_context.display_role,  # deterministic display role for logging
        task_id=req.task_id,
        approval_id=req.approval_id,
        auth_context=auth_context,  # full context for authorization decisions
    )

    try:
        result = await _pipeline.run(pipeline_req)
        request.state.trace_id = result.trace_id
    except Exception:
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
    if _engine is None:
        raise HTTPException(status_code=503, detail="ERP not initialized.")
    await seed_fresh_async(_engine)
    return {"status": "reset", "message": "ERP restored to seed state."}


# ---------------------------------------------------------------------------
# Approvals API
# ---------------------------------------------------------------------------

@app.get("/admin/approvals")
async def list_approvals(principal: Principal = Depends(require_role("admin"))) -> list[dict]:
    """List pending approvals."""
    if _engine is None:
        raise HTTPException(status_code=503, detail="ERP not initialized.")
    async with AsyncSession(_engine) as session:
        result = await session.execute(select(PendingApproval).filter_by(status="PENDING"))
        approvals = result.scalars().all()
        return [
            {
                "approval_id": a.approval_id,
                "trace_id": a.trace_id,
                "requested_by": a.requested_by,
                "created_at": a.created_at,
                "expires_at": a.expires_at,
            }
            for a in approvals
        ]


@app.post("/admin/approvals/{approval_id}/approve")
async def approve_escalation(approval_id: str, principal: Principal = Depends(require_role("admin"))) -> dict[str, str]:
    """Approve a pending request."""
    if _engine is None:
        raise HTTPException(status_code=503, detail="ERP not initialized.")
    async with AsyncSession(_engine) as session:
        result = await session.execute(select(PendingApproval).filter_by(approval_id=approval_id))
        approval = result.scalars().first()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found.")
        
        if approval.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Approval is in state {approval.status}.")
            
        if approval.requested_by == principal.user_id:
            raise HTTPException(status_code=403, detail="Segregation of Duties: Cannot approve your own request.")
            
        import time
        if approval.expires_at < time.time():
            approval.status = "EXPIRED"
            await session.commit()
            raise HTTPException(status_code=400, detail="Approval has expired.")
            
        approval.status = "APPROVED"
        approval.reviewed_by = principal.user_id
        await session.commit()
        return {"status": "APPROVED", "approval_id": approval_id}


@app.post("/admin/approvals/{approval_id}/reject")
async def reject_escalation(approval_id: str, principal: Principal = Depends(require_role("admin"))) -> dict[str, str]:
    """Reject a pending request."""
    if _engine is None:
        raise HTTPException(status_code=503, detail="ERP not initialized.")
    async with AsyncSession(_engine) as session:
        result = await session.execute(select(PendingApproval).filter_by(approval_id=approval_id))
        approval = result.scalars().first()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found.")
        
        if approval.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Approval is in state {approval.status}.")
            
        approval.status = "REJECTED"
        approval.reviewed_by = principal.user_id
        await session.commit()
        return {"status": "REJECTED", "approval_id": approval_id}


@app.post("/admin/traces/purge")
async def purge_traces(retention_days: int = 30, principal: Principal = Depends(require_role("admin"))) -> dict[str, Any]:
    """Purge trace files older than retention_days."""
    import time

    from apps.gateway.pipeline import _DEFAULT_TRACES_DIR
    
    cutoff_time = time.time() - (retention_days * 86400)
    deleted_count = 0
    
    if _DEFAULT_TRACES_DIR.exists():
        for path in _DEFAULT_TRACES_DIR.iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff_time:
                path.unlink()
                deleted_count += 1
                
    return {"status": "success", "message": f"Purged {deleted_count} trace files older than {retention_days} days."}
