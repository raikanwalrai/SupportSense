"""
SupportSense deep-learning training experiment.

Architecture:
    Embedding -> Mean Pooling -> Linear Classifier

This version provides:
    - configurable training
    - reproducibility
    - validation evaluation
    - best-model checkpointing

MLflow integration will be added next.
"""

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import Adam

from src.models.deep_learning.loaders import build_dataloaders
from src.models.deep_learning.model import SupportSenseTextClassifier
from src.models.deep_learning.reproducibility import set_seed


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
):

    set_seed(seed)

    if device is None:
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    (
        train_loader,
        validation_loader,
        tokenizer,
        label_to_id,
        id_to_label,
    ) = build_dataloaders(
        train_path="data/raw/train.csv",
        validation_path="data/processed/validation.csv",
        max_vocab_size=max_vocab_size,
        max_length=max_length,
        batch_size=batch_size,
    )

    model = SupportSenseTextClassifier(
        vocab_size=tokenizer.vocab_size,
        embedding_dim=embedding_dim,
        num_classes=len(label_to_id),
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
    }

    print("===== SUPPORTSENSE DL TRAINING =====")
    print("Device          :", device)
    print("Seed            :", seed)
    print("Vocabulary      :", tokenizer.vocab_size)
    print("Embedding dim   :", embedding_dim)
    print("Classes         :", len(label_to_id))
    print("Batch size      :", batch_size)
    print("Learning rate   :", learning_rate)
    print("Epochs          :", epochs)
    print("Checkpoint      :", checkpoint_path)

    history = []

    best_validation_loss = float("inf")
    best_epoch = None

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

            save_checkpoint(
                model=model,
                tokenizer=tokenizer,
                label_to_id=label_to_id,
                config=config,
                path=checkpoint_path,
            )

            print(
                f"  ✓ New best model saved "
                f"(validation loss: "
                f"{validation_loss:.4f})"
            )

    print()
    print("===== TRAINING COMPLETE =====")
    print("Best epoch         :", best_epoch)
    print("Best validation loss:", f"{best_validation_loss:.4f}")
    print("Checkpoint         :", checkpoint_path)

    return model, history


def parse_args():
    """Parse command-line training configuration."""

    parser = argparse.ArgumentParser(
        description="Train SupportSense deep-learning classifier."
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
    )

    parser.add_argument(
        "--embedding-dim",
        type=int,
        default=64,
    )

    parser.add_argument(
        "--max-vocab-size",
        type=int,
        default=2500,
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=48,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cpu", "cuda"],
    )

    parser.add_argument(
        "--checkpoint-path",
        type=str,
        default="models/deep_learning/best_model.pt",
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        embedding_dim=args.embedding_dim,
        max_vocab_size=args.max_vocab_size,
        max_length=args.max_length,
        seed=args.seed,
        device=args.device,
        checkpoint_path=args.checkpoint_path,
    )
