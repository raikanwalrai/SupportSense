# SupportSense — Sprint 8 Baseline & Architecture

**Sprint:** 8
**Branch:** `feature/sprint-7-observability`
**Status:** BASELINE ASSESSMENT COMPLETE — IMPLEMENTATION STARTING

---

## 1. Sprint 8 Objective

Sprint 8 evolves SupportSense from a functional prediction interface into a Support Operations Center while preserving the existing end-to-end ML and real-time streaming pipeline.

The primary objectives are:

- improve the SupportSense UI for demonstration and operational use;
- clearly separate live streaming predictions from manual predictions;
- make confidence, risk, action, and human-intervention decisions explicit;
- preserve the existing prediction, feedback, history, and action workflows;
- assess and selectively extend the existing Prometheus/Grafana observability;
- avoid duplicating engineering observability inside the business-facing UI;
- measure the existing real-time streaming path before performance changes.

---

## 2. Verified Current Architecture

The current real-time path is:

```text
Ticket Producer
      |
      v
Kafka
supportsense.tickets
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
Prediction History / UI
```

The current environment starts Kafka and Spark Streaming as part of the development environment. The ticket producer remains a separate event-generation mechanism.

---

## 3. Support Operations Center

The primary SupportSense UI will evolve into a Support Operations Center.

Its purpose is to answer:

> What tickets are arriving, what did the AI decide, what action should happen, and does a human need to intervene?

The UI should not attempt to duplicate the engineering observability provided by Grafana.

---

## 4. Proposed UI Modes

### 4.1 Live Operations

Purpose:

Show event-driven tickets entering through Kafka and being processed through Spark, the ML model, and the decision layer.

The interface should clearly identify:

- live event source;
- ticket;
- prediction;
- confidence;
- risk;
- recommended action;
- approval requirement;
- human intervention requirement;
- event identifier;
- source event identifier;
- processing latency.

---

### 4.2 Manual Prediction

Purpose:

Provide the existing human-entered ticket prediction workflow.

Manual predictions must remain visually distinct from streaming predictions.

The existing `/predict` workflow should be preserved.

---

### 4.3 Prediction History

Purpose:

Provide a unified historical operational record.

History should distinguish between:

- live/stream-generated predictions;
- manually submitted predictions.

Relevant information includes:

- timestamp;
- source;
- ticket;
- predicted intent;
- confidence;
- risk;
- action;
- approval requirement;
- actual intent;
- prediction correctness.

---

### 4.4 Human Review / Exceptions

Where supported by the existing decision logic, the UI should provide a clear operational view of cases requiring human attention.

The UI should distinguish confidence from risk.

Confidence describes the model’s prediction certainty.

Risk describes the operational consequence associated with the decision.

These values must not be treated as interchangeable.

---

### 4.5 System Status

The Support Operations Center may show concise operational status such as:

- Runner operational;
- Kafka operational;
- Spark processing;
- model ready.

Detailed engineering metrics remain the responsibility of Grafana.

---

## 5. Responsibility Boundary

SupportSense UI:

```text
Business / Support Operations
        |
        +-- Live tickets
        +-- AI decisions
        +-- Confidence
        +-- Risk
        +-- Actions
        +-- Human intervention
        +-- Exceptions
        +-- Prediction history
```

Grafana:

```text
Engineering / MLOps Observability
        |
        +-- Request rate
        +-- Prediction rate
        +-- Latency
        +-- p95 latency
        +-- Errors
        +-- Runtime metrics
        +-- Historical operational trends
```

The Support Operations Center should not recreate Grafana dashboards or duplicate Prometheus visualizations unnecessarily.

If a Grafana visualization can be safely and usefully embedded without creating authentication, maintenance, or architectural problems, selective embedding may be considered later.

Otherwise, the UI should provide a clear link to Grafana.

---

## 6. Current Observability Baseline

Prometheus is healthy and currently scrapes the SupportSense Runner.

Current target:

```text
supportsense-runner
host.docker.internal:8000/metrics
15 second scrape interval
```

Existing SupportSense metric families include:

```text
supportsense_http_requests_total
supportsense_http_request_duration_seconds_*
supportsense_predictions_total
supportsense_prediction_duration_seconds_*
```

Grafana is healthy and already contains a SupportSense Runner Overview dashboard backed by Prometheus.

Existing dashboard coverage includes:

- Runner status;
- HTTP request rate;
- average HTTP latency;
- requests by endpoint;
- HTTP p95 latency;
- prediction rate;
- total predictions;
- prediction latency.

Sprint 8 should extend this only where additional observability provides genuine value.

---

## 7. Streaming Baseline

Current Kafka state:

```text
Topic: supportsense.tickets
Partitions: 3
Replication factor: 1
```

Spark Structured Streaming is currently operational.

The verified correlation is:

```text
Kafka event_id
      =
prediction source_event_id
```

Spark establishes this correlation before calling the Runner prediction endpoint.

The existing streaming observability command confirms:

```text
Kafka
  |
  v
Spark Structured Streaming
  |
  v
Runner /predict
  |
  v
Prediction Event Store
```

---

## 8. Performance Baseline

The current Spark runtime has produced a warning indicating that one streaming batch exceeded its configured five-second trigger interval.

This is not currently classified as a system failure.

Sprint 8 should measure streaming performance before making optimization changes.

Relevant measurements include:

- Kafka-to-Spark processing;
- Spark-to-Runner processing;
- prediction latency;
- end-to-end processing latency;
- streaming throughput.

---

## 9. Sprint 8 Implementation Principles

1. Preserve the working Sprint 7 streaming path.
2. Preserve the existing manual prediction workflow.
3. Do not mix live and manual prediction experiences ambiguously.
4. Treat confidence and risk as separate concepts.
5. Make human intervention decisions visible.
6. Keep business-facing operations in SupportSense UI.
7. Keep detailed engineering observability in Grafana.
8. Prefer reuse of existing metrics and APIs.
9. Measure before optimizing.
10. Do not introduce unnecessary architectural duplication.

---

## 10. Target UX

The intended primary navigation is:

```text
SupportSense
    |
    +-- Live Operations
    |
    +-- Manual Prediction
    |
    +-- Prediction History
    |
    +-- Human Review / Exceptions
    |
    +-- System Status
```

The overall experience should communicate:

```text
Ticket
  |
  v
Prediction
  |
  v
Confidence + Risk
  |
  v
Decision / Action
  |
  v
Human Intervention?
  |
  v
Operational Outcome
```

---

## 11. Sprint 8 Success Criteria

Sprint 8 will be considered successful when:

- live and manual predictions are clearly separated;
- the Support Operations Center provides a coherent operational workflow;
- the existing ML prediction path remains functional;
- the existing streaming path remains functional;
- Prediction History distinguishes event sources;
- confidence, risk, action, and human intervention are clearly presented;
- Prometheus/Grafana responsibilities remain separated from the business UI;
- useful observability is reused rather than unnecessarily duplicated;
- streaming performance has a measured baseline;
- the resulting UI is suitable as the primary SupportSense demonstration interface.
