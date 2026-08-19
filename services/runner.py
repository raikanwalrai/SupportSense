from pathlib import Path
import subprocess
import time

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(
    title="SupportSense Runner",
    description="Execution service for SupportSense MLOps tasks.",
    version="0.2.0",
)

PROJECT_DIR = Path(__file__).resolve().parents[1]


class TicketPredictionRequest(BaseModel):
    """Request payload for ML ticket inference."""

    ticket: str




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
        "prediction": result.prediction,
        "model": {
            "experiment_name": result.model.experiment_name,
            "run_id": result.model.run_id,
            "model_id": result.model.model_id,
            "model_name": result.model.model_name,
            "status": result.model.status,
        },
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

    try:
        results = run_ray_experiments(config_path)
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
        "experiments": len(results),
        "results": results,
        "best": best_result,
    }
