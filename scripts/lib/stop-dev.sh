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
#   - Prometheus Docker Compose services
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
source "$ROOT_DIR/scripts/lib/dev-config.sh"
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

echo "[1/5] Stopping MLflow..."

if [[ -f "$MLFLOW_PID_FILE" ]]; then
    pid="$(cat "$MLFLOW_PID_FILE" 2>/dev/null || true)"

    if supportsense_process_matches "$pid" ".venv/bin/mlflow server"; then
        kill "$pid" 2>/dev/null || true
        echo "      MLflow stopped (PID $pid)."
        rm -f "$MLFLOW_PID_FILE"
    else
        echo "      MLflow PID is not a SupportSense-owned process."
        echo "      Leaving MLflow running."
        rm -f "$MLFLOW_PID_FILE"
    fi
else
    echo "      No SupportSense MLflow PID recorded."
    echo "      Any externally managed MLflow is left untouched."
fi
echo

# ------------------------------------------------------------
# Stop Runner
# ------------------------------------------------------------

echo "[2/5] Stopping SupportSense Runner..."

if [[ -f "$RUNNER_PID_FILE" ]]; then
    pid="$(cat "$RUNNER_PID_FILE" 2>/dev/null || true)"

    if supportsense_process_matches "$pid" "services.runner:app"; then
        kill "$pid" 2>/dev/null || true
        echo "      Runner stopped (PID $pid)."
        rm -f "$RUNNER_PID_FILE"
    else
        echo "      Runner PID is not a SupportSense-owned process."
        echo "      Leaving Runner running."
        rm -f "$RUNNER_PID_FILE"
    fi
else
    echo "      No SupportSense Runner PID recorded."
    echo "      Any externally managed Runner is left untouched."
fi
echo

# ------------------------------------------------------------
# Stop Prometheus
# ------------------------------------------------------------

echo "[3/5] Stopping Prometheus Docker Compose stack..."

PROMETHEUS_DIR="$ROOT_DIR/monitoring/prometheus"

if [[ -f "$PROMETHEUS_DIR/docker-compose.yml" ]]; then
    cd "$PROMETHEUS_DIR"

    docker compose stop

    echo "      Prometheus services stopped."
    echo "      Docker volumes were preserved."
else
    echo "      Prometheus Compose file not found; skipping."
fi
echo

# ------------------------------------------------------------
# Stop Grafana
# ------------------------------------------------------------

echo "[4/5] Stopping Grafana Docker Compose stack..."

GRAFANA_DIR="$ROOT_DIR/monitoring/grafana"

if [[ -f "$GRAFANA_DIR/docker-compose.yml" ]]; then
    cd "$GRAFANA_DIR"

    docker compose stop

    echo "      Grafana services stopped."
    echo "      Docker volumes were preserved."
else
    echo "      Grafana Compose file not found; skipping."
fi
echo

# ------------------------------------------------------------
# Stop Airflow
# ------------------------------------------------------------

echo "[5/5] Stopping Airflow Docker Compose stack..."

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
