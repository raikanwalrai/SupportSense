# Spark Structured Streaming Troubleshooting

## Overview

This document records the Spark Structured Streaming troubleshooting
performed during SupportSense Sprint 7.

The intended pipeline is:

Kafka
  |
  v
Spark Structured Streaming
  |
  v
SupportSense Runner /predict
  |
  v
Prediction Event Store
  |
  v
Prometheus / Observability

The investigation established that Spark itself was operational. The primary
issue was the SupportSense development-service lifecycle configuration:
incorrect path resolution and inherited environment variables affected Spark
process ownership and service management.

## 1. Initial Symptoms

Spark appeared to be running:

    python -m src.streaming.spark_streaming

The process was:

    PID 36587
    python -m src.streaming.spark_streaming

However, SupportSense reported:

    SPARK STREAMING
    Status: RUNNING
    PID: 36587

while simultaneously reporting:

    SPARK HEALTH
    No Spark health file.

This indicated that a Spark process existed but was not being correctly
managed by the SupportSense development environment.

## 2. Spark and Kafka Compatibility Verification

The environment was checked before changing the Spark application.

Observed versions:

- PySpark: 4.1.2
- Spark: 4.1.2
- Java: OpenJDK 17.0.19
- Scala: 2.13.17

The application uses:

    org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.2

Historical Spark logs confirmed successful dependency resolution:

    found org.apache.spark#spark-sql-kafka-0-10_2.13;4.1.2 in central
    found org.apache.kafka#kafka-clients;3.9.1 in central

Therefore, no Spark/Kafka version incompatibility was identified.

## 3. Evidence That Spark Streaming Worked

A real Kafka event was published:

    Event ID:
    d0370372-0720-4a49-8689-12e668a9252b

    Ticket:
    I was charged twice for the same card purchase

Kafka reported:

    Partition: 1
    Offset: 9

Spark subsequently reported:

    status=healthy
    pid=49750
    batch_id=10
    tickets=1

The resulting prediction was:

    Intent:
    transaction_charged_twice

    Action:
    Investigate duplicate charge

    Risk:
    MEDIUM

The prediction retained:

    source_event_id =
    d0370372-0720-4a49-8689-12e668a9252b

This established that:

    Kafka -> Spark -> Runner -> Prediction Store

was operational.

## 4. Actual Root Cause

The problem was found in:

    scripts/lib/dev-config.sh

The configuration defines paths using $ROOT_DIR, including:

    SPARK_PID_FILE
    SPARK_LOG_FILE
    KAFKA_COMPOSE_FILE

When the configuration was sourced without first establishing the repository
root, the resulting values were incorrect:

    ROOT_DIR=
    SPARK_PID_FILE=/.dev/spark-streaming.pid
    SPARK_LOG_FILE=/.dev/spark-streaming.log
    KAFKA_COMPOSE_FILE=/docker/kafka/docker-compose.yaml

The correct repository paths should be under:

    /home/kanwa/projects/SupportSense

## 5. Effect on Spark Process Ownership

The actual SupportSense Spark process was:

    PID 36587
    python -m src.streaming.spark_streaming

The ownership function correctly recognized it:

    supportsense_process_matches
    MATCH = YES

However, stop-dev.sh was checking the incorrect PID-file location:

    /.dev/spark-streaming.pid

instead of:

    /home/kanwa/projects/SupportSense/.dev/spark-streaming.pid

Consequently, stop-dev.sh reported:

    No SupportSense Spark PID recorded.
    Any externally managed Spark Streaming is left untouched.

The process was therefore left running.

## 6. Environment Variable Contamination

The shell contained inherited overrides:

    SPARK_PID_FILE=/.dev/spark-streaming.pid
    SPARK_LOG_FILE=/.dev/spark-streaming.log
    KAFKA_COMPOSE_FILE=/docker/kafka/docker-compose.yaml

Because dev-config.sh uses:

    ${VARIABLE:-default}

existing environment variables take precedence over the intended defaults.

The incorrect overrides were removed:

    unset SPARK_PID_FILE
    unset SPARK_LOG_FILE
    unset KAFKA_COMPOSE_FILE

After cleanup:

    No contaminated overrides

## 7. Correct Shutdown

After removing the incorrect environment overrides, stop-dev.sh was executed.

The result was:

    Spark Streaming stopped (PID 36587).

The subsequent process check confirmed:

    No SupportSense Spark process

The repository PID file was also removed.

## 8. Clean Restart

The development environment was started again.

Spark reported:

    Spark Streaming started (PID 49750).
    Ownership: SupportSense.
    Spark Streaming health: OK

The official observability command reported:

    Status: RUNNING
    PID: 49750

and the health file reported:

    status=healthy
    pid=49750

This confirmed that Spark was both running and correctly managed.

## 9. End-to-End Streaming Validation

A new Kafka event was processed successfully.

Spark reported:

    batch_id=10
    tickets=1

The resulting prediction was:

    transaction_charged_twice

with the corresponding Kafka event ID preserved as:

    source_event_id

This demonstrated event-level correlation across:

    Kafka
      |
      v
    Spark
      |
      v
    Runner /predict
      |
      v
    Prediction Event Store

## 10. Prometheus Validation

The Runner exposed Prometheus metrics.

Prometheus successfully scraped the Runner target:

    up{job="supportsense-runner"} = 1

A successful /predict request increased the observed request counter.

The successful prediction counter also increased.

The /predict latency histogram produced a valid P95 measurement of
approximately:

    0.235 seconds

Therefore the operational observability path was validated.

## 11. Important Distinction

The investigation should not be summarized as:

    Spark was broken.

The evidence supports the more precise conclusion:

    Spark 4.1.2, Java 17, the Spark Kafka connector, Kafka, and the streaming
    application were operational. The primary issue was incorrect SupportSense
    development-environment configuration and inherited environment variables,
    which caused service-management files to be resolved at incorrect paths.

No Spark/Kafka compatibility change was required.

## 12. Recovery Procedure

If the same symptom occurs in the future:

### Check overrides

    env | grep -E '^SPARK_(PID|LOG)_FILE=|^KAFKA_COMPOSE_FILE='

### Remove incorrect overrides

    unset SPARK_PID_FILE
    unset SPARK_LOG_FILE
    unset KAFKA_COMPOSE_FILE

### Verify the repository PID file

    ls -l .dev/spark-streaming.pid

### Verify the Spark process

    ps aux | grep '[s]rc.streaming.spark_streaming'

### Stop using the official SupportSense script

    ./scripts/lib/stop-dev.sh

### Start cleanly

    ./scripts/lib/start-dev.sh

### Verify streaming

    ./scripts/supportsense.sh stream

### Produce a test event

    python -m src.streaming.producer \
      --ticket "I was charged twice for the same card purchase" \
      --source "sprint-7-streaming-test" \
      --topic supportsense.tickets \
      --bootstrap-servers localhost:9092

### Verify the resulting prediction

    ./scripts/supportsense.sh stream

The Kafka event ID should match the prediction source_event_id.

## 13. Final Status

At the end of the investigation:

- Spark 4.1.2 -> operational
- Java 17 -> operational
- Spark Kafka connector -> resolved successfully
- Kafka -> operational
- Spark Structured Streaming -> operational
- Spark process ownership -> operational after environment cleanup
- Spark health file -> operational
- Kafka -> Spark -> Runner -> prediction flow -> validated
- Kafka event ID -> prediction source_event_id correlation -> validated
- Prometheus Runner scraping -> validated
- Prediction metrics -> validated
- Prediction latency metrics -> validated

The issue was resolved through development-environment configuration cleanup
and correct SupportSense service lifecycle management.
