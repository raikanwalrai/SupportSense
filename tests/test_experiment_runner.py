import os
from pathlib import Path

import pytest

from src.experiments.runner import run_experiment


CONFIG_PATH = Path("configs/experiments.yaml")

os.environ.setdefault(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)


@pytest.fixture(scope="module")
def experiment_result():
    """Run the real experiment once for this test module."""

    return run_experiment(CONFIG_PATH)


def test_experiment_runner_returns_result(experiment_result):
    result = experiment_result

    assert isinstance(result, dict)


def test_experiment_runner_identifies_experiment(experiment_result):
    result = experiment_result

    assert result["experiment_name"] == (
        "baseline_tfidf_logistic_regression"
    )


def test_experiment_runner_reports_feature_shapes(experiment_result):
    result = experiment_result

    assert result["train_shape"] == (8002, 8903)
    assert result["validation_shape"] == (2001, 8903)


def test_experiment_runner_reports_class_count(experiment_result):
    result = experiment_result

    assert result["num_classes"] == 77


def test_experiment_runner_reports_metrics(experiment_result):
    result = experiment_result

    metrics = result["metrics"]

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 0.0 <= metrics["weighted_f1"] <= 1.0


def test_experiment_runner_matches_baseline_target(experiment_result):
    result = experiment_result

    assert result["metrics"]["accuracy"] >= 0.80
    assert result["metrics"]["macro_f1"] >= 0.80
