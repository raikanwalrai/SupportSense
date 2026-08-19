"""
SupportSense prediction event store.

Sprint 7 provides a lightweight SQLite-backed event store for
ML inference and decision events.

The store is intentionally isolated from MLflow's database.
It can later be replaced by a production database without
changing the runner API contract.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[2]
EVENT_DB = PROJECT_DIR / "supportsense_events.db"


def _connect() -> sqlite3.Connection:
    """Create a connection to the SupportSense event database."""
    connection = sqlite3.connect(EVENT_DB)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_event_store() -> None:
    """Create the prediction-events table if it does not exist."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,

                ticket TEXT NOT NULL,
                predicted_intent TEXT NOT NULL,

                model_name TEXT NOT NULL,
                experiment_name TEXT NOT NULL,
                run_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                model_status TEXT NOT NULL,

                action_id TEXT NOT NULL,
                action_name TEXT NOT NULL,
                risk TEXT NOT NULL,
                requires_approval INTEGER NOT NULL,

                actual_intent TEXT,
                prediction_correct INTEGER,

                outcome TEXT
            )
            """
        )

        connection.commit()


def record_prediction(
    *,
    ticket: str,
    predicted_intent: str,
    model_name: str,
    experiment_name: str,
    run_id: str,
    model_id: str,
    model_status: str,
    action_id: str,
    action_name: str,
    risk: str,
    requires_approval: bool,
) -> str:
    """
    Persist one ML prediction and its associated decision.

    Actual/human outcome fields intentionally start as NULL.
    They will be populated later through the feedback workflow.
    """
    initialize_event_store()

    event_id = str(uuid.uuid4())

    timestamp = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO prediction_events (
                event_id,
                timestamp,
                ticket,
                predicted_intent,
                model_name,
                experiment_name,
                run_id,
                model_id,
                model_status,
                action_id,
                action_name,
                risk,
                requires_approval,
                actual_intent,
                prediction_correct,
                outcome
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                timestamp,
                ticket,
                predicted_intent,
                model_name,
                experiment_name,
                run_id,
                model_id,
                model_status,
                action_id,
                action_name,
                risk,
                int(requires_approval),
                None,
                None,
                None,
            ),
        )

        connection.commit()

    return event_id


def list_predictions(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent prediction events."""
    initialize_event_store()

    if limit < 1:
        raise ValueError("limit must be greater than zero")

    limit = min(limit, 500)

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                event_id,
                timestamp,
                ticket,
                predicted_intent,
                model_name,
                experiment_name,
                run_id,
                model_id,
                model_status,
                action_id,
                action_name,
                risk,
                requires_approval,
                actual_intent,
                prediction_correct,
                outcome
            FROM prediction_events
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def update_prediction_outcome(
    *,
    event_id: str,
    actual_intent: str,
    outcome: str | None = None,
) -> dict[str, Any] | None:
    """
    Record a human/actual outcome for a prediction.

    prediction_correct is derived automatically from the predicted
    and actual intent values.
    """
    initialize_event_store()

    with _connect() as connection:
        row = connection.execute(
            """
            SELECT predicted_intent
            FROM prediction_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return None

        prediction_correct = int(
            row["predicted_intent"] == actual_intent
        )

        connection.execute(
            """
            UPDATE prediction_events
            SET
                actual_intent = ?,
                prediction_correct = ?,
                outcome = ?
            WHERE event_id = ?
            """,
            (
                actual_intent,
                prediction_correct,
                outcome,
                event_id,
            ),
        )

        connection.commit()

    with _connect() as connection:
        updated = connection.execute(
            """
            SELECT *
            FROM prediction_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

    return dict(updated) if updated else None


def get_prediction(event_id: str) -> dict[str, Any] | None:
    """Return one prediction event by ID."""
    initialize_event_store()

    with _connect() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM prediction_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

    return dict(row) if row else None
