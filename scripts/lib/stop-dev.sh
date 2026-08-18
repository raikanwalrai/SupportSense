#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# STOP SCRIPT
# ============================================================
#
# Stops services managed by start-dev.sh.
#
# Stops:
#   - MLflow process started by SupportSense
#   - SupportSense Runner started by SupportSense
#   - Airflow Docker Compose services
#
# Docker volumes are NOT deleted.
#
# This means database state, Airflow metadata and other
# persistent development state are preserved.
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AIRFLOW_DIR="$ROOT_DIR/airflow"
DEV_DIR="$ROOT_DIR/.dev"

MLFLOW_PID_FILE="$DEV_DIR/mlflow.pid"
RUNNER_PID_FILE="$DEV_DIR/runner.pid"

echo "============================================================"
echo " SupportSense Development Environment"
echo " STOP"
echo "============================================================"
echo

# ------------------------------------------------------------
# Stop MLflow
# ------------------------------------------------------------

echo "[1/3] Stopping MLflow..."

if [[ -f "$MLFLOW_PID_FILE" ]]; then
    pid="$(cat "$MLFLOW_PID_FILE" 2>/dev/null || true)"

    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        echo "      MLflow stopped (PID $pid)."
    else
        echo "      MLflow process is not running."
    fi

    rm -f "$MLFLOW_PID_FILE"
else
    echo "      No SupportSense MLflow PID recorded."
fi

echo

# ------------------------------------------------------------
# Stop Runner
# ------------------------------------------------------------

echo "[2/3] Stopping SupportSense Runner..."

if [[ -f "$RUNNER_PID_FILE" ]]; then
    pid="$(cat "$RUNNER_PID_FILE" 2>/dev/null || true)"

    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        echo "      Runner stopped (PID $pid)."
    else
        echo "      Runner process is not running."
    fi

    rm -f "$RUNNER_PID_FILE"
else
    echo "      No SupportSense Runner PID recorded."
fi

echo

# ------------------------------------------------------------
# Stop Airflow
# ------------------------------------------------------------

echo "[3/3] Stopping Airflow Docker Compose stack..."

if [[ -f "$AIRFLOW_DIR/docker-compose.yaml" ]]; then
    cd "$AIRFLOW_DIR"

    docker compose stop

    echo "      Airflow services stopped."
    echo "      Docker volumes were preserved."
else
    echo "      Airflow Compose file not found; skipping."
fi

echo
echo "============================================================"
echo " SupportSense development environment STOPPED"
echo "============================================================"
