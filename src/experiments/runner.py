import os
from pathlib import Path
from typing import Any

from sklearn.pipeline import Pipeline

import mlflow
import mlflow.sklearn

from src.config.experiment_config import (
    load_experiment_config,
    validate_experiment_config,
)
from src.features.tfidf import (
    fit_tfidf,
    load_split,
    transform_tfidf,
)
from src.models.baseline import (
    create_baseline_model,
    evaluate_model,
)


DEFAULT_CONFIG_PATH = Path("configs/experiments.yaml")

MLFLOW_EXPERIMENT_NAME = "SupportSense Baseline"


def _configure_mlflow() -> None:
    """Configure MLflow from the environment."""
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")

    if not tracking_uri:
        raise RuntimeError(
            "MLFLOW_TRACKING_URI is not set. "
            "Source scripts/lib/dev-config.sh before running "
            "the experiment."
        )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)


def run_experiment(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """
    Run a configured SupportSense experiment.

    Returns the experiment configuration, metrics,
    feature shapes, and model information.

    The experiment is also recorded in MLflow.
    """

    config = load_experiment_config(config_path)
    validate_experiment_config(config)

    _configure_mlflow()

    data_config = config["data"]
    model_config = config["model"]
    experiment_config = config["experiment"]
    feature_config = config["features"]

    train_df = load_split(data_config["train_path"])
    validation_df = load_split(data_config["validation_path"])

    from src.features.tfidf import create_tfidf_vectorizer

    vectorizer = create_tfidf_vectorizer(config)

    X_train = fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    X_validation = transform_tfidf(
        vectorizer,
        validation_df["text"],
    )

    model = create_baseline_model(config)

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "experiment_name": experiment_config["name"],
                "random_state": experiment_config["random_state"],
                "primary_metric": experiment_config["primary_metric"],
                "model_type": model_config["type"],
                "model_max_iter": model_config["max_iter"],
                "model_random_state": model_config["random_state"],
                "feature_type": feature_config["type"],
                "feature_ngram_range": str(
                    feature_config["ngram_range"]
                ),
                "feature_min_df": feature_config["min_df"],
                "feature_max_df": feature_config["max_df"],
                "feature_sublinear_tf": feature_config[
                    "sublinear_tf"
                ],
            }
        )

        model.fit(
            X_train,
            train_df["category"],
        )

        pipeline = Pipeline(
            steps=[
                ("tfidf", vectorizer),
                ("classifier", model),
            ]
        )

        metrics = evaluate_model(
            model,
            X_validation,
            validation_df["category"],
        )

        mlflow.log_metrics(
            {
                "accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
                "weighted_f1": metrics["weighted_f1"],
            }
        )

        mlflow.sklearn.log_model(
            pipeline,
            name="model",
        )

        mlflow.set_tag(
            "model_stage",
            "candidate",
        )

        mlflow.set_tag(
            "model_framework",
            "sklearn_pipeline",
        )

        mlflow.set_tag(
            "experiment_runner",
            "baseline",
        )

        mlflow.set_tag(
            "mlflow_run_status",
            "completed",
        )

        run_id = run.info.run_id

    return {
        "experiment_name": experiment_config["name"],
        "random_state": experiment_config["random_state"],
        "primary_metric": experiment_config["primary_metric"],
        "model_type": model_config["type"],
        "metrics": metrics,
        "train_shape": X_train.shape,
        "validation_shape": X_validation.shape,
        "num_classes": len(model.classes_),
        "model_artifact": "model",
        "mlflow_experiment": MLFLOW_EXPERIMENT_NAME,
        "mlflow_run_id": run_id,
    }


if __name__ == "__main__":
    result = run_experiment()

    print()
    print("=" * 70)
    print("SupportSense Experiment Runner")
    print("=" * 70)

    print()
    print(f"Experiment     : {result['experiment_name']}")
    print(f"Model          : {result['model_type']}")
    print(f"Primary metric : {result['primary_metric']}")
    print(f"Random state   : {result['random_state']}")

    print()
    print("## Feature Matrix")

    print(f"Training       : {result['train_shape']}")
    print(f"Validation     : {result['validation_shape']}")

    print()
    print("## Classes")

    print(f"Number of classes : {result['num_classes']}")

    print()
    print("## Evaluation")

    print(f"Accuracy       : {result['metrics']['accuracy']:.4f}")
    print(f"Macro F1       : {result['metrics']['macro_f1']:.4f}")
    print(f"Weighted F1    : {result['metrics']['weighted_f1']:.4f}")

    print()
    print("## MLflow")

    print(f"Experiment     : {result['mlflow_experiment']}")
    print(f"Run ID         : {result['mlflow_run_id']}")
