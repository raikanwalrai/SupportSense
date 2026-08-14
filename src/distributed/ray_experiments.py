from pathlib import Path
from typing import Any

import ray


def build_experiment_configs() -> list[dict[str, Any]]:
    """Build candidate Logistic Regression configurations."""

    return [
        {
            "C": 0.5,
            "class_weight": None,
        },
        {
            "C": 1.0,
            "class_weight": None,
        },
        {
            "C": 1.0,
            "class_weight": "balanced",
        },
        {
            "C": 2.0,
            "class_weight": None,
        },
    ]


def select_best_experiment(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select the best experiment using Macro F1."""

    if not results:
        raise ValueError("Cannot select a best experiment from empty results.")

    return max(
        results,
        key=lambda result: result["macro_f1"],
    )

def run_ray_experiments(
    config_path: str | Path,
) -> list[dict[str, Any]]:
    """Run candidate Logistic Regression experiments with Ray."""

    from sklearn.linear_model import LogisticRegression

    from src.config.experiment_config import (
        load_experiment_config,
        validate_experiment_config,
    )
    from src.features.tfidf import (
        create_tfidf_vectorizer,
        fit_tfidf,
        load_split,
        transform_tfidf,
    )
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
    )

    config = load_experiment_config(config_path)
    validate_experiment_config(config)

    train_df = load_split(config["data"]["train_path"])
    validation_df = load_split(
        config["data"]["validation_path"]
    )

    vectorizer = create_tfidf_vectorizer(config)

    X_train = fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    X_validation = transform_tfidf(
        vectorizer,
        validation_df["text"],
    )

    y_train = train_df["category"]
    y_validation = validation_df["category"]

    experiment_configs = build_experiment_configs()

    if not ray.is_initialized():
        ray.init(
            num_cpus=2,
            ignore_reinit_error=True,
        )

    @ray.remote
    def run_single_experiment(
        experiment_config: dict[str, Any],
    ) -> dict[str, Any]:

        model = LogisticRegression(
            C=experiment_config["C"],
            class_weight=experiment_config["class_weight"],
            max_iter=1000,
            random_state=42,
        )

        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(X_validation)

        return {
            "C": experiment_config["C"],
            "class_weight": experiment_config["class_weight"],
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
        }

    futures = [
        run_single_experiment.remote(experiment_config)
        for experiment_config in experiment_configs
    ]

    results = ray.get(futures)

    return results

