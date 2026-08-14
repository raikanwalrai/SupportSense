from pathlib import Path
from typing import Any

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


def run_experiment(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """
    Run a configured SupportSense experiment.

    Returns the experiment configuration, metrics,
    feature shapes, and model information.
    """

    config = load_experiment_config(config_path)
    validate_experiment_config(config)

    data_config = config["data"]
    model_config = config["model"]
    experiment_config = config["experiment"]

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

    model.fit(
        X_train,
        train_df["category"],
    )

    metrics = evaluate_model(
        model,
        X_validation,
        validation_df["category"],
    )

    return {
        "experiment_name": experiment_config["name"],
        "random_state": experiment_config["random_state"],
        "primary_metric": experiment_config["primary_metric"],
        "model_type": model_config["type"],
        "metrics": metrics,
        "train_shape": X_train.shape,
        "validation_shape": X_validation.shape,
        "num_classes": len(model.classes_),
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
