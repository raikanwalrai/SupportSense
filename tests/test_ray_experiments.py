from pathlib import Path

from src.distributed.ray_experiments import (
    build_experiment_configs,
    run_ray_experiments,
    select_best_experiment,
)


CONFIG_PATH = Path("configs/experiments.yaml")


def test_build_experiment_configs_returns_candidates():
    configs = build_experiment_configs()

    assert len(configs) == 4


def test_experiment_configs_have_required_parameters():
    configs = build_experiment_configs()

    for config in configs:
        assert "C" in config
        assert "class_weight" in config


def test_experiment_configs_contain_expected_c_values():
    configs = build_experiment_configs()

    values = sorted(config["C"] for config in configs)

    assert values == [0.5, 1.0, 1.0, 2.0]


def test_ray_experiment_returns_results():
    results = run_ray_experiments(CONFIG_PATH)

    assert isinstance(results, list)
    assert len(results) == 4


def test_ray_results_contain_metrics():
    results = run_ray_experiments(CONFIG_PATH)

    for result in results:
        assert "C" in result
        assert "class_weight" in result
        assert "accuracy" in result
        assert "macro_f1" in result
        assert "weighted_f1" in result


def test_ray_results_have_valid_metrics():
    results = run_ray_experiments(CONFIG_PATH)

    for result in results:
        assert 0.0 <= result["accuracy"] <= 1.0
        assert 0.0 <= result["macro_f1"] <= 1.0
        assert 0.0 <= result["weighted_f1"] <= 1.0


def test_best_result_has_highest_macro_f1():
    results = run_ray_experiments(CONFIG_PATH)

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
