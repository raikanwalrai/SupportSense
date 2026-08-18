"""
SupportSense Deep Learning hyperparameter tuning with Ray Tune.

Configuration is loaded from configs/deep_learning.yaml.

Training profile:
    - smoke
    - full

The smoke profile is intended for fast laptop/infrastructure
validation. The full profile is intended for actual experiments.
"""

import argparse
import os
from pathlib import Path

import mlflow
import ray
from ray import tune
from ray.tune import Checkpoint as RayCheckpoint
from ray.tune.schedulers import ASHAScheduler

from src.config.deep_learning_config import (
    get_training_profile,
    get_tuning_profile,
    load_deep_learning_config,
)
from src.models.deep_learning.train import train


def parse_args():
    """Parse Ray Tune configuration options."""

    parser = argparse.ArgumentParser(
        description="Run SupportSense deep-learning Ray Tune experiments."
    )

    parser.add_argument(
        "--profile",
        type=str,
        default="smoke",
        choices=["smoke", "full"],
        help="Ray Tune configuration profile.",
    )

    return parser.parse_args()


def train_trial(config):
    """Run one SupportSense training configuration."""

    trial = config["trial"]

    print()
    print("===== RAY TRIAL =====")
    print("Configuration:", trial)

    # Give every Ray trial an isolated checkpoint location.
    # This prevents concurrent/sequential trials from overwriting
    # the same best_model.pt file.
    trial_dir = Path(
        tune.get_context().get_trial_dir()
    )

    trial_checkpoint_path = (
        trial_dir / "best_model.pt"
    )

    training_result = train(
        epochs=trial["epochs"],
        batch_size=trial["batch_size"],
        learning_rate=trial["learning_rate"],
        embedding_dim=trial["embedding_dim"],
        dropout=trial["dropout"],
        seed=trial["seed"],
        device=trial["device"],
        max_vocab_size=trial["max_vocab_size"],
        max_length=trial["max_length"],
        patience=trial["patience"],
        use_ray=True,
        checkpoint_path=str(
            trial_checkpoint_path
        ),
    )

    # Report the final trial result to Ray Tune.
    #
    # Metrics remain numeric so Ray can use them for scheduling
    # and comparison. The model checkpoint is passed separately
    # through the dedicated checkpoint argument.
    ray_checkpoint = None

    checkpoint_path = Path(
        training_result["checkpoint_path"]
    )

    print()
    print("===== RAY CHECKPOINT DEBUG =====")
    print("Checkpoint path :", checkpoint_path)
    print("Path exists     :", checkpoint_path.exists())
    print("Path is file    :", checkpoint_path.is_file())
    print("Parent exists   :", checkpoint_path.parent.exists())

    if checkpoint_path.parent.exists():
        print("Parent contents :", list(
            checkpoint_path.parent.iterdir()
        ))

    if checkpoint_path.exists():
        ray_checkpoint = RayCheckpoint.from_directory(
            str(checkpoint_path.parent)
        )
        print("Ray checkpoint  :", ray_checkpoint)
    else:
        print("Ray checkpoint  : NOT CREATED")

    tune.report(
        metrics={
            "validation_loss": float(
                training_result["best_validation_loss"]
            ),
            "validation_accuracy": float(
                training_result["history"][
                    training_result["best_epoch"] - 1
                ]["validation_accuracy"]
            ),
            "best_epoch": float(
                training_result["best_epoch"]
            ),
            "best_validation_loss": float(
                training_result["best_validation_loss"]
            ),
        },
        checkpoint=ray_checkpoint,
    )

    return {
        "run_id": training_result["run_id"],
        "checkpoint_path": training_result["checkpoint_path"],
        "best_epoch": training_result["best_epoch"],
        "best_validation_loss": training_result[
            "best_validation_loss"
        ],
    }

def main():

    args = parse_args()

    config = load_deep_learning_config()

    training_profile = get_training_profile(
        config,
        args.profile,
    )

    tuning_profile = get_tuning_profile(
        config,
        args.profile,
    )

    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000",
    )

    mlflow.set_tracking_uri(tracking_uri)

    print("===== SUPPORTSENSE RAY TUNE =====")
    print("Ray version    :", ray.__version__)
    print("MLflow URI     :", tracking_uri)
    print("Profile        :", args.profile)

    # Build complete trial configurations by combining:
    #
    #   common training profile
    #       +
    #   trial-specific hyperparameters
    #
    # This keeps model parameters centralized in YAML.
    trial_configs = []

    for trial in tuning_profile["trials"]:

        complete_trial = {
            **training_profile,
            **trial,
        }

        trial_configs.append(
            complete_trial
        )

    print("Trials         :", len(trial_configs))

    param_space = {
        "trial": tune.grid_search(
            trial_configs
        )
    }

    scheduler = ASHAScheduler(
        metric="validation_loss",
        mode="min",
        max_t=tuning_profile["max_t"],
        grace_period=tuning_profile["grace_period"],
        reduction_factor=tuning_profile["reduction_factor"],
    )

    tuner = tune.Tuner(
        train_trial,
        param_space=param_space,
        tune_config=tune.TuneConfig(
            scheduler=scheduler,
            max_concurrent_trials=(
                tuning_profile["max_concurrent_trials"]
            ),
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

        print(
            "Validation loss:",
            result.metrics.get("validation_loss"),
        )

        print(
            "Validation accuracy:",
            result.metrics.get("validation_accuracy"),
        )

        print(
            "Best epoch:",
            result.metrics.get("best_epoch"),
        )

        print(
            "Best validation loss:",
            result.metrics.get("best_validation_loss"),
        )

        print(
            "Ray checkpoint:",
            result.checkpoint,
        )

    print()
    print("===== RAY TUNE EXPERIMENT COMPLETE =====")


if __name__ == "__main__":
    main()
