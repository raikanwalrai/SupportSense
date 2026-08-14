from pathlib import Path
from typing import Any
from src.config.experiment_config import (    load_experiment_config,    validate_experiment_config,)

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)

from src.features.tfidf import (
    create_tfidf_vectorizer,
    fit_tfidf,
    load_split,
    transform_tfidf,
)


TRAIN_PATH = Path("data/processed/train.csv")
VALIDATION_PATH = Path("data/processed/validation.csv")

def create_baseline_model(
    config: dict[str, Any] | None = None,
) -> LogisticRegression:
    """Create the SupportSense Logistic Regression baseline."""

    if config is None:
        config = load_experiment_config(
            "configs/experiments.yaml"
        )

    validate_experiment_config(config)

    model_config = config["model"]

    if model_config["type"] != "logistic_regression":
        raise ValueError(
            "Baseline model configuration must specify "
            "'logistic_regression'."
        )

    return LogisticRegression(
        max_iter=model_config["max_iter"],
        random_state=model_config["random_state"],
    )

def train_baseline(
    X_train,
    y_train,
    config: dict[str, Any] | None = None,
) -> LogisticRegression:
    """Train the Logistic Regression baseline."""

    model = create_baseline_model(config)
    model.fit(X_train, y_train)

    return model

def evaluate_model(
    model: LogisticRegression,
    X_validation,
    y_validation,
) -> dict:
    """Evaluate the classifier on validation data."""

    predictions = model.predict(X_validation)

    return {
        "accuracy": accuracy_score(
            y_validation,
            predictions,
        ),
        "macro_f1": f1_score(
            y_validation,
            predictions,
            average="macro",
        ),
        "weighted_f1": f1_score(
            y_validation,
            predictions,
            average="weighted",
        ),
        "classification_report": classification_report(
            y_validation,
            predictions,
            zero_division=0,
        ),
    }


def run_baseline(
    train_path: str | Path = TRAIN_PATH,
    validation_path: str | Path = VALIDATION_PATH,
    config: dict[str, Any] | None = None,
) -> dict:
    """Run the complete TF-IDF + Logistic Regression baseline."""

    train_df = load_split(train_path)
    validation_df = load_split(validation_path)

    vectorizer = create_tfidf_vectorizer(config)

    X_train = fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    X_validation = transform_tfidf(
        vectorizer,
        validation_df["text"],
    )

    model = train_baseline(
        X_train,
        train_df["category"],
    )

    metrics = evaluate_model(
        model,
        X_validation,
        validation_df["category"],
    )

    return {
        "model": model,
        "vectorizer": vectorizer,
        "metrics": metrics,
        "train_shape": X_train.shape,
        "validation_shape": X_validation.shape,
    }


if __name__ == "__main__":
    result = run_baseline()

    metrics = result["metrics"]

    print()
    print("=" * 70)
    print("SupportSense Logistic Regression Baseline")
    print("=" * 70)

    print()
    print("## Feature Matrix")

    print(f"Training   : {result['train_shape']}")
    print(f"Validation : {result['validation_shape']}")

    print()
    print("## Evaluation")

    print(f"Accuracy    : {metrics['accuracy']:.4f}")
    print(f"Macro F1    : {metrics['macro_f1']:.4f}")
    print(f"Weighted F1 : {metrics['weighted_f1']:.4f}")

    print()
    print("## Classification Report")

    print(metrics["classification_report"])
