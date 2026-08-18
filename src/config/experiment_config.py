from pathlib import Path
from typing import Any

import yaml


def load_experiment_config(path: str | Path) -> dict[str, Any]:
    """Load an experiment configuration from a YAML file."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Experiment configuration must contain a YAML mapping.")

    return config


def get_ray_profile(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """Return a validated Ray experiment profile."""

    validate_experiment_config(config)
    validate_ray_config(config)

    profiles = config["ray"]["profiles"]

    if profile_name not in profiles:
        raise ValueError(
            f"Unknown Ray profile: {profile_name}. "
            f"Available profiles: {sorted(profiles)}"
        )

    return profiles[profile_name]


def validate_experiment_config(config: dict[str, Any]) -> None:
    """Validate the generic experiment configuration."""

    required_sections = {
        "experiment",
        "data",
        "features",
        "model",
    }

    missing_sections = required_sections - set(config.keys())

    if missing_sections:
        raise ValueError(
            f"Missing configuration sections: {sorted(missing_sections)}"
        )

    required_experiment_keys = {
        "name",
        "random_state",
        "primary_metric",
    }

    missing_experiment_keys = (
        required_experiment_keys - set(config["experiment"].keys())
    )

    if missing_experiment_keys:
        raise ValueError(
            "Missing experiment configuration keys: "
            f"{sorted(missing_experiment_keys)}"
        )

    if "ray" in config:
        validate_ray_config(config)


def validate_ray_config(config: dict[str, Any]) -> None:
    """Validate the Ray-specific experiment configuration."""

    if "ray" not in config:
        raise ValueError(
            "Missing Ray configuration."
        )

    ray_config = config["ray"]

    if not isinstance(ray_config, dict):
        raise ValueError(
            "Ray configuration must be a mapping."
        )

    if "profiles" not in ray_config:
        raise ValueError(
            "Missing ray.profiles configuration."
        )

    profiles = ray_config["profiles"]

    if not isinstance(profiles, dict):
        raise ValueError(
            "ray.profiles must be a mapping."
        )

    required_profiles = {"smoke", "full"}

    missing_profiles = (
        required_profiles - set(profiles.keys())
    )

    if missing_profiles:
        raise ValueError(
            "Missing Ray profiles: "
            f"{sorted(missing_profiles)}"
        )

    for profile_name in required_profiles:
        profile = profiles[profile_name]

        if not isinstance(profile, dict):
            raise ValueError(
                f"Ray profile '{profile_name}' must be a mapping."
            )

        required_profile_keys = {
            "max_iter",
            "candidates",
        }

        missing_profile_keys = (
            required_profile_keys - set(profile.keys())
        )

        if missing_profile_keys:
            raise ValueError(
                f"Missing keys in Ray profile '{profile_name}': "
                f"{sorted(missing_profile_keys)}"
            )

        if not isinstance(profile["candidates"], list):
            raise ValueError(
                f"Ray profile '{profile_name}' candidates "
                "must be a list."
            )

        if not profile["candidates"]:
            raise ValueError(
                f"Ray profile '{profile_name}' must contain "
                "at least one candidate."
            )

        for candidate in profile["candidates"]:
            if not isinstance(candidate, dict):
                raise ValueError(
                    f"Ray profile '{profile_name}' contains "
                    "an invalid candidate."
                )

            required_candidate_keys = {
                "C",
                "class_weight",
            }

            missing_candidate_keys = (
                required_candidate_keys - set(candidate.keys())
            )

            if missing_candidate_keys:
                raise ValueError(
                    f"Missing candidate keys in Ray profile "
                    f"'{profile_name}': "
                    f"{sorted(missing_candidate_keys)}"
                )
    execution = ray_config.get("execution")

    if execution is None:
        raise ValueError(
            "Missing ray.execution configuration."
        )

    if not isinstance(execution, dict):
        raise ValueError(
            "ray.execution must be a mapping."
        )

    required_execution_keys = {
        "num_cpus",
        "max_concurrent_experiments",
    }

    missing_execution_keys = (
        required_execution_keys - set(execution.keys())
    )

    if missing_execution_keys:
        raise ValueError(
            "Missing ray.execution configuration keys: "
            f"{sorted(missing_execution_keys)}"
        )

    if not isinstance(execution["num_cpus"], int):
        raise ValueError(
            "ray.execution.num_cpus must be an integer."
        )

    if execution["num_cpus"] < 1:
        raise ValueError(
            "ray.execution.num_cpus must be at least 1."
        )

    if not isinstance(
        execution["max_concurrent_experiments"],
        int,
    ):
        raise ValueError(
            "ray.execution.max_concurrent_experiments "
            "must be an integer."
        )

    if execution["max_concurrent_experiments"] < 1:
        raise ValueError(
            "ray.execution.max_concurrent_experiments "
            "must be at least 1."
        )


if __name__ == "__main__":
    config_path = "configs/experiments.yaml"

    config = load_experiment_config(config_path)
    validate_experiment_config(config)

    print()
    print("=" * 70)
    print("SupportSense Experiment Configuration")
    print("=" * 70)

    print(f"Experiment    : {config['experiment']['name']}")
    print(f"Random state  : {config['experiment']['random_state']}")
    print(f"Primary metric: {config['experiment']['primary_metric']}")
    print(f"Feature type  : {config['features']['type']}")
    print(f"Model type    : {config['model']['type']}")
