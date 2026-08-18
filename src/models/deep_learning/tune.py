"""
SupportSense Deep Learning hyperparameter tuning with Ray Tune.

This first version performs a small end-to-end tuning experiment
with epoch-level metric reporting to Ray Tune.
"""


import os

import mlflow
import ray
from ray import tune
from ray.air import session

from src.models.deep_learning.train import train


def train_trial(config):
    """Run one SupportSense training configuration."""

    print()
    print("===== RAY TRIAL =====")
    print("Configuration:", config)

    train(
        epochs=config["epochs"],
        batch_size=config["batch_size"],
        learning_rate=config["learning_rate"],
        embedding_dim=config["embedding_dim"],
        dropout=config["dropout"],
        seed=42,
        device="cpu",
        patience=config["patience"],
        use_ray=True,
        checkpoint_path=(
            f"models/deep_learning/"
            f"ray_trial_{session.get_trial_id()}.pt"
        ),
    )


def main():

    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000",
    )

    mlflow.set_tracking_uri(tracking_uri)

    print("===== SUPPORTSENSE RAY TUNE =====")
    print("Ray version    :", ray.__version__)
    print("MLflow URI     :", tracking_uri)

    search_space = {
        "epochs": 2,
        "patience": 3,
        "batch_size": 32,

        "learning_rate": 0.001,

        "embedding_dim": 128,

        "dropout": 0.2,
    }

    tuner = tune.Tuner(
        train_trial,
        param_space=search_space,
        tune_config=tune.TuneConfig(
            max_concurrent_trials=1,
        ),
    )

    results = tuner.fit()

    print()
    print("===== RAY TUNE COMPLETE =====")

    for result in results:
        print(
            "Config:",
            result.config,
        )

    print()
    print("===== RAY TUNE EXPERIMENT COMPLETE =====")


if __name__ == "__main__":
    main()
