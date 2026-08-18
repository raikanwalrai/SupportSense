#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# STATUS SCRIPT
# ============================================================
#
# Reports the current state of:
#
#   - Python environment
#   - MLflow
#   - Runner
#   - Airflow
#   - DVC
#   - Docker
#
# This script does NOT modify the environment.
#
# ============================================================

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AIRFLOW_DIR="$ROOT_DIR/airflow"
DEV_DIR="$ROOT_DIR/.dev"

MLFLOW_URL="http://127.0.0.1:5000"
RUNNER_URL="http://127.0.0.1:8000"
AIRFLOW_URL="http://127.0.0.1:18080"

echo "============================================================"
echo " SupportSense Development Environment"
echo " STATUS"
echo "============================================================"
echo
echo "Project:"
echo "    $ROOT_DIR"
echo

# ------------------------------------------------------------
# Git
# ------------------------------------------------------------

echo "===== GIT ====="

cd "$ROOT_DIR"

echo "Branch:"
git branch --show-current 2>/dev/null || echo "unknown"

echo
echo "Working tree:"
if [[ -z "$(git status --short 2>/dev/null)" ]]; then
    echo "    CLEAN"
else
    git status --short
fi

echo

# ------------------------------------------------------------
# Python
# ------------------------------------------------------------

echo "===== PYTHON ====="

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    echo "Virtual environment:"
    echo "    $VIRTUAL_ENV"
else
    echo "Virtual environment:"
    echo "    NOT ACTIVATED"
fi

python --version 2>/dev/null || echo "Python unavailable"

echo

# ------------------------------------------------------------
# Docker
# ------------------------------------------------------------

echo "===== DOCKER ====="

if command -v docker >/dev/null 2>&1; then
    docker --version
    echo

    if docker info >/dev/null 2>&1; then
        echo "Docker daemon: HEALTHY"
    else
        echo "Docker daemon: NOT AVAILABLE"
    fi
else
    echo "Docker: NOT INSTALLED"
fi

echo

# ------------------------------------------------------------
# MLflow
# ------------------------------------------------------------

echo "===== MLFLOW ====="

if curl -sf "$MLFLOW_URL/version" >/dev/null 2>&1; then
    echo "MLflow: HEALTHY"
    echo "URL: $MLFLOW_URL"
else
    echo "MLflow: NOT RUNNING"
fi

if [[ -f "$DEV_DIR/mlflow.pid" ]]; then
    echo "PID: $(cat "$DEV_DIR/mlflow.pid")"
fi

echo

# ------------------------------------------------------------
# Runner
# ------------------------------------------------------------

echo "===== SUPPORTSENSE RUNNER ====="

if curl -sf "$RUNNER_URL/health" >/dev/null 2>&1; then
    echo "Runner: HEALTHY"
    echo "URL: $RUNNER_URL/health"
else
    echo "Runner: NOT RUNNING"
fi

if [[ -f "$DEV_DIR/runner.pid" ]]; then
    echo "PID: $(cat "$DEV_DIR/runner.pid")"
fi

echo

# ------------------------------------------------------------
# Airflow
# ------------------------------------------------------------

echo "===== AIRFLOW ====="

if [[ -f "$AIRFLOW_DIR/docker-compose.yaml" ]]; then
    cd "$AIRFLOW_DIR"

    docker compose ps

    echo

    if curl -sf "$AIRFLOW_URL/api/v2/monitor/health" >/dev/null 2>&1; then
        echo "Airflow API health: HEALTHY"
    else
        echo "Airflow API health: NOT HEALTHY"
    fi
else
    echo "Airflow Compose configuration not found."
fi

echo

# ------------------------------------------------------------
# DVC
# ------------------------------------------------------------

echo "===== DVC ====="

cd "$ROOT_DIR"

if command -v dvc >/dev/null 2>&1; then
    dvc --version
    echo
    dvc status
else
    echo "DVC unavailable in current environment."
fi

echo
echo "============================================================"
echo " STATUS COMPLETE"
echo "============================================================"
