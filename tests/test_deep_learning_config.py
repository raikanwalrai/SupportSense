from pathlib import Path

import pytest

from src.config.deep_learning_config import (
    get_training_profile,
    get_tuning_profile,
    load_deep_learning_config,
    validate_deep_learning_config,
)


CONFIG_PATH = Path("configs/deep_learning.yaml")


def test_deep_learning_config_loads():
    config = load_deep_learning_config(CONFIG_PATH)

    assert "deep_learning" in config
    assert "defaults" in config["deep_learning"]
    assert "profiles" in config["deep_learning"]
    assert "tuning" in config["deep_learning"]


def test_training_profiles_are_available():
    config = load_deep_learning_config(CONFIG_PATH)

    profiles = config["deep_learning"]["profiles"]

    assert set(profiles) == {"smoke", "full"}


def test_smoke_training_profile_is_lightweight():
    config = load_deep_learning_config(CONFIG_PATH)

    profile = get_training_profile(config, "smoke")

    assert profile["epochs"] == 1
    assert profile["batch_size"] == 64
    assert profile["learning_rate"] == 0.001
    assert profile["embedding_dim"] == 16
    assert profile["patience"] == 1
    assert profile["dropout"] == 0.0


def test_full_training_profile_is_available():
    config = load_deep_learning_config(CONFIG_PATH)

    profile = get_training_profile(config, "full")

    assert profile["epochs"] == 20
    assert profile["batch_size"] == 32
    assert profile["embedding_dim"] == 128
    assert profile["patience"] == 3
    assert profile["dropout"] == 0.2


def test_training_profile_contains_defaults():
    config = load_deep_learning_config(CONFIG_PATH)

    profile = get_training_profile(config, "smoke")

    assert profile["seed"] == 42
    assert profile["device"] == "cpu"
    assert profile["max_vocab_size"] == 2500
    assert profile["max_length"] == 48
    assert profile["checkpoint_path"] == (
        "models/deep_learning/best_model.pt"
    )


def test_unknown_training_profile_raises_error():
    config = load_deep_learning_config(CONFIG_PATH)

    with pytest.raises(
        ValueError,
        match="Unknown deep-learning profile",
    ):
        get_training_profile(config, "unknown")


def test_tuning_profiles_are_available():
    config = load_deep_learning_config(CONFIG_PATH)

    smoke = get_tuning_profile(config, "smoke")
    full = get_tuning_profile(config, "full")

    assert smoke["max_concurrent_trials"] == 1
    assert smoke["max_t"] == 1

    assert full["max_concurrent_trials"] == 1
    assert full["max_t"] == 20


def test_tuning_profiles_contain_trials():
    config = load_deep_learning_config(CONFIG_PATH)

    smoke = get_tuning_profile(config, "smoke")
    full = get_tuning_profile(config, "full")

    assert len(smoke["trials"]) == 2
    assert len(full["trials"]) == 3

    for trial in smoke["trials"] + full["trials"]:
        assert "learning_rate" in trial
        assert "embedding_dim" in trial
        assert "dropout" in trial


def test_unknown_tuning_profile_raises_error():
    config = load_deep_learning_config(CONFIG_PATH)

    with pytest.raises(
        ValueError,
        match="Unknown Ray Tune profile",
    ):
        get_tuning_profile(config, "unknown")


def test_invalid_deep_learning_config_is_rejected():
    config = load_deep_learning_config(CONFIG_PATH)

    del config["deep_learning"]["profiles"]["smoke"]["epochs"]

    with pytest.raises(
        ValueError,
        match="Profile 'smoke' is missing keys",
    ):
        validate_deep_learning_config(config)
