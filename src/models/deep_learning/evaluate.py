"""
SupportSense Deep Learning evaluation.

Evaluates a selected MLflow checkpoint on the untouched test dataset
and records the evaluation results as a separate MLflow run.
"""

import argparse
import json
import tempfile
from pathlib import Path

import mlflow
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.models.deep_learning.dataset import SupportSenseDataset
from src.models.deep_learning.model import SupportSenseTextClassifier
from src.models.deep_learning.tokenizer import SimpleTokenizer


EVALUATION_EXPERIMENT = "SupportSense-DL-Evaluation"


def download_checkpoint(run_id: str) -> Path:
    """Download the selected MLflow checkpoint."""

    tmpdir = tempfile.mkdtemp(
        prefix="supportsense_eval_"
    )

    downloaded = mlflow.artifacts.download_artifacts(
        run_id=run_id,
        artifact_path="model_checkpoint",
        dst_path=tmpdir,
    )

    pt_files = list(
        Path(downloaded).rglob("*.pt")
    )

    if not pt_files:
        raise FileNotFoundError(
            f"No .pt checkpoint found in {downloaded}"
        )

    return pt_files[0]


def evaluate(
    run_id: str,
    test_path: str,
    batch_size: int = 32,
    device: str = "cpu",
):
    """Evaluate a selected MLflow checkpoint."""

    mlflow.set_tracking_uri(
        "http://127.0.0.1:5000"
    )

    mlflow.set_experiment(
        EVALUATION_EXPERIMENT
    )

    checkpoint_path = download_checkpoint(
        run_id
    )

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    token_to_id = checkpoint["token_to_id"]
    label_to_id = checkpoint["label_to_id"]

    id_to_label = {
        value: key
        for key, value in label_to_id.items()
    }

    tokenizer = SimpleTokenizer(
        max_vocab_size=checkpoint["vocab_size"],
    )

    tokenizer.token_to_id = token_to_id

    tokenizer.id_to_token = {
        value: key
        for key, value in token_to_id.items()
    }

    test_df = pd.read_csv(
        test_path
    )

    dataset = SupportSenseDataset(
        dataframe=test_df,
        tokenizer=tokenizer,
        label_to_id=label_to_id,
    )

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    model = SupportSenseTextClassifier(
        vocab_size=checkpoint["vocab_size"],
        embedding_dim=checkpoint["embedding_dim"],
        num_classes=checkpoint["num_classes"],
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    all_predictions = []
    all_labels = []

    with torch.no_grad():

        for batch in loader:

            input_ids = batch[
                "input_ids"
            ].to(device)

            labels = batch[
                "label"
            ].to(device)

            logits = model(
                input_ids
            )

            predictions = torch.argmax(
                logits,
                dim=1,
            )

            all_predictions.extend(
                predictions.cpu().tolist()
            )

            all_labels.extend(
                labels.cpu().tolist()
            )

    labels = list(
        range(
            checkpoint["num_classes"]
        )
    )

    target_names = [
        id_to_label[i]
        for i in labels
    ]

    accuracy = accuracy_score(
        all_labels,
        all_predictions,
    )

    macro_precision = precision_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        all_labels,
        all_predictions,
        average="weighted",
        zero_division=0,
    )

    report = classification_report(
        all_labels,
        all_predictions,
        labels=labels,
        target_names=target_names,
        zero_division=0,
    )

    cm = confusion_matrix(
        all_labels,
        all_predictions,
        labels=labels,
    )

    print(
        "===== SUPPORTSENSE DL TEST EVALUATION ====="
    )
    print()
    print("Source MLflow Run :", run_id)
    print("Checkpoint        :", checkpoint_path)
    print("Test dataset      :", test_path)
    print("Test samples      :", len(test_df))
    print("Classes           :", checkpoint["num_classes"])
    print("Device             :", device)

    print()
    print("===== TEST METRICS =====")
    print(
        f"Accuracy        : {accuracy:.4f}"
    )
    print(
        f"Macro precision : {macro_precision:.4f}"
    )
    print(
        f"Macro recall    : {macro_recall:.4f}"
    )
    print(
        f"Macro F1        : {macro_f1:.4f}"
    )
    print(
        f"Weighted F1     : {weighted_f1:.4f}"
    )

    with mlflow.start_run() as run:

        mlflow.log_params(
            {
                "source_run_id": run_id,
                "test_dataset": test_path,
                "test_samples": len(test_df),
                "batch_size": batch_size,
                "device": device,
                "vocab_size": checkpoint[
                    "vocab_size"
                ],
                "embedding_dim": checkpoint[
                    "embedding_dim"
                ],
                "max_length": checkpoint[
                    "max_length"
                ],
                "num_classes": checkpoint[
                    "num_classes"
                ],
            }
        )

        mlflow.log_metrics(
            {
                "test_accuracy": accuracy,
                "test_macro_precision": macro_precision,
                "test_macro_recall": macro_recall,
                "test_macro_f1": macro_f1,
                "test_weighted_f1": weighted_f1,
            }
        )

        with tempfile.TemporaryDirectory(
            prefix="supportsense_eval_artifacts_"
        ) as artifact_dir:

            artifact_dir = Path(
                artifact_dir
            )

            report_path = (
                artifact_dir
                / "classification_report.txt"
            )

            report_path.write_text(
                report
            )

            cm_path = (
                artifact_dir
                / "confusion_matrix.csv"
            )

            cm_df = pd.DataFrame(
                cm,
                index=target_names,
                columns=target_names,
            )

            cm_df.to_csv(
                cm_path
            )

            summary = {
                "source_run_id": run_id,
                "test_dataset": test_path,
                "test_samples": len(test_df),
                "num_classes": checkpoint[
                    "num_classes"
                ],
                "vocab_size": checkpoint[
                    "vocab_size"
                ],
                "embedding_dim": checkpoint[
                    "embedding_dim"
                ],
                "max_length": checkpoint[
                    "max_length"
                ],
                "accuracy": accuracy,
                "macro_precision": macro_precision,
                "macro_recall": macro_recall,
                "macro_f1": macro_f1,
                "weighted_f1": weighted_f1,
            }

            summary_path = (
                artifact_dir
                / "evaluation_summary.json"
            )

            summary_path.write_text(
                json.dumps(
                    summary,
                    indent=2,
                )
            )

            mlflow.log_artifact(
                str(report_path),
                artifact_path="evaluation",
            )

            mlflow.log_artifact(
                str(cm_path),
                artifact_path="evaluation",
            )

            mlflow.log_artifact(
                str(summary_path),
                artifact_path="evaluation",
            )

        print()
        print(
            "===== MLFLOW EVALUATION RUN ====="
        )
        print(
            "Evaluation Run ID :",
            run.info.run_id,
        )
        print(
            "Experiment        :",
            EVALUATION_EXPERIMENT,
        )

    print()
    print(
        "PASS: Test evaluation completed "
        "and logged to MLflow"
    )
    return {
        "source_run_id": run_id,
        "evaluation_run_id": run.info.run_id,
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
    }



def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate SupportSense DL model."
        )
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )

    parser.add_argument(
        "--test-path",
        default="data/raw/test.csv",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    evaluate(
        run_id=args.run_id,
        test_path=args.test_path,
        batch_size=args.batch_size,
        device=args.device,
    )
