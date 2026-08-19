#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# VALIDATION SCRIPT
# ============================================================
#
# Performs a complete development-environment validation.
#
# Checks:
#
# Validation sections:
#   Python environment
#   Core package imports
#   Deep Learning / Ray Tune
#   Dependency consistency
#   DVC
#   MLflow health
#   Runner health
#   ML model artifact and inference
#   Prometheus health and Runner scrape
#   Grafana health
#   Airflow health
#   Airflow DAG visibility
#   Full pytest suite
#
# This is intentionally more expensive than "status".
#
# Use:
#
#     ./scripts/supportsense.sh validate
#
# before a major sprint checkpoint, demo, or release.
#
# ============================================================

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT_DIR/scripts/lib/dev-config.sh"
AIRFLOW_DIR="$ROOT_DIR/airflow"


FAILURES=0

pass() {
    echo "PASS: $1"
}

fail() {
    echo "FAIL: $1"
    FAILURES=$((FAILURES + 1))
}

echo "============================================================"
echo " SupportSense Development Environment"
echo " VALIDATION"
echo "============================================================"
echo

cd "$ROOT_DIR"

# ------------------------------------------------------------
# Python
# ------------------------------------------------------------

echo "===== 1. PYTHON ENVIRONMENT ====="

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    pass "Virtual environment active: $VIRTUAL_ENV"
else
    fail "Virtual environment is not active"
fi

echo

# ------------------------------------------------------------
# Package imports
# ------------------------------------------------------------

echo "===== 2. CORE PACKAGE IMPORTS ====="

if python - <<'PY'
import pandas
import sklearn
import mlflow
import ray
import pyspark
import fastapi
import dvc

print("pandas :", pandas.__version__)
print("sklearn:", sklearn.__version__)
print("mlflow :", mlflow.__version__)
print("ray    :", ray.__version__)
print("pyspark:", pyspark.__version__)
print("fastapi:", fastapi.__version__)
print("dvc    :", dvc.__version__)
PY
then
    pass "Core Python packages import correctly"
else
    fail "Core Python package import check failed"
fi

echo

# ------------------------------------------------------------
# Deep Learning / Ray Tune
# ------------------------------------------------------------

echo "===== 3. DEEP LEARNING / RAY TUNE ====="

if PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" python - <<'PYTHON'
import inspect
import subprocess

import torch
import ray
from ray import tune

from src.models.deep_learning.model import (
    SupportSenseTextClassifier,
)
from src.models.deep_learning.train import train

print("torch       :", torch.__version__)
print("ray         :", ray.__version__)
print("ray.tune    :", "available")

signature = inspect.signature(train)

required_parameters = {
    "epochs",
    "batch_size",
    "learning_rate",
    "embedding_dim",
    "dropout",
    "patience",
    "use_ray",
}

missing = required_parameters - set(signature.parameters)

if missing:
    raise RuntimeError(
        f"Missing train() parameters: {sorted(missing)}"
    )

print("train() API :", "Sprint 6 parameters available")
print("DL model    :", "importable")

compile_result = subprocess.run(
    [
        "python",
        "-m",
        "compileall",
        "-q",
        "src/models/deep_learning",
    ],
    check=False,
)

if compile_result.returncode != 0:
    raise RuntimeError(
        "Deep-learning module compilation failed."
    )

print("DL compile  :", "PASS")
PYTHON
then
    pass "Deep-learning and Ray Tune integration"
else
    fail "Deep-learning and Ray Tune integration"
fi

echo

# ------------------------------------------------------------
# pip check
# ------------------------------------------------------------

echo "===== 4. DEPENDENCY CONSISTENCY ====="

if pip check; then
    pass "pip check"
else
    fail "pip check"
fi

echo

# ------------------------------------------------------------
# DVC
# ------------------------------------------------------------

echo "===== 5. DVC ====="

if dvc status; then
    pass "DVC pipeline/data state"
else
    fail "DVC status"
fi

echo

# ------------------------------------------------------------
# MLflow
# ------------------------------------------------------------

echo "===== 6. MLFLOW ====="

if curl -sf "$MLFLOW_URL/version"; then
    echo
    pass "MLflow health"
else
    fail "MLflow health"
fi

echo

# ------------------------------------------------------------
# Runner
# ------------------------------------------------------------

echo "===== 7. SUPPORTSENSE RUNNER ====="

if curl -sf "$RUNNER_URL/health"; then
    echo
    pass "Runner health"
else
    fail "Runner health"
fi

echo

# ------------------------------------------------------------
# ML model / inference
# ------------------------------------------------------------

echo "===== 8. ML MODEL / INFERENCE ====="

if MLFLOW_TRACKING_URI="$MLFLOW_TRACKING_URI" python - <<'PYTHON'
import os

import mlflow
from mlflow import MlflowClient

tracking_uri = os.environ["MLFLOW_TRACKING_URI"]

mlflow.set_tracking_uri(tracking_uri)

client = MlflowClient(
    tracking_uri=tracking_uri
)

experiment = client.get_experiment_by_name(
    "SupportSense Baseline"
)

if experiment is None:
    raise RuntimeError(
        "SupportSense Baseline MLflow experiment not found"
    )

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string="attributes.status = 'FINISHED'",
    order_by=["attributes.start_time DESC"],
    max_results=20,
)

if not runs:
    raise RuntimeError(
        "No completed SupportSense Baseline MLflow run found"
    )

run = None
logged_model = None

for candidate_run in runs:
    candidate_models = client.search_logged_models(
        experiment_ids=[experiment.experiment_id],
        filter_string=(
            f"source_run_id = '{candidate_run.info.run_id}'"
        ),
    )

    ready_models = [
        model
        for model in candidate_models
        if model.status == "READY"
    ]

    if ready_models:
        run = candidate_run
        logged_model = ready_models[0]
        break

if run is None or logged_model is None:
    raise RuntimeError(
        "No READY SupportSense MLflow model found "
        "in the latest 20 completed runs"
    )

if logged_model.status != "READY":
    raise RuntimeError(
        f"MLflow logged model is not READY: "
        f"{logged_model.status}"
    )

model_uri = f"models:/{logged_model.model_id}"

model = mlflow.sklearn.load_model(model_uri)

prediction = model.predict(
    ["I cannot login to my account"]
)

if len(prediction) != 1 or not prediction[0]:
    raise RuntimeError(
        "ML model inference returned an invalid prediction"
    )

print("Experiment :", experiment.name)
print("Run ID     :", run.info.run_id)
print("Model ID   :", logged_model.model_id)
print("Model      :", logged_model.name)
print("Status     :", logged_model.status)
print("Test ticket: I cannot login to my account")
print("Prediction :", prediction[0])
PYTHON
then
    pass "ML model artifact and inference"
else
    fail "ML model artifact and inference"
fi

echo

# ------------------------------------------------------------
# Prometheus
# ------------------------------------------------------------

echo "===== 9. PROMETHEUS ====="

if curl -sf "$PROMETHEUS_URL/-/healthy"; then
    echo
    pass "Prometheus health"
else
    fail "Prometheus health"
fi

echo

echo "Prometheus Runner target:"

PROMETHEUS_TARGET="$(
    curl -sf -G "$PROMETHEUS_URL/api/v1/query"         --data-urlencode 'query=up{job="supportsense-runner"}'         2>/dev/null || true
)"

if printf '%s' "$PROMETHEUS_TARGET" |
    grep -q '"status":"success"' &&
    printf '%s' "$PROMETHEUS_TARGET" |
    grep -q '"value":\[[^]]*,"1"\]'; then
    echo "$PROMETHEUS_TARGET"
    pass "Prometheus scraping SupportSense Runner"
else
    echo "$PROMETHEUS_TARGET"
    fail "Prometheus scraping SupportSense Runner"
fi

echo

# ------------------------------------------------------------
# Grafana
# ------------------------------------------------------------

echo "===== 10. GRAFANA ====="

if curl -sf "$GRAFANA_URL/api/health"; then
    echo
    pass "Grafana health"
else
    fail "Grafana health"
fi

echo

# ------------------------------------------------------------
# Airflow health
# ------------------------------------------------------------

echo "===== 11. AIRFLOW HEALTH ====="

if curl -sf "$AIRFLOW_URL/api/v2/monitor/health"; then
    echo
    pass "Airflow health"
else
    fail "Airflow health"
fi

echo

# ------------------------------------------------------------
# Airflow DAG
# ------------------------------------------------------------

echo "===== 12. AIRFLOW DAG ====="

if [[ -f "$AIRFLOW_DIR/docker-compose.yaml" ]]; then
    cd "$AIRFLOW_DIR"

    if docker compose exec -T supportsense-airflow-apiserver \
        airflow dags list 2>/dev/null |
        grep -q "supportsense_ml_pipeline"; then

        pass "SupportSense Airflow DAG visible"
    else
        fail "SupportSense Airflow DAG not visible"
    fi
else
    fail "Airflow Compose configuration missing"
fi

echo

# ------------------------------------------------------------
# SupportSense event store / feedback / history
# ------------------------------------------------------------

echo "===== 13. EVENT STORE / FEEDBACK / HISTORY ====="
echo

echo "Event store persistence:"

if PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" python - <<'PYTHON'
import tempfile
from pathlib import Path

import src.monitoring.event_store as event_store

with tempfile.TemporaryDirectory() as tmp:
    database = Path(tmp) / "events.db"

    event_store.EVENT_DB = database

    event_store.initialize_event_store()

    event_id = event_store.record_prediction(
        ticket="Validation test ticket",
        predicted_intent="passcode_forgotten",
        model_name="validation-model",
        experiment_name="SupportSense Validation",
        run_id="validation-run",
        model_id="validation-model-id",
        model_status="READY",
        action_id="RESET_PASSCODE",
        action_name="Reset passcode",
        risk="MEDIUM",
        requires_approval=False,
    )

    event = event_store.get_prediction(event_id)

    if event is None:
        raise RuntimeError(
            "Prediction event was not persisted"
        )

    if event["predicted_intent"] != "passcode_forgotten":
        raise RuntimeError(
            "Persisted prediction intent is incorrect"
        )

    updated = event_store.update_prediction_outcome(
        event_id=event_id,
        actual_intent="passcode_forgotten",
        outcome="validation",
    )

    if updated is None:
        raise RuntimeError(
            "Prediction feedback update returned no event"
        )

    if updated["actual_intent"] != "passcode_forgotten":
        raise RuntimeError(
            "Actual intent was not persisted"
        )

    if updated["prediction_correct"] != 1:
        raise RuntimeError(
            "Prediction correctness was not calculated correctly"
        )

    events = event_store.list_predictions(limit=10)

    if not events:
        raise RuntimeError(
            "Prediction history is empty after persistence test"
        )

    print("Event ID :", event_id)
    print("Prediction:", event["predicted_intent"])
    print("Actual    :", updated["actual_intent"])
    print("Correct   :", updated["prediction_correct"])
    print("History   :", len(events))
PYTHON
then
    pass "Event store persistence and feedback"
else
    fail "Event store persistence and feedback"
fi

echo
echo "Prediction history API:"

HISTORY_RESPONSE="$(
    curl -sf "$RUNNER_URL/predictions?limit=1" 2>/dev/null || true
)"

if printf '%s' "$HISTORY_RESPONSE" |
    grep -q '"status":"success"' &&
    printf '%s' "$HISTORY_RESPONSE" |
    grep -q '"predictions"'; then

    echo "$HISTORY_RESPONSE"
    pass "Prediction history API"
else
    echo "$HISTORY_RESPONSE"
    fail "Prediction history API"
fi

echo
echo "Intent registry API:"

INTENTS_RESPONSE="$(
    curl -sf "$RUNNER_URL/intents" 2>/dev/null || true
)"

if printf '%s' "$INTENTS_RESPONSE" |
    grep -q '"status":"success"' &&
    printf '%s' "$INTENTS_RESPONSE" |
    grep -q '"intents"'; then

    echo "$INTENTS_RESPONSE" |
        python -c '
import json
import sys

body = json.load(sys.stdin)

print("Intent count:", body.get("count"))
'

    pass "Intent registry API"
else
    echo "$INTENTS_RESPONSE"
    fail "Intent registry API"
fi

echo
echo "Action simulation:"

ACTION_RESPONSE="$(
    curl -sf -X POST         "$RUNNER_URL/action/simulate"         -H "Content-Type: application/json"         -d '{"action_id":"RESET_PASSCODE"}'         2>/dev/null || true
)"

if printf '%s' "$ACTION_RESPONSE" |
    grep -q '"status":"simulated"' &&
    printf '%s' "$ACTION_RESPONSE" |
    grep -q '"action_id":"RESET_PASSCODE"'; then

    echo "$ACTION_RESPONSE"
    pass "Safe action simulation"
else
    echo "$ACTION_RESPONSE"
    fail "Safe action simulation"
fi

echo
echo "High-risk approval guard:"

APPROVAL_RESPONSE="$(
    curl -sf -X POST         "$RUNNER_URL/action/simulate"         -H "Content-Type: application/json"         -d '{"action_id":"TERMINATE_ACCOUNT"}'         2>/dev/null || true
)"

if printf '%s' "$APPROVAL_RESPONSE" |
    grep -q '"status":"approval_required"' &&
    printf '%s' "$APPROVAL_RESPONSE" |
    grep -q '"requires_approval":true'; then

    echo "$APPROVAL_RESPONSE"
    pass "High-risk approval guard"
else
    echo "$APPROVAL_RESPONSE"
    fail "High-risk approval guard"
fi

echo

# ------------------------------------------------------------
# Full test suite
# ------------------------------------------------------------

echo "===== 14. FULL PYTEST SUITE ====="
echo
echo "Runs the complete automated test suite, including"
echo "the lightweight Ray smoke integration tests."
echo

cd "$ROOT_DIR"

if pytest -q; then
    pass "Full pytest suite"
else
    fail "Full pytest suite"
fi

echo
echo "============================================================"

if [[ "$FAILURES" -eq 0 ]]; then
    echo " VALIDATION SUCCESSFUL"
    echo " All checks passed."
    echo "============================================================"
    exit 0
else
    echo " VALIDATION FAILED"
    echo " Failures: $FAILURES"
    echo "============================================================"
    exit 1
fi
