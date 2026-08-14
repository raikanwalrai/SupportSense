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


def validate_experiment_config(config: dict[str, Any]) -> None:
    """Validate the minimum required experiment configuration."""

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
