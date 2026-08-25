# SupportSense — Sprint 7 Checkpoint

**Sprint:** 7
**Branch:** `feature/sprint-7-observability`
**Checkpoint date:** 2026-08-23
**Status:** COMPLETED — CHECKPOINT CLOSED

---

## 1. Sprint Objective

Sprint 7 established and verified the real-time ticket-processing path for SupportSense while preserving the existing manual prediction workflow.

The sprint also strengthened developer observability, Git safety, CI verification, and operational developer tooling.

The verified architecture is:

```text
Customer Ticket
      |
      v
Kafka
      |
      v
Spark Structured Streaming
      |
      v
SupportSense Runner /predict
      |
      v
Prediction Store
      |
      v
Prediction History / UI
```

---

## 2. Completed Sprint Objectives

### Real-Time Streaming

- Kafka topic `supportsense.tickets` implemented and verified.
- Kafka ticket producer implemented and verified.
- Spark Structured Streaming implemented and verified.
- Kafka -> Spark -> Runner `/predict` flow verified.
- Kafka event correlation verified through `event_id` -> prediction `source_event_id`.
- Prediction persistence verified through the Runner `/predictions` endpoint.

### ML Prediction

- Existing serving model remained operational.
- The current serving path continues to use the SupportSense baseline model.
- Streaming tickets are classified through the same Runner prediction service used by the manual workflow.

### UI

- Existing SupportSense manual prediction workflow preserved.
- Prediction History UI verified.
- Kafka-generated predictions verified in the same Prediction History.
- Manual and streaming prediction paths therefore converge on the same prediction store and history view.

### Observability

- Read-only `./scripts/supportsense.sh stream` observability command implemented.
- Kafka health and topic/partition information exposed.
- Spark Streaming status and health exposed.
- Recent streaming predictions displayed.
- Kafka event -> prediction correlation displayed.

### Developer Tooling

- Git helper argument forwarding corrected and verified.
- Git safety checks used for repository operations.
- Airflow developer credential discovery implemented.
- Airflow login URL and username are displayed through development tooling.
- Generated Airflow password can be retrieved dynamically with:

```bash
./scripts/supportsense.sh airflow credentials
```

- Airflow credentials are not stored in the repository.

---

## 3. End-to-End Streaming Verification

A new Kafka event was published using:

`My card was charged twice`

The event was successfully processed through:

```text
Kafka
  ->
Spark Structured Streaming
  ->
Runner /predict
  ->
Prediction Store
```

The resulting prediction was:

```text
Intent:
transaction_charged_twice

Action:
Investigate duplicate charge

Risk:
MEDIUM
```

The Kafka event identifier was preserved as the prediction `source_event_id`, establishing end-to-end event correlation.

A later streaming verification also processed:

`My cash withdrawal shows twice`

and produced a corresponding prediction through the same streaming path.

---

## 4. CI Verification

The Sprint 7 implementation was pushed to:

`feature/sprint-7-observability`

Latest verified CI run:

`32868376054`

Result:

`SUCCESS`

The CI pipeline completed:

- Python environment setup
- OIDC inspection
- AWS credential configuration
- AWS identity verification
- DVC data retrieval
- DVC pipeline reproduction
- MLflow tracking setup
- MLflow environment verification
- Full test suite

---

## 5. Final Sprint 7 Environment

At checkpoint closure, the local development environment was verified with:

```text
Python 3.12.3
Docker
MLflow
SupportSense Runner
Kafka
Spark Structured Streaming
Prometheus
Grafana
Airflow
DVC
```

The SupportSense Runner health endpoint returned successfully.

The Airflow development UI is available at:

`http://127.0.0.1:18080`

Airflow development credentials are retrieved dynamically using:

```bash
./scripts/supportsense.sh airflow credentials
```

---

## 6. Known Non-Blocking Items Deferred to Sprint 8

### Kafka Event Viewer

A richer developer-facing Kafka event viewer will be considered in Sprint 8.

### Streaming Performance Investigation

The observed Spark processing-time behavior will be measured systematically in Sprint 8 rather than relying on a single historical warning.

### UI Demo Upgrade

The existing functional UI will receive a substantial demo/presentation-quality improvement in Sprint 8 while preserving its existing functionality.

### Prometheus / Grafana Assessment

The current Prometheus and Grafana implementation will first be assessed and documented in Sprint 8.

The assessment will determine:

- currently exposed metrics;
- current Prometheus targets;
- existing Grafana dashboards;
- application-level monitoring coverage;
- Kafka/Spark observability coverage;
- ML/prediction monitoring gaps;
- future dashboard and alerting requirements.

No assumption is made that these components need to be rebuilt.

---

## 7. Sprint 7 Closure

Sprint 7 is considered **COMPLETED**.

The core objective — establishing and verifying the SupportSense real-time streaming prediction path — has been achieved.

The remaining items are intentionally carried forward as Sprint 8 work.

```text
Sprint 7
   |
   +-- Kafka
   +-- Spark Streaming
   +-- Runner Integration
   +-- Prediction Persistence
   +-- Event Correlation
   +-- Prediction History
   +-- Streaming Observability
   +-- Git Safety
   +-- CI Verification
   +-- Airflow Developer Tooling
   |
   v
COMPLETED / CHECKPOINT CLOSED

                 |
                 v

Sprint 8
   |
   +-- Streaming Operations
   +-- Performance Measurement
   +-- Kafka Event Viewer
   +-- UI Demo Upgrade
   +-- Prometheus Assessment
   +-- Grafana Assessment
```

---

## 8. Checkpoint Principle

Sprint 8 work should begin from this verified state.

No Sprint 7 functionality should be removed merely to introduce Sprint 8 improvements.

The Sprint 7 streaming path and manual prediction path remain the baseline for subsequent development.
