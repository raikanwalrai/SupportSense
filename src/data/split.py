from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
VALIDATION_SIZE = 0.20

REQUIRED_COLUMNS = {"text", "category"}


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load and validate a text classification dataset."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError(f"Dataset is empty: {path}")

    return df


def create_train_validation_split(
    df: pd.DataFrame,
    validation_size: float = VALIDATION_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create a reproducible stratified train/validation split.

    The class distribution is preserved across both subsets.
    """

    if not 0 < validation_size < 1:
        raise ValueError(
            "validation_size must be between 0 and 1"
        )

    if df["category"].isna().any():
        raise ValueError("Cannot split data with missing categories")

    if df["category"].nunique() < 2:
        raise ValueError(
            "At least two intents are required for stratified splitting"
        )

    train_df, validation_df = train_test_split(
        df,
        test_size=validation_size,
        random_state=random_state,
        stratify=df["category"],
    )

    train_df = train_df.reset_index(drop=True)
    validation_df = validation_df.reset_index(drop=True)

    return train_df, validation_df


def save_split(
    df: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Save a prepared dataset split as CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)


def prepare_train_validation(
    input_path: str | Path,
    train_output: str | Path,
    validation_output: str | Path,
    validation_size: float = VALIDATION_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create and save reproducible train and validation datasets."""

    df = load_dataset(input_path)

    train_df, validation_df = create_train_validation_split(
        df,
        validation_size=validation_size,
        random_state=random_state,
    )

    save_split(train_df, train_output)
    save_split(validation_df, validation_output)

    return train_df, validation_df


def print_summary(
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    validation_size: float,
    random_state: int,
) -> None:
    """Print a summary of the generated splits."""

    print()
    print("=" * 70)
    print("SupportSense Train/Validation Split")
    print("=" * 70)

    print(f"Random state    : {random_state}")
    print(f"Validation size : {validation_size:.0%}")

    print()
    print("## Records")

    print(f"Training        : {len(train_df)}")
    print(f"Validation      : {len(validation_df)}")

    print()
    print("## Intents")

    print(f"Training        : {train_df['category'].nunique()}")
    print(f"Validation      : {validation_df['category'].nunique()}")

    print()
    print("## Class distribution")

    train_counts = train_df["category"].value_counts()
    validation_counts = validation_df["category"].value_counts()

    comparison = pd.DataFrame(
        {
            "train": train_counts,
            "validation": validation_counts,
        }
    ).sort_index()

    print(comparison.to_string())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a stratified train/validation split."
    )

    parser.add_argument(
        "--input",
        default="data/raw/train.csv",
    )

    parser.add_argument(
        "--train-output",
        default="data/processed/train.csv",
    )

    parser.add_argument(
        "--validation-output",
        default="data/processed/validation.csv",
    )

    parser.add_argument(
        "--validation-size",
        type=float,
        default=VALIDATION_SIZE,
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=RANDOM_STATE,
    )

    args = parser.parse_args()

    train_df, validation_df = prepare_train_validation(
        input_path=args.input,
        train_output=args.train_output,
        validation_output=args.validation_output,
        validation_size=args.validation_size,
        random_state=args.random_state,
    )

    print_summary(
        train_df,
        validation_df,
        validation_size=args.validation_size,
        random_state=args.random_state,
    )
