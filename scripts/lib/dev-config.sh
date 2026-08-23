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

# Kafka development configuration.
export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
export KAFKA_TOPIC="${KAFKA_TOPIC:-supportsense.tickets}"
export KAFKA_COMPOSE_FILE="${KAFKA_COMPOSE_FILE:-$ROOT_DIR/docker/kafka/docker-compose.yaml}"
export KAFKA_CONTAINER_NAME="${KAFKA_CONTAINER_NAME:-supportsense-kafka}"

# Spark Structured Streaming development configuration.
export SPARK_HEALTH_FILE="${SPARK_HEALTH_FILE:-/tmp/supportsense-spark-streaming.health}"
export SPARK_PID_FILE="${SPARK_PID_FILE:-$ROOT_DIR/.dev/spark-streaming.pid}"
export SPARK_LOG_FILE="${SPARK_LOG_FILE:-$ROOT_DIR/.dev/spark-streaming.log}"
export SPARK_RUNNER_URL="${SPARK_RUNNER_URL:-$RUNNER_URL}"


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
