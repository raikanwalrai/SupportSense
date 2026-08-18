#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# START SCRIPT
# ============================================================
#
# Starts all services required for the current development
# environment.
#
# Current services:
#
#   1. MLflow
#      Local experiment tracking server
#      http://127.0.0.1:5000
#
#   2. SupportSense Runner
#      FastAPI execution service
#      http://127.0.0.1:8000
#
#   3. Airflow
#      Docker Compose orchestration environment
#      http://127.0.0.1:18080
#
# Airflow itself runs inside Docker.
#
# MLflow and the Runner currently run as local WSL processes.
#
# Future sprints will progressively move additional services
# into the appropriate container/Kubernetes architecture.
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT_DIR/scripts/lib/dev-config.sh"
AIRFLOW_DIR="$ROOT_DIR/airflow"
DEV_DIR="$ROOT_DIR/.dev"

MLFLOW_PID_FILE="$DEV_DIR/mlflow.pid"
RUNNER_PID_FILE="$DEV_DIR/runner.pid"

MLFLOW_LOG="$DEV_DIR/mlflow.log"
RUNNER_LOG="$DEV_DIR/runner.log"


mkdir -p "$DEV_DIR"

echo "============================================================"
echo " SupportSense Development Environment"
echo " START"
echo "============================================================"
echo
echo "Project: $ROOT_DIR"
echo

# ------------------------------------------------------------
# Basic checks
# ------------------------------------------------------------

if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    echo "ERROR: Python virtual environment not found:"
    echo "       $ROOT_DIR/.venv"
    echo
    echo "Create it first or restore the project environment."
    exit 1
fi

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "WARNING: .venv is not currently activated."
    echo
    echo "Recommended:"
    echo "    source .venv/bin/activate"
    echo
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not available."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not reachable."
    echo "Start Docker Desktop and try again."
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl is required."
    exit 1
fi

# ------------------------------------------------------------
# Python / MLflow
# ------------------------------------------------------------

echo "[1/3] Starting MLflow..."

if curl -sf "$MLFLOW_URL/version" >/dev/null 2>&1; then
    echo "      MLflow is already running."

    if [[ -f "$MLFLOW_PID_FILE" ]]; then
        pid="$(cat "$MLFLOW_PID_FILE" 2>/dev/null || true)"

        if supportsense_process_matches "$pid" ".venv/bin/mlflow server"; then
            echo "      Ownership: SupportSense."
        else
            echo "      Ownership: External."
            rm -f "$MLFLOW_PID_FILE"
        fi
    else
        echo "      Ownership: External/pre-existing."
    fi
else
    if [[ -f "$MLFLOW_PID_FILE" ]]; then
        old_pid="$(cat "$MLFLOW_PID_FILE" 2>/dev/null || true)"

        if supportsense_process_matches "$old_pid" ".venv/bin/mlflow server"; then
            echo "      MLflow process already exists (PID $old_pid)."
        else
            rm -f "$MLFLOW_PID_FILE"
        fi
    fi

    if [[ ! -f "$MLFLOW_PID_FILE" ]]; then
        cd "$ROOT_DIR"

        nohup mlflow server \
            --host 127.0.0.1 \
            --port 5000 \
            --backend-store-uri "sqlite:///$ROOT_DIR/mlflow.db" \
            --default-artifact-root "$ROOT_DIR/mlruns" \
            --artifacts-destination "$ROOT_DIR/mlartifacts" \
            > "$MLFLOW_LOG" 2>&1 &

        echo $! > "$MLFLOW_PID_FILE"

        echo "      MLflow started (PID $(cat "$MLFLOW_PID_FILE"))."
        echo "      Ownership: SupportSense."
        echo "      Log: $MLFLOW_LOG"
    fi
fi

# Wait for MLflow
for i in {1..30}; do
    if curl -sf "$MLFLOW_URL/version" >/dev/null 2>&1; then
        echo "      MLflow health: OK"
        break
    fi

    if [[ "$i" -eq 30 ]]; then
        echo "ERROR: MLflow did not become healthy."
        echo "Check:"
        echo "    $MLFLOW_LOG"
        exit 1
    fi

    sleep 1
done

echo

# ------------------------------------------------------------
# SupportSense Runner
# ------------------------------------------------------------

echo "[2/3] Starting SupportSense Runner..."

if curl -sf "$RUNNER_URL/health" >/dev/null 2>&1; then
    echo "      Runner is already running."

    if [[ -f "$RUNNER_PID_FILE" ]]; then
        pid="$(cat "$RUNNER_PID_FILE" 2>/dev/null || true)"

        if supportsense_process_matches "$pid" "services.runner:app"; then
            echo "      Ownership: SupportSense."
        else
            echo "      Ownership: External."
            rm -f "$RUNNER_PID_FILE"
        fi
    else
        echo "      Ownership: External/pre-existing."
    fi
else
    if [[ -f "$RUNNER_PID_FILE" ]]; then
        old_pid="$(cat "$RUNNER_PID_FILE" 2>/dev/null || true)"

        if supportsense_process_matches "$old_pid" "services.runner:app"; then
            echo "      Runner process already exists (PID $old_pid)."
        else
            rm -f "$RUNNER_PID_FILE"
        fi
    fi

    if [[ ! -f "$RUNNER_PID_FILE" ]]; then
        cd "$ROOT_DIR"

        nohup python -m uvicorn services.runner:app \
            --host 0.0.0.0 \
            --port 8000 \
            > "$RUNNER_LOG" 2>&1 &

        echo $! > "$RUNNER_PID_FILE"

        echo "      Runner started (PID $(cat "$RUNNER_PID_FILE"))."
        echo "      Ownership: SupportSense."
        echo "      Log: $RUNNER_LOG"
    fi
fi

# Wait for Runner
for i in {1..30}; do
    if curl -sf "$RUNNER_URL/health" >/dev/null 2>&1; then
        echo "      Runner health: OK"
        break
    fi

    if [[ "$i" -eq 30 ]]; then
        echo "ERROR: Runner did not become healthy."
        echo "Check:"
        echo "    $RUNNER_LOG"
        exit 1
    fi

    sleep 1
done

echo

# ------------------------------------------------------------
# Prometheus
# ------------------------------------------------------------

echo "[3/4] Starting Prometheus..."

PROMETHEUS_DIR="$ROOT_DIR/monitoring/prometheus"

if [[ ! -f "$PROMETHEUS_DIR/docker-compose.yml" ]]; then
    echo "ERROR: Prometheus Compose file not found:"
    echo "       $PROMETHEUS_DIR/docker-compose.yml"
    exit 1
fi

cd "$PROMETHEUS_DIR"

docker compose up -d

echo
echo "      Prometheus Docker Compose started."

for i in {1..30}; do
    if curl -sf "$PROMETHEUS_URL/-/healthy" >/dev/null 2>&1; then
        echo "      Prometheus health: OK"
        break
    fi

    if [[ "$i" -eq 30 ]]; then
        echo "WARNING: Prometheus did not report healthy within the wait period."
        echo "Check:"
        echo "    cd $PROMETHEUS_DIR"
        echo "    docker compose ps"
        echo "    docker compose logs --tail=100"
        break
    fi

    sleep 2
done

echo

# ------------------------------------------------------------
# Airflow
# ------------------------------------------------------------

echo "[4/4] Starting Airflow Docker Compose stack..."

if [[ ! -f "$AIRFLOW_DIR/docker-compose.yaml" ]]; then
    echo "ERROR: Airflow Compose file not found:"
    echo "       $AIRFLOW_DIR/docker-compose.yaml"
    exit 1
fi

cd "$AIRFLOW_DIR"

docker compose up -d

echo
echo "      Airflow Docker Compose started."

# Wait for Airflow health endpoint
for i in {1..60}; do
    if curl -sf "$AIRFLOW_URL/api/v2/monitor/health" >/dev/null 2>&1; then
        echo "      Airflow health: OK"
        break
    fi

    if [[ "$i" -eq 60 ]]; then
        echo "WARNING: Airflow did not report healthy within the wait period."
        echo "Check:"
        echo "    cd $AIRFLOW_DIR"
        echo "    docker compose ps"
        echo "    docker compose logs --tail=100"
        break
    fi

    sleep 2
done

echo
echo "============================================================"
echo " SupportSense development environment STARTED"
echo "============================================================"
echo
echo "MLflow:"
echo "    $MLFLOW_URL"
echo
echo "Runner:"
echo "    $RUNNER_URL/health"
echo
echo "Airflow:"
echo "    $AIRFLOW_URL"
echo
echo "Next recommended command:"
echo "    ./scripts/supportsense.sh status"
echo
