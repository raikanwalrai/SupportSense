from pathlib import Path

import pytest

from src.config.experiment_config import (
    load_experiment_config,
    validate_experiment_config,
)


CONFIG_PATH = Path("configs/experiments.yaml")


def test_load_experiment_config():
    config = load_experiment_config(CONFIG_PATH)

    assert isinstance(config, dict)
    assert config["experiment"]["name"] == (
        "baseline_tfidf_logistic_regression"
    )
    assert config["experiment"]["random_state"] == 42
    assert config["experiment"]["primary_metric"] == "macro_f1"


def test_required_sections_are_present():
    config = load_experiment_config(CONFIG_PATH)

    validate_experiment_config(config)

    assert "experiment" in config
    assert "data" in config
    assert "features" in config
    assert "model" in config


def test_missing_configuration_file_raises_error():
    with pytest.raises(FileNotFoundError):
        load_experiment_config("configs/does_not_exist.yaml")


def test_missing_configuration_section_raises_error():
    config = {
        "experiment": {
            "name": "test",
            "random_state": 42,
            "primary_metric": "macro_f1",
        },
        "data": {},
        "features": {},
    }

    with pytest.raises(ValueError, match="Missing configuration sections"):
        validate_experiment_config(config)


def test_missing_experiment_key_raises_error():
    config = {
        "experiment": {
            "name": "test",
            "random_state": 42,
        },
        "data": {},
        "features": {},
        "model": {},
    }

    with pytest.raises(
        ValueError,
        match="Missing experiment configuration keys",
    ):
        validate_experiment_config(config)
