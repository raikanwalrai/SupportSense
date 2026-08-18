from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from services.runner import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "supportsense-runner",
    }


def test_dvc_pull_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Data and pipelines are up to date.\n"
    mock_result.stderr = ""

    with patch(
        "services.runner.subprocess.run",
        return_value=mock_result,
    ) as mock_run:
        response = client.post("/dvc/pull")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["operation"] == "dvc_pull"
    assert body["returncode"] == 0
    assert body["stdout"] == "Data and pipelines are up to date.\n"

    mock_run.assert_called_once()


def test_dvc_pull_failure():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "DVC remote unavailable."

    with patch(
        "services.runner.subprocess.run",
        return_value=mock_result,
    ):
        response = client.post("/dvc/pull")

    assert response.status_code == 500

    body = response.json()

    assert body["detail"]["message"] == "DVC pull failed."
    assert body["detail"]["returncode"] == 1
    assert body["detail"]["stderr"] == "DVC remote unavailable."


def test_dvc_pull_timeout():
    import subprocess

    with patch(
        "services.runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd=["dvc", "pull"],
            timeout=300,
        ),
    ):
        response = client.post("/dvc/pull")

    assert response.status_code == 504
    assert response.json()["detail"] == (
        "DVC pull timed out after 300 seconds."
    )


def test_dvc_pull_missing_project_directory():
    with patch(
        "services.runner.PROJECT_DIR",
        Path("/path/that/does/not/exist"),
    ):
        response = client.post("/dvc/pull")

    assert response.status_code == 500
    assert "Project directory not found" in response.json()["detail"]


def test_ray_experiments_success():
    fake_results = [
        {
            "C": 0.5,
            "class_weight": None,
            "accuracy": 0.90,
            "macro_f1": 0.80,
            "weighted_f1": 0.85,
            "run_id": "run-low",
        },
        {
            "C": 2.0,
            "class_weight": None,
            "accuracy": 0.92,
            "macro_f1": 0.87,
            "weighted_f1": 0.88,
            "run_id": "run-best",
        },
    ]

    config_path = Path("configs/experiments.yaml")

    with patch(
        "src.distributed.ray_experiments.run_ray_experiments",
        return_value=fake_results,
    ):
        response = client.post("/ray/experiments")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["operation"] == "ray_experiments"
    assert body["experiments"] == 2
    assert body["results"] == fake_results
    assert body["best"] == fake_results[1]

    assert body["best"]["macro_f1"] == 0.87


def test_ray_experiments_failure():
    with patch(
        "src.distributed.ray_experiments.run_ray_experiments",
        side_effect=RuntimeError("Ray execution failed."),
    ):
        response = client.post("/ray/experiments")

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Ray experiments failed: Ray execution failed."
    )


def test_ray_experiments_missing_config():
    with patch(
        "services.runner.PROJECT_DIR",
        Path("/path/that/does/not/exist"),
    ):
        response = client.post("/ray/experiments")

    assert response.status_code == 500
    assert "Experiment config not found" in response.json()["detail"]


def test_metrics_endpoint_returns_prometheus_output():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    body = response.text

    assert "# HELP supportsense_http_requests_total" in body
    assert "# TYPE supportsense_http_requests_total counter" in body
    assert "# HELP supportsense_http_request_duration_seconds" in body
    assert "# TYPE supportsense_http_request_duration_seconds histogram" in body


def test_health_request_is_recorded_in_metrics():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert 'endpoint="/health"' in body
    assert 'method="GET"' in body
    assert 'status="200"' in body


def test_request_duration_metric_is_recorded():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "supportsense_http_request_duration_seconds_bucket" in body
    assert "supportsense_http_request_duration_seconds_count" in body
    assert "supportsense_http_request_duration_seconds_sum" in body
