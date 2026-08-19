import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import mlflow
import mlflow.sklearn
from mlflow import MlflowClient


DEFAULT_EXPERIMENT_NAME = "SupportSense Baseline"


@dataclass(frozen=True)
class MLModelInfo:
    """Metadata describing the loaded MLflow model."""

    experiment_name: str
    run_id: str
    model_id: str
    model_name: str
    status: str


@dataclass(frozen=True)
class MLPrediction:
    """Prediction returned by the SupportSense ML model."""

    prediction: str
    model: MLModelInfo


def _tracking_uri() -> str:
    """Return the configured MLflow tracking URI."""

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")

    if not tracking_uri:
        raise RuntimeError(
            "MLFLOW_TRACKING_URI is not set."
        )

    return tracking_uri


def _client() -> MlflowClient:
    """Create an MLflow client using the configured tracking URI."""

    tracking_uri = _tracking_uri()

    mlflow.set_tracking_uri(tracking_uri)

    return MlflowClient(
        tracking_uri=tracking_uri
    )


def _latest_logged_model() -> tuple[Any, Any]:
    """Find the latest READY logged model for SupportSense ML."""

    client = _client()

    experiment = client.get_experiment_by_name(
        DEFAULT_EXPERIMENT_NAME
    )

    if experiment is None:
        raise RuntimeError(
            f"MLflow experiment not found: "
            f"{DEFAULT_EXPERIMENT_NAME}"
        )

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
        max_results=20,
    )

    for run in runs:
        logged_models = client.search_logged_models(
            experiment_ids=[experiment.experiment_id],
            filter_string=(
                f"source_run_id = '{run.info.run_id}'"
            ),
        )

        for logged_model in logged_models:
            if logged_model.status == "READY":
                return run, logged_model

    raise RuntimeError(
        "No READY SupportSense MLflow model was found."
    )


@lru_cache(maxsize=1)
def load_ml_model() -> tuple[Any, MLModelInfo]:
    """
    Load and cache the latest READY SupportSense MLflow model.

    The model is cached so that every incoming ticket does not
    repeatedly download the model from MLflow.
    """

    run, logged_model = _latest_logged_model()

    model_uri = (
        f"models:/{logged_model.model_id}"
    )

    model = mlflow.sklearn.load_model(
        model_uri
    )

    model_info = MLModelInfo(
        experiment_name=DEFAULT_EXPERIMENT_NAME,
        run_id=run.info.run_id,
        model_id=logged_model.model_id,
        model_name=logged_model.name,
        status=logged_model.status,
    )

    return model, model_info


def predict_ticket(text: str) -> MLPrediction:
    """Predict the category of a support ticket."""

    if not text or not text.strip():
        raise ValueError(
            "Ticket text must not be empty."
        )

    model, model_info = load_ml_model()

    predictions = model.predict(
        [text]
    )

    if len(predictions) != 1:
        raise RuntimeError(
            "ML model returned an unexpected number "
            "of predictions."
        )

    prediction = str(predictions[0])

    if not prediction:
        raise RuntimeError(
            "ML model returned an empty prediction."
        )

    return MLPrediction(
        prediction=prediction,
        model=model_info,
    )


def clear_model_cache() -> None:
    """Clear the cached ML model.

    This will be used later when a newly trained model becomes
    the active production candidate.
    """

    load_ml_model.cache_clear()
