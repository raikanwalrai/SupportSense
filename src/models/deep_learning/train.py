"""
SupportSense deep-learning training experiment.

Architecture:
    Embedding -> Mean Pooling -> Linear Classifier

MLOps capabilities:
    - configurable training
    - reproducibility
    - validation evaluation
    - best-model checkpointing
    - MLflow experiment tracking
"""

import argparse
import os
from pathlib import Path

import mlflow
import mlflow.pytorch

try:
    from ray import tune as ray_tune
except ImportError:
    ray_tune = None

import torch
import torch.nn as nn
from mlflow.models import infer_signature
from torch.optim import Adam

from src.config.deep_learning_config import (
    get_training_profile,
    load_deep_learning_config,
)
from src.models.deep_learning.loaders import build_dataloaders
from src.models.deep_learning.model import SupportSenseTextClassifier
from src.models.deep_learning.reproducibility import set_seed


EXPERIMENT_NAME = "SupportSense-DL"



def run_epoch(
    model,
    loader,
    loss_fn,
    optimizer=None,
    device="cpu",
):
    """Run one training or validation epoch."""

    is_training = optimizer is not None

    if is_training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    for batch in loader:

        input_ids = batch["input_ids"].to(device)
        labels = batch["label"].to(device)

        if is_training:
            optimizer.zero_grad()

        with torch.set_grad_enabled(is_training):

            logits = model(input_ids)

            loss = loss_fn(logits, labels)

            if is_training:
                loss.backward()
                optimizer.step()

        batch_size = labels.size(0)

        total_loss += loss.item() * batch_size

        predictions = logits.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += batch_size

    average_loss = total_loss / total
    accuracy = correct / total

    return average_loss, accuracy


def save_checkpoint(
    model,
    tokenizer,
    label_to_id,
    config,
    path,
):
    """Save model weights and metadata required for reuse."""

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "vocab_size": tokenizer.vocab_size,
        "embedding_dim": config["embedding_dim"],
        "num_classes": len(label_to_id),
        "max_length": config["max_length"],
        "token_to_id": tokenizer.token_to_id,
        "label_to_id": label_to_id,
    }

    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    torch.save(
        checkpoint,
        path,
    )


def train(
    epochs=3,
    batch_size=32,
    learning_rate=0.001,
    embedding_dim=64,
    max_vocab_size=2500,
    max_length=48,
    seed=42,
    device=None,
    checkpoint_path="models/deep_learning/best_model.pt",
    patience=3,
    dropout=0.0,
    use_ray=False,
):

    set_seed(seed)

    if device is None:
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    mlflow_tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI"
    )

    if not mlflow_tracking_uri:
        raise RuntimeError(
            "MLFLOW_TRACKING_URI is not set. "
            "Run: source .dev/environment.sh"
        )

    mlflow.set_tracking_uri(
        mlflow_tracking_uri
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    project_root = Path(__file__).resolve().parents[3]

    train_path = (
        project_root
        / "data"
        / "processed"
        / "train.csv"
    )

    validation_path = (
        project_root
        / "data"
        / "processed"
        / "validation.csv"
    )

    (
        train_loader,
        validation_loader,
        tokenizer,
        label_to_id,
        id_to_label,
    ) = build_dataloaders(
        train_path=str(train_path),
        validation_path=str(validation_path),
        max_vocab_size=max_vocab_size,
        max_length=max_length,
        batch_size=batch_size,
    )

    model = SupportSenseTextClassifier(
        vocab_size=tokenizer.vocab_size,
        embedding_dim=embedding_dim,
        num_classes=len(label_to_id),
        dropout=dropout,
    ).to(device)

    loss_fn = nn.CrossEntropyLoss()

    optimizer = Adam(
        model.parameters(),
        lr=learning_rate,
    )

    config = {
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "embedding_dim": embedding_dim,
        "max_vocab_size": max_vocab_size,
        "max_length": max_length,
        "seed": seed,
        "device": device,
        "patience": patience,
        "dropout": dropout,
        "vocab_size": tokenizer.vocab_size,
        "num_classes": len(label_to_id),
    }

    print("===== SUPPORTSENSE DL TRAINING =====")
    print("MLflow URI      :", mlflow_tracking_uri)
    print("Experiment      :", EXPERIMENT_NAME)
    print("Device          :", device)
    print("Seed            :", seed)
    print("Vocabulary      :", tokenizer.vocab_size)
    print("Embedding dim   :", embedding_dim)
    print("Classes         :", len(label_to_id))
    print("Batch size      :", batch_size)
    print("Learning rate   :", learning_rate)
    print("Epochs          :", epochs)
    print("Patience        :", patience)
    print("Dropout         :", dropout)
    print("Checkpoint      :", checkpoint_path)

    with mlflow.start_run() as run:

        print("MLflow Run ID   :", run.info.run_id)

        mlflow.log_params(config)

        history = []

        best_validation_loss = float("inf")
        best_epoch = None
        epochs_without_improvement = 0

        for epoch in range(epochs):

            train_loss, train_accuracy = run_epoch(
                model=model,
                loader=train_loader,
                loss_fn=loss_fn,
                optimizer=optimizer,
                device=device,
            )

            validation_loss, validation_accuracy = run_epoch(
                model=model,
                loader=validation_loader,
                loss_fn=loss_fn,
                optimizer=None,
                device=device,
            )

            metrics = {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "train_accuracy": train_accuracy,
                "validation_loss": validation_loss,
                "validation_accuracy": validation_accuracy,
            }

            history.append(metrics)

            mlflow.log_metrics(
                {
                    "train_loss": train_loss,
                    "train_accuracy": train_accuracy,
                    "validation_loss": validation_loss,
                    "validation_accuracy": validation_accuracy,
                },
                step=epoch + 1,
            )

            print()
            print(f"Epoch {epoch + 1}/{epochs}")

            print(
                f"  Train      "
                f"Loss: {train_loss:.4f} "
                f"Accuracy: {train_accuracy:.4f}"
            )

            print(
                f"  Validation "
                f"Loss: {validation_loss:.4f} "
                f"Accuracy: {validation_accuracy:.4f}"
            )

            if validation_loss < best_validation_loss:

                best_validation_loss = validation_loss
                best_epoch = epoch + 1
                epochs_without_improvement = 0

                save_checkpoint(
                    model=model,
                    tokenizer=tokenizer,
                    label_to_id=label_to_id,
                    config=config,
                    path=checkpoint_path,
                )

                mlflow.log_artifact(
                    checkpoint_path,
                    artifact_path="model_checkpoint",
                )

                print(
                    f"  ✓ New best model saved "
                    f"(validation loss: "
                    f"{validation_loss:.4f})"
                )

            else:

                epochs_without_improvement += 1

                print(
                    f"  No improvement "
                    f"({epochs_without_improvement}/"
                    f"{patience})"
                )

                if epochs_without_improvement >= patience:

                    print()
                    print(
                        "  Early stopping triggered."
                    )

                    print(
                        f"  No validation improvement "
                        f"for {patience} epochs."
                    )

                    break


        mlflow.log_metric(
            "best_validation_loss",
            best_validation_loss,
        )

        mlflow.log_metric(
            "best_epoch",
            best_epoch,
        )

        # Log the PyTorch model itself as an MLflow model.
        example_batch = next(
            iter(validation_loader)
        )["input_ids"][:1].to(device)

        with torch.no_grad():
            example_output = model(
                example_batch
            ).detach().cpu().numpy()

        signature = infer_signature(
            example_batch.cpu().numpy(),
            example_output,
        )

        mlflow.pytorch.log_model(
            model,
            name="model",
            signature=signature,
            input_example=example_batch.cpu(),
        )

        print()
        print("===== TRAINING COMPLETE =====")
        print("Best epoch          :", best_epoch)
        print(
            "Best validation loss:",
            f"{best_validation_loss:.4f}",
        )
        print("Checkpoint          :", checkpoint_path)
        print("MLflow Run ID       :", run.info.run_id)

    return {
           "model": model,
           "history": history,
           "run_id": run.info.run_id,
           "checkpoint_path": checkpoint_path,
           "best_epoch": best_epoch,
           "best_validation_loss": best_validation_loss,
        }


def parse_args():
    """Parse command-line training configuration."""

    parser = argparse.ArgumentParser(
        description="Train SupportSense deep-learning classifier."
    )

    parser.add_argument(
        "--profile",
        type=str,
        default="full",
        choices=["smoke", "full"],
        help="Deep-learning configuration profile.",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--embedding-dim",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--max-vocab-size",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cpu", "cuda"],
    )

    parser.add_argument(
	    "--patience",
	    type=int,
	    default=None,
    )

    parser.add_argument(
        "--dropout",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--checkpoint-path",
        type=str,
        default=None,
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    config = load_deep_learning_config()

    profile = get_training_profile(
        config,
        args.profile,
    )

    train(
        epochs=(
            args.epochs
            if args.epochs is not None
            else profile["epochs"]
        ),
        batch_size=(
            args.batch_size
            if args.batch_size is not None
            else profile["batch_size"]
        ),
        learning_rate=(
            args.learning_rate
            if args.learning_rate is not None
            else profile["learning_rate"]
        ),
        embedding_dim=(
            args.embedding_dim
            if args.embedding_dim is not None
            else profile["embedding_dim"]
        ),
        max_vocab_size=(
            args.max_vocab_size
            if args.max_vocab_size is not None
            else profile["max_vocab_size"]
        ),
        max_length=(
            args.max_length
            if args.max_length is not None
            else profile["max_length"]
        ),
        seed=(
            args.seed
            if args.seed is not None
            else profile["seed"]
        ),
        device=(
            args.device
            if args.device is not None
            else profile["device"]
        ),
        patience=(
            args.patience
            if args.patience is not None
            else profile["patience"]
        ),
        dropout=(
            args.dropout
            if args.dropout is not None
            else profile["dropout"]
        ),
        checkpoint_path=(
            args.checkpoint_path
            if args.checkpoint_path is not None
            else profile["checkpoint_path"]
        ),
    )
