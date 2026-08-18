import os
from pathlib import Path
from typing import Any

import mlflow.sklearn
import mlflow
import ray


def build_experiment_configs(
    config: dict[str, Any],
    profile_name: str = "full",
) -> list[dict[str, Any]]:
    """Build Logistic Regression candidates from configuration."""

    from src.config.experiment_config import get_ray_profile

    profile = get_ray_profile(
        config,
        profile_name,
    )

    return list(profile["candidates"])


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
    profile_name: str = "full",
) -> list[dict[str, Any]]:
    """Run candidate Logistic Regression experiments with Ray."""
    mlflow.set_tracking_uri(
        os.environ.get(
            "MLFLOW_TRACKING_URI",
            "http://127.0.0.1:5000",
        )
    )
    mlflow.set_experiment("SupportSense Logistic Regression Tuning")

    from sklearn.linear_model import LogisticRegression

    from src.config.experiment_config import (
        get_ray_profile,
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

    ray_profile = get_ray_profile(
        config,
        profile_name,
    )

    experiment_configs = build_experiment_configs(
        config,
        profile_name,
    )

    max_iter = ray_profile["max_iter"]

    execution_config = config["ray"]["execution"]

    num_cpus = execution_config["num_cpus"]
    max_concurrent_experiments = execution_config[
        "max_concurrent_experiments"
    ]

    if not ray.is_initialized():
       ray.init(
            num_cpus=num_cpus,
            ignore_reinit_error=True,
        )



    @ray.remote
    def run_single_experiment(
        experiment_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Train and evaluate one Logistic Regression experiment."""

        # Each Ray worker is a separate process, so configure MLflow
        # explicitly inside the worker.
        mlflow.set_tracking_uri(
        os.environ.get(
            "MLFLOW_TRACKING_URI",
            "http://127.0.0.1:5000",
        )
    )
        mlflow.set_experiment(
            "SupportSense Logistic Regression Tuning"
        )

        with mlflow.start_run() as run:
            mlflow.log_params(
                {
                    "C": experiment_config["C"],
                    "class_weight": experiment_config["class_weight"],
                    "max_iter": max_iter,
                    "random_state": config["experiment"]["random_state"],
                }
            )

            model = LogisticRegression(
                C=experiment_config["C"],
                class_weight=experiment_config["class_weight"],
                max_iter=max_iter,
                random_state=config["experiment"]["random_state"],
            )

            model.fit(
                X_train,
                y_train,
            )

            predictions = model.predict(X_validation)

            accuracy = accuracy_score(
                y_validation,
                predictions,
            )

            macro_f1 = f1_score(
                y_validation,
                predictions,
                average="macro",
            )

            weighted_f1 = f1_score(
                y_validation,
                predictions,
                average="weighted",
            )

            mlflow.log_metrics(
                {
                    "accuracy": accuracy,
                    "macro_f1": macro_f1,
                    "weighted_f1": weighted_f1,
                }
            )
            mlflow.sklearn.log_model(
		    model,
		    name="model",
		)

            return {
                "C": experiment_config["C"],
                "class_weight": experiment_config["class_weight"],
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "weighted_f1": weighted_f1,
                "run_id": run.info.run_id,
            }

    results = []

    for start in range(
        0,
        len(experiment_configs),
        max_concurrent_experiments,
    ):
        batch = experiment_configs[
            start:start + max_concurrent_experiments
        ]

        futures = [
            run_single_experiment.remote(experiment_config)
            for experiment_config in batch
        ]

        results.extend(ray.get(futures))

    return results
