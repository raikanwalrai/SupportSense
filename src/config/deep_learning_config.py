"""
SupportSense deep-learning configuration loader.

Loads and validates deep-learning training and Ray Tune
configuration from configs/deep_learning.yaml.
"""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("configs/deep_learning.yaml")


def load_deep_learning_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load and validate the deep-learning YAML configuration."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Deep-learning configuration not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            "Deep-learning configuration must contain a YAML mapping."
        )

    validate_deep_learning_config(config)

    return config


def validate_deep_learning_config(
    config: dict[str, Any],
) -> None:
    """Validate the required deep-learning configuration structure."""

    if "deep_learning" not in config:
        raise ValueError(
            "Missing required 'deep_learning' section."
        )

    deep_learning = config["deep_learning"]

    if not isinstance(deep_learning, dict):
        raise ValueError(
            "'deep_learning' must be a mapping."
        )

    required_sections = {
        "defaults",
        "profiles",
        "tuning",
    }

    missing_sections = (
        required_sections - set(deep_learning.keys())
    )

    if missing_sections:
        raise ValueError(
            "Missing deep-learning configuration sections: "
            f"{sorted(missing_sections)}"
        )

    defaults = deep_learning["defaults"]
    profiles = deep_learning["profiles"]
    tuning = deep_learning["tuning"]

    if not isinstance(defaults, dict):
        raise ValueError(
            "'defaults' must be a mapping."
        )

    if not isinstance(profiles, dict):
        raise ValueError(
            "'profiles' must be a mapping."
        )

    if not isinstance(tuning, dict):
        raise ValueError(
            "'tuning' must be a mapping."
        )

    required_defaults = {
        "seed",
        "device",
        "max_vocab_size",
        "max_length",
        "checkpoint_path",
    }

    missing_defaults = (
        required_defaults - set(defaults.keys())
    )

    if missing_defaults:
        raise ValueError(
            "Missing default configuration keys: "
            f"{sorted(missing_defaults)}"
        )

    required_profiles = {
        "smoke",
        "full",
    }

    missing_profiles = (
        required_profiles - set(profiles.keys())
    )

    if missing_profiles:
        raise ValueError(
            "Missing deep-learning profiles: "
            f"{sorted(missing_profiles)}"
        )

    required_profile_keys = {
        "epochs",
        "batch_size",
        "learning_rate",
        "embedding_dim",
        "patience",
        "dropout",
    }

    for profile_name, profile in profiles.items():

        if not isinstance(profile, dict):
            raise ValueError(
                f"Profile '{profile_name}' must be a mapping."
            )

        missing_keys = (
            required_profile_keys - set(profile.keys())
        )

        if missing_keys:
            raise ValueError(
                f"Profile '{profile_name}' is missing keys: "
                f"{sorted(missing_keys)}"
            )

        _validate_positive_integer(
            profile["epochs"],
            f"{profile_name}.epochs",
        )

        _validate_positive_integer(
            profile["batch_size"],
            f"{profile_name}.batch_size",
        )

        _validate_positive_number(
            profile["learning_rate"],
            f"{profile_name}.learning_rate",
        )

        _validate_positive_integer(
            profile["embedding_dim"],
            f"{profile_name}.embedding_dim",
        )

        _validate_positive_integer(
            profile["patience"],
            f"{profile_name}.patience",
        )

        dropout = profile["dropout"]

        if not isinstance(dropout, (int, float)):
            raise ValueError(
                f"{profile_name}.dropout must be numeric."
            )

        if not 0.0 <= dropout < 1.0:
            raise ValueError(
                f"{profile_name}.dropout must be >= 0 and < 1."
            )

    for tuning_name, tuning_config in tuning.items():

        if not isinstance(tuning_config, dict):
            raise ValueError(
                f"Tuning profile '{tuning_name}' "
                "must be a mapping."
            )

        required_tuning_keys = {
            "max_concurrent_trials",
            "max_t",
            "grace_period",
            "reduction_factor",
            "trials",
        }

        missing_keys = (
            required_tuning_keys - set(tuning_config.keys())
        )

        if missing_keys:
            raise ValueError(
                f"Tuning profile '{tuning_name}' "
                f"is missing keys: {sorted(missing_keys)}"
            )

        trials = tuning_config["trials"]

        if not isinstance(trials, list) or not trials:
            raise ValueError(
                f"Tuning profile '{tuning_name}' "
                "must contain at least one trial."
            )

        for index, trial in enumerate(trials):

            if not isinstance(trial, dict):
                raise ValueError(
                    f"Trial {index} in '{tuning_name}' "
                    "must be a mapping."
                )

            required_trial_keys = {
                "learning_rate",
                "embedding_dim",
                "dropout",
            }

            missing_trial_keys = (
                required_trial_keys - set(trial.keys())
            )

            if missing_trial_keys:
                raise ValueError(
                    f"Trial {index} in '{tuning_name}' "
                    f"is missing keys: "
                    f"{sorted(missing_trial_keys)}"
                )


def _validate_positive_integer(
    value: Any,
    name: str,
) -> None:
    """Validate a positive integer configuration value."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{name} must be a positive integer."
        )

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )


def _validate_positive_number(
    value: Any,
    name: str,
) -> None:
    """Validate a positive numeric configuration value."""

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ValueError(
            f"{name} must be a positive number."
        )

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )


def get_training_profile(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """Return one validated training profile."""

    profiles = config["deep_learning"]["profiles"]

    if profile_name not in profiles:
        raise ValueError(
            f"Unknown deep-learning profile: {profile_name}. "
            f"Available profiles: {sorted(profiles)}"
        )

    defaults = config["deep_learning"]["defaults"]
    profile = profiles[profile_name]

    return {
        **defaults,
        **profile,
    }


def get_tuning_profile(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """Return one validated Ray Tune profile."""

    tuning = config["deep_learning"]["tuning"]

    if profile_name not in tuning:
        raise ValueError(
            f"Unknown Ray Tune profile: {profile_name}. "
            f"Available profiles: {sorted(tuning)}"
        )

    return tuning[profile_name]


if __name__ == "__main__":

    config = load_deep_learning_config()

    print()
    print("=" * 70)
    print("SupportSense Deep-Learning Configuration")
    print("=" * 70)

    print(
        "Training profiles:",
        sorted(config["deep_learning"]["profiles"]),
    )

    print(
        "Tuning profiles   :",
        sorted(config["deep_learning"]["tuning"]),
    )

    smoke = get_training_profile(
        config,
        "smoke",
    )

    print()
    print("Smoke profile:")
    for key, value in smoke.items():
        print(f"  {key}: {value}")

    smoke_tuning = get_tuning_profile(
        config,
        "smoke",
    )

    print()
    print(
        "Smoke tuning trials:",
        len(smoke_tuning["trials"]),
    )

    print()
    print("PASS: Deep-learning configuration is valid.")
