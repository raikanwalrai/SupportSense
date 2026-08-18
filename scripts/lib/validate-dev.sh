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
#   1. Python environment
#   2. Core package imports
#   3. pip dependency consistency
#   4. DVC status
#   5. MLflow health
#   6. Runner health
#   7. Airflow health
#   8. Airflow DAG visibility
#   9. Full pytest suite
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
AIRFLOW_DIR="$ROOT_DIR/airflow"

MLFLOW_URL="http://127.0.0.1:5000"
RUNNER_URL="http://127.0.0.1:8000"
AIRFLOW_URL="http://127.0.0.1:18080"

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
# pip check
# ------------------------------------------------------------

echo "===== 3. DEPENDENCY CONSISTENCY ====="

if pip check; then
    pass "pip check"
else
    fail "pip check"
fi

echo

# ------------------------------------------------------------
# DVC
# ------------------------------------------------------------

echo "===== 4. DVC ====="

if dvc status; then
    pass "DVC pipeline/data state"
else
    fail "DVC status"
fi

echo

# ------------------------------------------------------------
# MLflow
# ------------------------------------------------------------

echo "===== 5. MLFLOW ====="

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

echo "===== 6. SUPPORTSENSE RUNNER ====="

if curl -sf "$RUNNER_URL/health"; then
    echo
    pass "Runner health"
else
    fail "Runner health"
fi

echo

# ------------------------------------------------------------
# Airflow health
# ------------------------------------------------------------

echo "===== 7. AIRFLOW HEALTH ====="

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

echo "===== 8. AIRFLOW DAG ====="

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
# Full test suite
# ------------------------------------------------------------

echo "===== 9. FULL PYTEST SUITE ====="
echo
echo "This may take several minutes because Ray experiments are"
echo "included in the test suite."
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
