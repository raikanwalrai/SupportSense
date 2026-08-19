import pytest
from src.features.tfidf import load_split
from src.config.experiment_config import load_experiment_config


from src.decision.actions import (
    ACTION_REGISTRY,
    ActionDefinition,
    get_action,
)


def test_registry_contains_initial_actions():
    assert "passcode_forgotten" in ACTION_REGISTRY
    assert "terminate_account" in ACTION_REGISTRY


def test_passcode_forgotten_action():
    action = get_action("passcode_forgotten")

    assert isinstance(action, ActionDefinition)
    assert action.intent == "passcode_forgotten"
    assert action.action_id == "RESET_PASSCODE"
    assert action.action_name == "Reset passcode"
    assert action.risk == "MEDIUM"
    assert action.requires_approval is False


def test_terminate_account_requires_approval():
    action = get_action("terminate_account")

    assert action.intent == "terminate_account"
    assert action.action_id == "TERMINATE_ACCOUNT"
    assert action.risk == "HIGH"
    assert action.requires_approval is True


def test_unknown_intent_is_rejected():
    with pytest.raises(
        ValueError,
        match="No action is registered",
    ):
        get_action("unknown_support_intent")


def test_action_definitions_are_immutable():
    action = get_action("passcode_forgotten")

    with pytest.raises(AttributeError):
        action.risk = "HIGH"


def test_action_registry_covers_all_dataset_intents():
    config = load_experiment_config("configs/experiments.yaml")

    df = load_split(config["data"]["train_path"])

    dataset_intents = set(
        df["category"].dropna().unique()
    )

    registered_intents = set(ACTION_REGISTRY)

    missing = dataset_intents - registered_intents
    extra = registered_intents - dataset_intents

    assert not missing, (
        "Missing action mappings: "
        f"{sorted(missing)}"
    )

    assert not extra, (
        "Action mappings not present in dataset: "
        f"{sorted(extra)}"
    )
