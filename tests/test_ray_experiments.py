import pytest

from pathlib import Path

from src.config.experiment_config import (
    load_experiment_config,
)
from src.distributed.ray_experiments import (
    build_experiment_configs,
    run_ray_experiments,
    select_best_experiment,
)


CONFIG_PATH = Path("configs/experiments.yaml")


def load_config():
    return load_experiment_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def ray_smoke_results():
    """Run the real Ray smoke experiment once for this test module."""

    return run_ray_experiments(
        CONFIG_PATH,
        profile_name="smoke",
    )


def test_build_experiment_configs_returns_smoke_candidates():
    config = load_config()

    candidates = build_experiment_configs(
        config,
        "smoke",
    )

    assert len(candidates) == 1


def test_build_experiment_configs_returns_full_candidates():
    config = load_config()

    candidates = build_experiment_configs(
        config,
        "full",
    )

    assert len(candidates) == 4


def test_experiment_configs_have_required_parameters():
    config = load_config()

    for profile_name in ("smoke", "full"):
        candidates = build_experiment_configs(
            config,
            profile_name,
        )

        for candidate in candidates:
            assert "C" in candidate
            assert "class_weight" in candidate


def test_experiment_configs_contain_expected_full_c_values():
    config = load_config()

    candidates = build_experiment_configs(
        config,
        "full",
    )

    values = sorted(
        candidate["C"]
        for candidate in candidates
    )

    assert values == [0.5, 1.0, 1.0, 2.0]


def test_ray_experiment_returns_results(ray_smoke_results):
    results = ray_smoke_results

    assert isinstance(results, list)
    assert len(results) == 1


def test_ray_results_contain_metrics(ray_smoke_results):
    results = ray_smoke_results

    for result in results:
        assert "C" in result
        assert "class_weight" in result
        assert "accuracy" in result
        assert "macro_f1" in result
        assert "weighted_f1" in result


def test_ray_results_have_valid_metrics(ray_smoke_results):
    results = ray_smoke_results

    for result in results:
        assert 0.0 <= result["accuracy"] <= 1.0
        assert 0.0 <= result["macro_f1"] <= 1.0
        assert 0.0 <= result["weighted_f1"] <= 1.0


def test_best_result_has_highest_macro_f1(ray_smoke_results):
    results = ray_smoke_results

    best = max(results, key=lambda result: result["macro_f1"])

    assert best["macro_f1"] == max(
        result["macro_f1"] for result in results
    )

def test_select_best_experiment_uses_macro_f1():
    results = [
        {
            "C": 0.5,
            "class_weight": None,
            "accuracy": 0.90,
            "macro_f1": 0.80,
            "weighted_f1": 0.85,
        },
        {
            "C": 2.0,
            "class_weight": None,
            "accuracy": 0.86,
            "macro_f1": 0.87,
            "weighted_f1": 0.86,
        },
        {
            "C": 1.0,
            "class_weight": "balanced",
            "accuracy": 0.88,
            "macro_f1": 0.84,
            "weighted_f1": 0.88,
        },
    ]

    best = select_best_experiment(results)

    assert best["C"] == 2.0
    assert best["macro_f1"] == 0.87

def test_select_best_experiment_rejects_empty_results():
    import pytest

    with pytest.raises(ValueError):
        select_best_experiment([])

def test_ray_execution_configuration_is_available():
    config = load_config()

    execution = config["ray"]["execution"]

    assert execution["num_cpus"] == 2
    assert execution["max_concurrent_experiments"] == 1

def test_select_best_experiment_marks_best_result():
    results = [
        {
            "C": 0.5,
            "class_weight": None,
            "accuracy": 0.82,
            "macro_f1": 0.80,
            "weighted_f1": 0.81,
        },
        {
            "C": 2.0,
            "class_weight": None,
            "accuracy": 0.86,
            "macro_f1": 0.86,
            "weighted_f1": 0.86,
        },
    ]

    best = select_best_experiment(results)

    assert best["C"] == 2.0
    assert best["macro_f1"] == 0.86

def test_ray_results_include_mlflow_run_id(ray_smoke_results):
    results = ray_smoke_results

    for result in results:
        assert "run_id" in result
        assert isinstance(result["run_id"], str)
        assert result["run_id"]

def test_select_best_experiment_preserves_mlflow_run_id():
    results = [
        {
            "C": 0.5,
            "class_weight": None,
            "accuracy": 0.82,
            "macro_f1": 0.80,
            "weighted_f1": 0.81,
            "run_id": "run-low",
        },
        {
            "C": 2.0,
            "class_weight": None,
            "accuracy": 0.86,
            "macro_f1": 0.86,
            "weighted_f1": 0.86,
            "run_id": "run-best",
        },
    ]

    best = select_best_experiment(results)

    assert best["C"] == 2.0
    assert best["macro_f1"] == 0.86
    assert best["run_id"] == "run-best"
