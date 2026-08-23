#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# STREAMING OBSERVABILITY
# ============================================================
#
# Read-only operational view of:
#
#   Kafka -> Spark -> Runner -> Prediction Store
#
# This script NEVER:
#   - starts/stops services
#   - joins a Kafka consumer group
#   - commits Kafka offsets
#   - modifies application data
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT_DIR/scripts/lib/dev-config.sh"

echo "============================================================"
echo " SupportSense Streaming"
echo " OBSERVABILITY"
echo "============================================================"
echo

# ------------------------------------------------------------
# Kafka broker
# ------------------------------------------------------------

echo "===== KAFKA ====="

KAFKA_STATUS="$(
    docker inspect "$KAFKA_CONTAINER_NAME" \
        --format '{{.State.Status}}' 2>/dev/null || true
)"

if [[ "$KAFKA_STATUS" == "running" ]]; then
    echo "Status:       HEALTHY"
else
    echo "Status:       ${KAFKA_STATUS:-NOT FOUND}"
fi

echo "Container:    $KAFKA_CONTAINER_NAME"
echo "Bootstrap:    $KAFKA_BOOTSTRAP_SERVERS"
echo "Topic:        $KAFKA_TOPIC"

echo

# ------------------------------------------------------------
# Kafka topic metadata
# ------------------------------------------------------------

echo "===== KAFKA TOPIC ====="

if [[ "$KAFKA_STATUS" == "running" ]]; then

    TOPIC_INFO="$(
        docker exec "$KAFKA_CONTAINER_NAME" \
            /opt/kafka/bin/kafka-topics.sh \
            --describe \
            --topic "$KAFKA_TOPIC" \
            --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
            2>/dev/null || true
    )"

    if [[ -n "$TOPIC_INFO" ]]; then
        echo "$TOPIC_INFO"
    else
        echo "Topic metadata unavailable."
    fi
else
    echo "Kafka is not running."
fi

echo

# ------------------------------------------------------------
# Kafka log-end offsets
# ------------------------------------------------------------

echo "===== KAFKA PARTITION OFFSETS ====="

if [[ "$KAFKA_STATUS" == "running" ]]; then

    OFFSET_INFO="$(
        docker exec "$KAFKA_CONTAINER_NAME" \
            /opt/kafka/bin/kafka-get-offsets.sh \
            --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
            --topic "$KAFKA_TOPIC" \
            2>/dev/null || true
    )"

    if [[ -n "$OFFSET_INFO" ]]; then
        echo "$OFFSET_INFO"
    else
        echo "Kafka offsets unavailable."
    fi
else
    echo "Kafka is not running."
fi

echo

# ------------------------------------------------------------
# Spark process
# ------------------------------------------------------------

echo "===== SPARK STREAMING ====="

SPARK_PID=""

if [[ -f "$SPARK_PID_FILE" ]]; then
    SPARK_PID="$(cat "$SPARK_PID_FILE" 2>/dev/null || true)"
fi

if [[ -n "$SPARK_PID" ]] &&
   ps -p "$SPARK_PID" -o args= 2>/dev/null |
   grep -q 'src.streaming.spark_streaming'; then

    echo "Status:       RUNNING"
    echo "PID:          $SPARK_PID"
else
    echo "Status:       NOT RUNNING"
fi

echo

# ------------------------------------------------------------
# Spark health
# ------------------------------------------------------------

echo "===== SPARK HEALTH ====="

if [[ -f "$SPARK_HEALTH_FILE" ]]; then
    cat "$SPARK_HEALTH_FILE"
else
    echo "No Spark health file."
fi

echo

# ------------------------------------------------------------
# Recent Spark log
# ------------------------------------------------------------

echo "===== RECENT SPARK LOG ====="

if [[ -f "$SPARK_LOG_FILE" ]]; then
    tail -20 "$SPARK_LOG_FILE"
else
    echo "No Spark log file."
fi

echo

# ------------------------------------------------------------
# Recent predictions
# ------------------------------------------------------------

echo "===== RECENT PREDICTIONS ====="

PREDICTIONS_JSON="$(
    curl -fsS \
        "$RUNNER_URL/predictions?limit=5" \
        2>/dev/null || true
)"

if [[ -z "$PREDICTIONS_JSON" ]]; then
    echo "Prediction API unavailable."
else
    PREDICTIONS_JSON="$PREDICTIONS_JSON" python3 - <<'PY'
import json
import os

try:
    payload = json.loads(os.environ["PREDICTIONS_JSON"])
except json.JSONDecodeError:
    print("Prediction API returned invalid JSON.")
    raise SystemExit(0)

predictions = payload.get("predictions", [])

if not predictions:
    print("No predictions available.")
    raise SystemExit(0)

for index, item in enumerate(predictions, start=1):
    print(f"[{index}]")
    print(f"  Prediction event : {item.get('event_id')}")
    print(f"  Source event     : {item.get('source_event_id')}")
    print(f"  Ticket           : {item.get('ticket')}")
    print(f"  Intent           : {item.get('predicted_intent')}")
    print(f"  Action           : {item.get('action_name')}")
    print(f"  Risk             : {item.get('risk')}")
    print()
PY
fi

echo

# ------------------------------------------------------------
# Pipeline summary
# ------------------------------------------------------------

echo "===== PIPELINE ====="

echo "Kafka"
echo "  $KAFKA_TOPIC"
echo "       |"
echo "       v"
echo "Spark Structured Streaming"
echo "       |"
echo "       v"
echo "Runner /predict"
echo "       |"
echo "       v"
echo "Prediction Event Store"
echo "       |"
echo "       v"
echo "Runner /predictions"

echo

echo "===== CORRELATION ====="
echo "Kafka event_id = prediction source_event_id"
echo "This correlation is established by Spark before calling"
echo "the Runner /predict endpoint."

echo
echo "============================================================"
echo " STREAMING OBSERVABILITY COMPLETE"
echo "============================================================"
