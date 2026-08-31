from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.risklens.training import train_and_save

from .audit import AuditStore
from .incident_engine import IncidentEngine
from .risk_engine import RiskEngine
from .schemas import BatchRequest, BatchResponse, RiskDecision, Transaction


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"
STATIC_DIR = ROOT / "app" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MODEL_PATH.exists() or not METRICS_PATH.exists():
        train_and_save(ARTIFACT_DIR)
    app.state.engine = RiskEngine(MODEL_PATH)
    app.state.incidents = IncidentEngine()
    app.state.audit = AuditStore(ROOT / "data" / "audit" / "decisions.jsonl")
    yield


app = FastAPI(
    title="RiskLens AI",
    version="0.1.0",
    description="Explainable, bounded payment fraud-risk decision support.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "model_version": app.state.engine.model_version,
        "incident_intelligence": "ready",
    }


@app.post("/api/score", response_model=RiskDecision)
def score_transaction(transaction: Transaction) -> RiskDecision:
    try:
        decision = app.state.engine.score(transaction)
        app.state.audit.append(decision.model_dump())
        return decision
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/batch", response_model=BatchResponse)
def score_batch(request: BatchRequest) -> BatchResponse:
    system_mode = "degraded" if request.simulate_model_failure else "normal"
    decisions = (
        app.state.engine.score_many_degraded(request.transactions)
        if request.simulate_model_failure
        else app.state.engine.score_many(request.transactions)
    )
    for decision in decisions:
        app.state.audit.append(decision.model_dump())
    spikes = app.state.engine.detect_merchant_spikes(decisions)
    active_threshold = 0.40 if request.simulate_model_failure else app.state.engine.threshold
    incidents = app.state.incidents.analyze(
        request.transactions,
        decisions,
        active_threshold,
        system_mode=system_mode,
    )
    flagged = sum(decision.risk_score >= active_threshold for decision in decisions)
    return BatchResponse(
        decisions=decisions,
        merchant_spikes=spikes,
        incidents=incidents,
        system_mode=system_mode,
        safety_notice=(
            "Model unavailable: transparent fallback rules are active, automation is disabled, and high-impact actions are human-gated."
            if request.simulate_model_failure
            else "Incident affinities and financial projections are decision-support estimates, not attacker attribution or production guarantees."
        ),
        summary={
            "transactions": len(decisions),
            "flagged": flagged,
            "held_for_review": sum(item.recommended_action == "hold_for_review" for item in decisions),
            "merchant_spikes": sum(item.alert for item in spikes),
            "average_risk": round(sum(item.risk_score for item in decisions) / len(decisions), 4),
            "active_incidents": sum(item.risk_twin.status == "attack" for item in incidents),
        },
    )


@app.get("/api/metrics")
def metrics() -> dict:
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=503, detail="Evaluation metrics are not available.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.get("/api/audit")
def recent_audit(limit: int = Query(default=25, ge=1, le=200)) -> dict:
    records = app.state.audit.recent(limit)
    return {"records": records, "count": len(records)}
