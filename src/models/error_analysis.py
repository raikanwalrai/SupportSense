from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)

from src.features.tfidf import (
    create_tfidf_vectorizer,
    fit_tfidf,
    load_split,
    transform_tfidf,
)
from src.models.baseline import (
    evaluate_model,
    train_baseline,
)


def analyze_errors(
    train_path: str | Path,
    validation_path: str | Path,
) -> dict:
    """Train the baseline model and analyze validation errors."""

    train_df = load_split(train_path)
    validation_df = load_split(validation_path)

    # ---------------------------------------------------------
    # TF-IDF
    # ---------------------------------------------------------

    vectorizer = create_tfidf_vectorizer()

    X_train = fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    X_validation = transform_tfidf(
        vectorizer,
        validation_df["text"],
    )

    # ---------------------------------------------------------
    # Train baseline
    # ---------------------------------------------------------

    model = train_baseline(
        X_train,
        train_df["category"],
    )

    # ---------------------------------------------------------
    # Predictions and evaluation
    # ---------------------------------------------------------

    y_true = validation_df["category"]
    y_pred = model.predict(X_validation)

    metrics = evaluate_model(
        model,
        X_validation,
        y_true,
    )

    # ---------------------------------------------------------
    # Classification report
    # ---------------------------------------------------------

    labels = sorted(y_true.unique())

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    # ---------------------------------------------------------
    # Confusion matrix
    # ---------------------------------------------------------

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=labels,
    )

    confusion_pairs = []

    for i, true_intent in enumerate(labels):

        for j, predicted_intent in enumerate(labels):

            # Ignore correct predictions.
            if i == j:
                continue

            count = int(matrix[i, j])

            if count > 0:
                confusion_pairs.append(
                    {
                        "true_intent": true_intent,
                        "predicted_intent": predicted_intent,
                        "count": count,
                    }
                )

    confusion_pairs.sort(
        key=lambda item: item["count"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # Per-intent performance
    # ---------------------------------------------------------

    per_intent = []

    for intent in labels:

        intent_metrics = report[intent]

        per_intent.append(
            {
                "intent": intent,
                "precision": intent_metrics["precision"],
                "recall": intent_metrics["recall"],
                "f1": intent_metrics["f1-score"],
                "support": int(intent_metrics["support"]),
            }
        )

    per_intent.sort(
        key=lambda item: item["f1"]
    )

    # ---------------------------------------------------------
    # Individual errors
    # ---------------------------------------------------------

    error_mask = (
        y_true.to_numpy()
        != y_pred
    )

    errors = validation_df.loc[
        error_mask
    ].copy()

    errors["predicted_category"] = y_pred[
        error_mask
    ]

    return {
        "model": model,
        "vectorizer": vectorizer,
        "metrics": metrics,
        "classification_report": report,
        "confusion_pairs": confusion_pairs,
        "per_intent": per_intent,
        "errors": errors,
        "total_errors": int(error_mask.sum()),
        "total_validation_records": len(
            validation_df
        ),
    }


def print_error_summary(result: dict) -> None:
    """Print the main baseline error-analysis results."""

    print()
    print("=" * 100)
    print("SupportSense Baseline Error Analysis")
    print("=" * 100)

    metrics = result["metrics"]

    print()
    print("## Baseline Performance")

    print(
        f"Accuracy    : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Macro F1    : "
        f"{metrics['macro_f1']:.4f}"
    )

    print(
        f"Weighted F1 : "
        f"{metrics['weighted_f1']:.4f}"
    )

    print()
    print("## Errors")

    print(
        f"Validation records : "
        f"{result['total_validation_records']}"
    )

    print(
        f"Incorrect          : "
        f"{result['total_errors']}"
    )

    print()
    print("## Lowest-F1 Intents")
    print()

    print(
        f"{'Intent':45s}"
        f"{'Precision':>10s}"
        f"{'Recall':>10s}"
        f"{'F1':>10s}"
        f"{'Support':>10s}"
    )

    print("-" * 90)

    for item in result["per_intent"][:10]:

        print(
            f"{item['intent']:45s}"
            f"{item['precision']:10.3f}"
            f"{item['recall']:10.3f}"
            f"{item['f1']:10.3f}"
            f"{item['support']:10d}"
        )

    print()
    print("## Most Common Confusion Pairs")
    print()

    print(
        f"{'True Intent':45s}"
        f"{'Predicted Intent':45s}"
        f"{'Errors':>8s}"
    )

    print("-" * 100)

    for item in result["confusion_pairs"][:20]:

        print(
            f"{item['true_intent']:45s}"
            f"{item['predicted_intent']:45s}"
            f"{item['count']:8d}"
        )


def main() -> None:
    """Run baseline error analysis."""

    train_path = Path(
        "data/processed/train.csv"
    )

    validation_path = Path(
        "data/processed/validation.csv"
    )

    result = analyze_errors(
        train_path=train_path,
        validation_path=validation_path,
    )

    print_error_summary(result)


if __name__ == "__main__":
    main()
