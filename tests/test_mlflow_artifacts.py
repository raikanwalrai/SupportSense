import mlflow


MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"


def test_mlflow_artifact_lifecycle():
    """Verify MLflow can log, list, and download an artifact."""

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    with mlflow.start_run(
        run_name="automated-artifact-regression"
    ) as run:

        run_id = run.info.run_id

        mlflow.log_text(
            "SupportSense MLflow artifact regression test",
            "verification/mlflow-artifact-test.txt",
        )

        artifact_uri = mlflow.get_artifact_uri()

    # Verify artifact is visible through the MLflow artifact store.
    artifacts = mlflow.artifacts.list_artifacts(
        artifact_uri=artifact_uri,
    )

    paths = {
        artifact.path
        for artifact in artifacts
    }

    assert "artifacts/verification" in paths

    # Verify nested artifact listing.
    verification_uri = (
        f"{artifact_uri}/verification"
    )

    nested_artifacts = mlflow.artifacts.list_artifacts(
        artifact_uri=verification_uri,
    )

    nested_paths = {
        artifact.path
        for artifact in nested_artifacts
    }

    assert (
        "verification/"
        "mlflow-artifact-test.txt"
        in nested_paths
    )

    # Verify artifact can actually be downloaded.
    downloaded_path = mlflow.artifacts.download_artifacts(
        artifact_uri=(
            f"{verification_uri}/"
            "mlflow-artifact-test.txt"
        )
    )

    with open(
        downloaded_path,
        "r",
        encoding="utf-8",
    ) as file:
        content = file.read()

    assert (
        content
        == "SupportSense MLflow artifact regression test"
    )
