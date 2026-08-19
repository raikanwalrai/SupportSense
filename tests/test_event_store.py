from pathlib import Path

import src.monitoring.event_store as event_store


def test_initialize_event_store(tmp_path, monkeypatch):
    database = tmp_path / "events.db"

    monkeypatch.setattr(
        event_store,
        "EVENT_DB",
        Path(database),
    )

    event_store.initialize_event_store()

    assert database.exists()


def test_record_and_retrieve_prediction(tmp_path, monkeypatch):
    database = tmp_path / "events.db"

    monkeypatch.setattr(
        event_store,
        "EVENT_DB",
        Path(database),
    )

    event_id = event_store.record_prediction(
        ticket="I forgot my password",
        predicted_intent="passcode_forgotten",
        model_name="model",
        experiment_name="SupportSense Baseline",
        run_id="run-123",
        model_id="model-123",
        model_status="READY",
        action_id="RESET_PASSCODE",
        action_name="Reset passcode",
        risk="MEDIUM",
        requires_approval=False,
    )

    event = event_store.get_prediction(event_id)

    assert event is not None
    assert event["event_id"] == event_id
    assert event["ticket"] == "I forgot my password"
    assert event["predicted_intent"] == "passcode_forgotten"
    assert event["action_id"] == "RESET_PASSCODE"
    assert event["actual_intent"] is None
    assert event["prediction_correct"] is None


def test_update_prediction_outcome(tmp_path, monkeypatch):
    database = tmp_path / "events.db"

    monkeypatch.setattr(
        event_store,
        "EVENT_DB",
        Path(database),
    )

    event_id = event_store.record_prediction(
        ticket="I forgot my password",
        predicted_intent="passcode_forgotten",
        model_name="model",
        experiment_name="SupportSense Baseline",
        run_id="run-123",
        model_id="model-123",
        model_status="READY",
        action_id="RESET_PASSCODE",
        action_name="Reset passcode",
        risk="MEDIUM",
        requires_approval=False,
    )

    updated = event_store.update_prediction_outcome(
        event_id=event_id,
        actual_intent="passcode_forgotten",
        outcome="confirmed",
    )

    assert updated is not None
    assert updated["actual_intent"] == "passcode_forgotten"
    assert updated["prediction_correct"] == 1
    assert updated["outcome"] == "confirmed"


def test_incorrect_prediction_is_recorded(tmp_path, monkeypatch):
    database = tmp_path / "events.db"

    monkeypatch.setattr(
        event_store,
        "EVENT_DB",
        Path(database),
    )

    event_id = event_store.record_prediction(
        ticket="My card does not work",
        predicted_intent="card_not_working",
        model_name="model",
        experiment_name="SupportSense Baseline",
        run_id="run-123",
        model_id="model-123",
        model_status="READY",
        action_id="TROUBLESHOOT_CARD",
        action_name="Troubleshoot card",
        risk="LOW",
        requires_approval=False,
    )

    updated = event_store.update_prediction_outcome(
        event_id=event_id,
        actual_intent="declined_card_payment",
        outcome="corrected_by_human",
    )

    assert updated is not None
    assert updated["actual_intent"] == "declined_card_payment"
    assert updated["prediction_correct"] == 0
