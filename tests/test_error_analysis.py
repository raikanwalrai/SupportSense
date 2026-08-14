from pathlib import Path

from src.models.error_analysis import analyze_errors


TRAIN_PATH = Path("data/processed/train.csv")
VALIDATION_PATH = Path("data/processed/validation.csv")


def test_error_analysis_returns_expected_structure():

    result = analyze_errors(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    assert "model" in result
    assert "vectorizer" in result
    assert "metrics" in result
    assert "classification_report" in result
    assert "confusion_pairs" in result
    assert "per_intent" in result
    assert "errors" in result


def test_error_analysis_has_expected_error_count():

    result = analyze_errors(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    assert result["total_validation_records"] == 2001
    assert result["total_errors"] == 311


def test_error_analysis_contains_all_intents():

    result = analyze_errors(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    assert len(result["per_intent"]) == 77


def test_error_analysis_confusion_pairs_are_sorted():

    result = analyze_errors(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    pairs = result["confusion_pairs"]

    counts = [item["count"] for item in pairs]

    assert counts == sorted(
        counts,
        reverse=True,
    )


def test_error_analysis_meets_baseline_target():

    result = analyze_errors(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
    )

    assert result["metrics"]["macro_f1"] >= 0.80
