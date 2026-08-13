# SupportSense Data Contract

## 1. Purpose

The SupportSense data contract defines the canonical representation of a
customer support ticket used by the data, machine learning, deep learning,
LLM, and customer-service agent layers.

The contract is designed to be independent of a specific dataset so that
different customer-support domains can be integrated later.

## 2. Canonical Ticket Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| ticket_id | string | Yes | Unique identifier for the ticket |
| text | string | Yes | Customer support request text |
| intent | string | Yes | Customer intent / classification target |
| source | string | Yes | Dataset or ingestion source |
| created_at | datetime | No | Ticket creation timestamp |
| customer_id | string | No | Customer identifier |
| priority | string | No | Ticket priority / urgency |
| status | string | No | Ticket lifecycle status |

## 3. Sprint 1 Dataset Mapping

Sprint 1 uses the BANKING77 dataset.

The dataset-native information used by SupportSense is:

- customer query text
- intent label

The following fields are not assumed to exist in BANKING77:

- customer_id
- priority
- status
- created_at

If these fields are introduced later as synthetic or production metadata,
their origin must be explicitly documented.

## 4. Machine Learning Task

Sprint 1 treats customer support intent prediction as a multi-class
classification problem.

Input:

    X = customer ticket text

Target:

    y = intent

## 5. Data Quality Rules

A valid ticket must:

1. Have non-null text.
2. Have non-null intent.
3. Have non-empty text after trimming whitespace.
4. Have a valid intent belonging to the supported intent vocabulary.
5. Have a unique ticket identifier within the canonical dataset.
6. Not contain exact duplicate records unless explicitly retained and documented.

## 6. Data Lineage

The dataset source, version, preprocessing operations, and generated
datasets must be traceable.

Raw datasets will be versioned using DVC.

Source code and configuration will be versioned using Git.

Experiments and model-training results will eventually be tracked using MLflow.

## 7. Future Extensions

The canonical schema may later be extended with:

- language
- channel
- product
- customer segment
- priority
- sentiment
- resolution status
- agent assignment
- model prediction
- prediction confidence
- escalation decision
- resolution time

These fields will be introduced only when their data source and semantics
are clearly defined.
