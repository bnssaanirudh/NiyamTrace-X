"""
apps/dashboard/main.py — NiyamTrace Analytics Dashboard (Week 7)

FastAPI application serving:
  - GET /            → dashboard HTML UI (static/index.html)
  - GET /api/metrics → combined metrics JSON for the UI
  - GET /api/verdicts  → gate verdict counts
  - GET /api/latency   → avg latency by event type
  - GET /api/evidence  → evidence verdict distribution
  - GET /api/divergence → cross-lingual divergence rate
  - GET /api/traces    → recent traces list
  - GET /api/traces/{trace_id} → single trace event detail

Start with:
    uvicorn apps.dashboard.main:app --port 8001 --reload

Status: IMPLEMENTED (Week 7)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from packages.lake.transform import SilverTransform
from packages.lake.metrics import GoldMetrics

_STATIC_DIR = Path(__file__).parent / "static"
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_SILVER_DIR = _REPO_ROOT / "traces" / "silver"

app = FastAPI(
    title="NiyamTrace Dashboard",
    description="Gold-layer analytics for NiyamTrace pipeline runs.",
    version="0.7.0",
)

# Mount static files for the HTML UI
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


def _get_metrics() -> GoldMetrics:
    """
    Refresh Silver from Bronze, then return a GoldMetrics instance.
    This is called on every request so the dashboard always shows fresh data.
    In production this would be a background job.
    """
    # Run silver transform to pick up any new Bronze traces
    transform = SilverTransform()
    transform.run(verbose=False)
    return GoldMetrics(silver_dir=_SILVER_DIR)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def dashboard_ui():
    """Serve the dashboard HTML page."""
    index_path = _STATIC_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse(
            content={"error": "Dashboard UI not found. Check apps/dashboard/static/index.html"},
            status_code=404,
        )
    return FileResponse(str(index_path))


@app.get("/api/metrics")
async def all_metrics():
    """Combined metrics endpoint — used by dashboard on load."""
    try:
        gm = _get_metrics()
        data = {
            "gate_verdict_counts": gm.gate_verdict_counts(),
            "avg_latency_by_event": gm.avg_latency_by_event(),
            "evidence_verdict_distribution": gm.evidence_verdict_distribution(),
            "cross_lingual_divergence": gm.cross_lingual_divergence_rate(),
            "recent_traces": gm.recent_traces(n=10),
        }
        gm.close()
        return JSONResponse(content=data)
    except Exception as exc:
        return JSONResponse(content={"error": str(exc), "data": {}}, status_code=500)


@app.get("/api/verdicts")
async def gate_verdicts():
    gm = _get_metrics()
    result = gm.gate_verdict_counts()
    gm.close()
    return result


@app.get("/api/latency")
async def avg_latency():
    gm = _get_metrics()
    result = gm.avg_latency_by_event()
    gm.close()
    return result


@app.get("/api/evidence")
async def evidence_distribution():
    gm = _get_metrics()
    result = gm.evidence_verdict_distribution()
    gm.close()
    return result


@app.get("/api/divergence")
async def divergence_rate():
    gm = _get_metrics()
    result = gm.cross_lingual_divergence_rate()
    gm.close()
    return result


@app.get("/api/traces")
async def recent_traces(n: int = 20):
    gm = _get_metrics()
    result = gm.recent_traces(n=n)
    gm.close()
    return result


@app.get("/api/traces/{trace_id}")
async def trace_detail(trace_id: str):
    gm = _get_metrics()
    result = gm.trace_summary(trace_id)
    gm.close()
    if not result:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found in Silver layer.")
    return result
