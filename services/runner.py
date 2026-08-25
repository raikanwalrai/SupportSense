import os
from pathlib import Path
import subprocess
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import FileResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(
    title="SupportSense Runner",
    description="Execution service for SupportSense MLOps tasks.",
    version="0.2.0",
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
UI_DIR = PROJECT_DIR / "ui"


app.mount(
    "/ui",
    StaticFiles(directory=UI_DIR),
    name="ui",
)


class TicketPredictionRequest(BaseModel):
    """Request payload for ML ticket inference."""

    ticket: str
    source_event_id: str | None = None




HTTP_REQUESTS_TOTAL = Counter(
    "supportsense_http_requests_total",
    "Total number of HTTP requests handled by the SupportSense Runner.",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "supportsense_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
)

PREDICTIONS_TOTAL = Counter(
    "supportsense_predictions_total",
    "Total number of support ticket predictions.",
    ["model", "status"],
)

PREDICTION_DURATION_SECONDS = Histogram(
    "supportsense_prediction_duration_seconds",
    "Support ticket prediction duration in seconds.",
    ["model"],
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Record request count and latency for application endpoints."""
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    endpoint = request.url.path

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    return response


@app.get("/")
def ui() -> FileResponse:
    """Serve the SupportSense web interface."""
    index_path = UI_DIR / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=500,
            detail="SupportSense UI is not available.",
        )

    return FileResponse(index_path)


@app.get("/health")
def health() -> dict[str, str]:
    """Return runner health status."""
    return {
        "status": "ok",
        "service": "supportsense-runner",
    }


@app.post("/predict")
def predict(request: TicketPredictionRequest) -> dict[str, object]:
    """Predict the category of a support ticket using the active ML model."""
    from src.inference.ml import predict_ticket
    from src.decision.actions import get_action
    from src.monitoring.event_store import record_prediction

    if not request.ticket.strip():
        raise HTTPException(
            status_code=400,
            detail="Ticket text must not be empty.",
        )

    start_time = time.perf_counter()

    try:
        result = predict_ticket(request.ticket)
    except ValueError as exc:
        PREDICTIONS_TOTAL.labels(
            model="unknown",
            status="validation_error",
        ).inc()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        PREDICTIONS_TOTAL.labels(
            model="unknown",
            status="error",
        ).inc()

        raise HTTPException(
            status_code=500,
            detail=f"ML inference failed: {exc}",
        ) from exc

    model_name = result.model.model_name
    action = get_action(result.prediction)
    event_id = record_prediction(
        ticket=request.ticket,
        source_event_id=request.source_event_id,
        predicted_intent=result.prediction,
        model_name=result.model.model_name,
        experiment_name=result.model.experiment_name,
        run_id=result.model.run_id,
        model_id=result.model.model_id,
        model_status=result.model.status,
        action_id=action.action_id,
        action_name=action.action_name,
        risk=action.risk,
        requires_approval=action.requires_approval,
    )

    PREDICTIONS_TOTAL.labels(
        model=model_name,
        status="success",
    ).inc()

    PREDICTION_DURATION_SECONDS.labels(
        model=model_name,
    ).observe(
        time.perf_counter() - start_time
    )

    return {
        "status": "success",
        "ticket": request.ticket,
        "event_id": event_id,
        "source_event_id": request.source_event_id,
        "prediction": result.prediction,
        "decision": {
            "intent": action.intent,
            "action_id": action.action_id,
            "action_name": action.action_name,
            "risk": action.risk,
            "requires_approval": action.requires_approval,
            "simulation_message": action.simulation_message,
        },
        "model": {
            "experiment_name": result.model.experiment_name,
            "run_id": result.model.run_id,
            "model_id": result.model.model_id,
            "model_name": result.model.model_name,
            "status": result.model.status,
        },
    }


class ActionSimulationRequest(BaseModel):
    """Request to simulate a registered SupportSense action."""

    action_id: str


@app.post("/action/simulate")
def simulate_action(request: ActionSimulationRequest) -> dict[str, object]:
    """Safely simulate a registered operational action."""
    from src.decision.actions import ACTION_REGISTRY

    action = next(
        (item for item in ACTION_REGISTRY.values()
         if item.action_id == request.action_id),
        None,
    )

    if action is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown action ID: {request.action_id}",
        )

    if action.requires_approval:
        return {
            "status": "approval_required",
            "action_id": action.action_id,
            "action_name": action.action_name,
            "risk": action.risk,
            "requires_approval": True,
            "message": action.simulation_message,
        }

    return {
        "status": "simulated",
        "action_id": action.action_id,
        "action_name": action.action_name,
        "risk": action.risk,
        "requires_approval": False,
        "message": action.simulation_message,
    }



@app.get("/predictions")
def predictions(limit: int = 50) -> dict[str, object]:
    """Return recent SupportSense prediction events."""
    from src.monitoring.event_store import list_predictions

    try:
        events = list_predictions(limit=limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "success",
        "count": len(events),
        "predictions": events,
    }


@app.get("/intents")
def intents() -> dict[str, object]:
    """Return the supported SupportSense classification intents."""
    from src.features.tfidf import load_split
    from src.config.experiment_config import load_experiment_config

    config = load_experiment_config("configs/experiments.yaml")
    df = load_split(config["data"]["train_path"])

    labels = sorted(df["category"].dropna().unique())

    return {
        "status": "success",
        "count": len(labels),
        "intents": labels,
    }


class PredictionFeedbackRequest(BaseModel):
    """Human feedback for a SupportSense prediction."""

    event_id: str
    actual_intent: str
    outcome: str | None = None


@app.post("/feedback")
def record_feedback(
    request: PredictionFeedbackRequest,
) -> dict[str, object]:
    """Record human feedback for a prediction event."""
    from src.monitoring.event_store import update_prediction_outcome

    try:
        updated = update_prediction_outcome(
            event_id=request.event_id,
            actual_intent=request.actual_intent,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Prediction event not found: {request.event_id}",
        )

    return {
        "status": "recorded",
        "event_id": updated["event_id"],
        "predicted_intent": updated["predicted_intent"],
        "actual_intent": updated["actual_intent"],
        "prediction_correct": updated["prediction_correct"],
    }


@app.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/dvc/pull")
def dvc_pull() -> dict[str, object]:
    """Pull DVC-managed data from the configured remote."""
    if not PROJECT_DIR.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Project directory not found: {PROJECT_DIR}",
        )

    try:
        result = subprocess.run(
            ["dvc", "pull"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="DVC pull timed out after 300 seconds.",
        ) from None

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "DVC pull failed.",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
        )

    return {
        "status": "success",
        "operation": "dvc_pull",
        "returncode": result.returncode,
        "stdout": result.stdout,
    }


@app.post("/ray/experiments")
def ray_experiments() -> dict[str, object]:
    """Run the configured Ray experiments and return the results."""
    from src.distributed.ray_experiments import run_ray_experiments

    config_path = PROJECT_DIR / "configs" / "experiments.yaml"

    if not config_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Experiment config not found: {config_path}",
        )

    profile_name = os.environ.get("RAY_EXPERIMENT_PROFILE", "smoke")

    try:
        results = run_ray_experiments(
            config_path,
            profile_name=profile_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ray experiments failed: {exc}",
        ) from exc

    best_result = max(
        results,
        key=lambda result: result["macro_f1"],
    )

    return {
        "status": "success",
        "operation": "ray_experiments",
        "profile": profile_name,
        "experiments": len(results),
        "results": results,
        "best": best_result,
    }
