#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# STOP SCRIPT
# ============================================================
#
# Stops services managed by start-dev.sh.
#
# Stops:
#   - Spark Structured Streaming started by SupportSense
#   - Kafka Docker Compose services
#   - MLflow process started by SupportSense
#   - SupportSense Runner started by SupportSense
#   - Prometheus Docker Compose services
#   - Grafana Docker Compose services
#   - Airflow Docker Compose services
#
# Docker volumes are NOT deleted.
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT_DIR/scripts/lib/dev-config.sh"

AIRFLOW_DIR="$ROOT_DIR/airflow"
PROMETHEUS_DIR="$ROOT_DIR/monitoring/prometheus"
GRAFANA_DIR="$ROOT_DIR/monitoring/grafana"
DEV_DIR="$ROOT_DIR/.dev"

MLFLOW_PID_FILE="$DEV_DIR/mlflow.pid"
RUNNER_PID_FILE="$DEV_DIR/runner.pid"

echo "============================================================"
echo " SupportSense Development Environment"
echo " STOP"
echo "============================================================"
echo

# ------------------------------------------------------------
# Stop Spark Streaming
# ------------------------------------------------------------

echo "[1/7] Stopping Spark Streaming..."

if [[ -f "$SPARK_PID_FILE" ]]; then
    pid="$(cat "$SPARK_PID_FILE" 2>/dev/null || true)"

    if supportsense_process_matches "$pid" "src.streaming.spark_streaming"; then
        kill "$pid" 2>/dev/null || true

        for _ in {1..15}; do
            if ! supportsense_pid_is_running "$pid"; then
                break
            fi
            sleep 1
        done

        if supportsense_pid_is_running "$pid"; then
            echo "      Spark Streaming did not stop gracefully."
            echo "      Terminating PID $pid."
            kill -TERM "$pid" 2>/dev/null || true
        fi

        echo "      Spark Streaming stopped (PID $pid)."
    else
        echo "      Spark PID is not a SupportSense-owned process."
        echo "      Leaving Spark Streaming running."
    fi

    rm -f "$SPARK_PID_FILE"
else
    echo "      No SupportSense Spark PID recorded."
    echo "      Any externally managed Spark Streaming is left untouched."
fi

rm -f "$SPARK_HEALTH_FILE"

echo

# ------------------------------------------------------------
# Stop Kafka
# ------------------------------------------------------------

echo "[2/7] Stopping Kafka Docker Compose stack..."

if [[ -f "$KAFKA_COMPOSE_FILE" ]]; then
    KAFKA_DIR="$(dirname "$KAFKA_COMPOSE_FILE")"

    cd "$KAFKA_DIR"

    docker compose stop

    echo "      Kafka services stopped."
    echo "      Docker volumes were preserved."
else
    echo "      Kafka Compose file not found; skipping."
fi

echo

# ------------------------------------------------------------
# Stop MLflow
# ------------------------------------------------------------

echo "[3/7] Stopping MLflow..."

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

echo "[4/7] Stopping SupportSense Runner..."

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

echo "[5/7] Stopping Prometheus Docker Compose stack..."

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

echo "[6/7] Stopping Grafana Docker Compose stack..."

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

echo "[7/7] Stopping Airflow Docker Compose stack..."

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
