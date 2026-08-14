from pathlib import Path

from src.models.baseline import (
    create_baseline_model,
    evaluate_model,
    run_baseline,
    train_baseline,
)


TRAIN_PATH = Path("data/processed/train.csv")
VALIDATION_PATH = Path("data/processed/validation.csv")


def test_create_baseline_model():
    model = create_baseline_model()

    assert model.max_iter == 1000
    assert model.random_state == 42


def test_baseline_training_produces_fitted_model():
    result = run_baseline(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    model = result["model"]

    assert hasattr(model, "classes_")
    assert len(model.classes_) == 77


def test_baseline_feature_shapes_match():
    result = run_baseline(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    train_shape = result["train_shape"]
    validation_shape = result["validation_shape"]

    assert train_shape[0] == 8002
    assert validation_shape[0] == 2001
    assert train_shape[1] == validation_shape[1]


def test_baseline_metrics_are_valid():
    result = run_baseline(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    metrics = result["metrics"]

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 0.0 <= metrics["weighted_f1"] <= 1.0


def test_baseline_performance_meets_initial_target():
    result = run_baseline(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    metrics = result["metrics"]

    assert metrics["accuracy"] >= 0.80
    assert metrics["macro_f1"] >= 0.80
