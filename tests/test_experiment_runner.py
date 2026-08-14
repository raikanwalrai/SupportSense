from pathlib import Path

from src.experiments.runner import run_experiment


CONFIG_PATH = Path("configs/experiments.yaml")


def test_experiment_runner_returns_result():
    result = run_experiment(CONFIG_PATH)

    assert isinstance(result, dict)


def test_experiment_runner_identifies_experiment():
    result = run_experiment(CONFIG_PATH)

    assert result["experiment_name"] == (
        "baseline_tfidf_logistic_regression"
    )


def test_experiment_runner_reports_feature_shapes():
    result = run_experiment(CONFIG_PATH)

    assert result["train_shape"] == (8002, 8903)
    assert result["validation_shape"] == (2001, 8903)


def test_experiment_runner_reports_class_count():
    result = run_experiment(CONFIG_PATH)

    assert result["num_classes"] == 77


def test_experiment_runner_reports_metrics():
    result = run_experiment(CONFIG_PATH)

    metrics = result["metrics"]

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 0.0 <= metrics["weighted_f1"] <= 1.0


def test_experiment_runner_matches_baseline_target():
    result = run_experiment(CONFIG_PATH)

    assert result["metrics"]["accuracy"] >= 0.80
    assert result["metrics"]["macro_f1"] >= 0.80
