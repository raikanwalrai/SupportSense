#!/usr/bin/env bash

# ============================================================
# SupportSense Development Configuration
# ============================================================
#
# Non-secret development configuration.
#
# Secrets must NEVER be placed here.
#
# MLFLOW_URL:
#   Used by shell scripts for service health checks.
#
# MLFLOW_TRACKING_URI:
#   Used by Python/MLflow clients for experiment tracking.
#
# These are intentionally separate variables because they serve
# different application layers.
# ============================================================

export MLFLOW_URL="${MLFLOW_URL:-http://127.0.0.1:5000}"
export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-$MLFLOW_URL}"

export RUNNER_URL="${RUNNER_URL:-http://127.0.0.1:8000}"
export AIRFLOW_URL="${AIRFLOW_URL:-http://127.0.0.1:18080}"
export PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
export GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"


supportsense_pid_is_running() {
    local pid="$1"

    [[ "$pid" =~ ^[0-9]+$ ]] || return 1
    kill -0 "$pid" 2>/dev/null
}


supportsense_process_matches() {
    local pid="$1"
    local expected="$2"

    [[ "$pid" =~ ^[0-9]+$ ]] || return 1
    kill -0 "$pid" 2>/dev/null || return 1

    ps -p "$pid" -o args= 2>/dev/null |
        grep -F -- "$expected" >/dev/null
}
