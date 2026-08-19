from pathlib import Path

import mlflow
from mlflow import MlflowClient


MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"


def test_baseline_experiment_logs_and_loads_sklearn_model():
    """Verify the baseline experiment logs a usable sklearn model."""

    from src.experiments.runner import run_experiment

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    result = run_experiment(
        Path("configs/experiments.yaml")
    )

    assert result["model_artifact"] == "model"
    assert result["mlflow_run_id"]

    client = MlflowClient(
        tracking_uri=MLFLOW_TRACKING_URI
    )

    run = client.get_run(
        result["mlflow_run_id"]
    )

    assert run.info.status == "FINISHED"

    logged_models = client.search_logged_models(
        experiment_ids=[run.info.experiment_id],
        filter_string=(
            f"source_run_id = '{result['mlflow_run_id']}'"
        ),
    )

    assert logged_models, (
        "No MLflow logged model found for the run"
    )

    logged_model = logged_models[0]

    assert logged_model.name == "model"

    model_id = logged_model.model_id

    model_uri = f"models:/{model_id}"

    loaded_model = mlflow.sklearn.load_model(
        model_uri
    )

    predictions = loaded_model.predict(
        ["I cannot login to my account"]
    )

    assert len(predictions) == 1
    assert predictions[0]
