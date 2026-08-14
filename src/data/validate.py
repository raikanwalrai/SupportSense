from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"text", "category"}
EXPECTED_INTENT_COUNT = 77


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a CSV dataset and perform basic structural validation."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Dataset is empty: {path}")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns in {path}: "
            f"{sorted(missing_columns)}"
        )

    return df


def validate_content(df: pd.DataFrame, name: str) -> list[str]:
    """Validate ticket text and intent content."""
    errors = []

    null_text = int(df["text"].isna().sum())
    null_category = int(df["category"].isna().sum())

    if null_text:
        errors.append(f"{name}: {null_text} null text values")

    if null_category:
        errors.append(f"{name}: {null_category} null category values")

    empty_text = int(
        df["text"].fillna("").astype(str).str.strip().eq("").sum()
    )

    if empty_text:
        errors.append(f"{name}: {empty_text} empty text values")

    return errors


def validate_intents(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> list[str]:
    """Validate the intent vocabulary across train and test."""
    errors = []

    train_labels = set(train["category"].dropna())
    test_labels = set(test["category"].dropna())

    if len(train_labels) != EXPECTED_INTENT_COUNT:
        errors.append(
            f"Train contains {len(train_labels)} intents; "
            f"expected {EXPECTED_INTENT_COUNT}"
        )

    if len(test_labels) != EXPECTED_INTENT_COUNT:
        errors.append(
            f"Test contains {len(test_labels)} intents; "
            f"expected {EXPECTED_INTENT_COUNT}"
        )

    only_train = train_labels - test_labels
    only_test = test_labels - train_labels

    if only_train:
        errors.append(
            f"Intents present only in train: {sorted(only_train)}"
        )

    if only_test:
        errors.append(
            f"Intents present only in test: {sorted(only_test)}"
        )

    return errors


def validate_duplicates(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> list[str]:
    """Validate duplicate and train/test leakage conditions."""
    errors = []

    train_duplicates = int(train.duplicated().sum())
    test_duplicates = int(test.duplicated().sum())

    if train_duplicates:
        errors.append(
            f"Train contains {train_duplicates} exact duplicate rows"
        )

    if test_duplicates:
        errors.append(
            f"Test contains {test_duplicates} exact duplicate rows"
        )

    train_text_duplicates = int(train["text"].duplicated().sum())
    test_text_duplicates = int(test["text"].duplicated().sum())

    if train_text_duplicates:
        errors.append(
            f"Train contains {train_text_duplicates} duplicate texts"
        )

    if test_text_duplicates:
        errors.append(
            f"Test contains {test_text_duplicates} duplicate texts"
        )

    overlap = set(train["text"]) & set(test["text"])

    if overlap:
        errors.append(
            f"Found {len(overlap)} text values shared between train and test"
        )

    return errors


def validate_datasets(
    train_path: str | Path,
    test_path: str | Path,
) -> None:
    """Run all Sprint 1 data-quality checks."""
    train = load_dataset(train_path)
    test = load_dataset(test_path)

    errors = []

    errors.extend(validate_content(train, "Train"))
    errors.extend(validate_content(test, "Test"))
    errors.extend(validate_intents(train, test))
    errors.extend(validate_duplicates(train, test))

    if errors:
        print("SupportSense Data Validation")
        print("=" * 40)
        print("VALIDATION FAILED")
        print()

        for error in errors:
            print(f"- {error}")

        raise ValueError(
            f"Data validation failed with {len(errors)} error(s)."
        )

    print("SupportSense Data Validation")
    print("=" * 40)
    print(f"Train records : {len(train)}")
    print(f"Test records  : {len(test)}")
    print(f"Intent count  : {train['category'].nunique()}")
    print()
    print("Content validation       : PASSED")
    print("Intent vocabulary        : PASSED")
    print("Duplicate validation     : PASSED")
    print("Train/test leakage check : PASSED")
    print()
    print("DATA VALIDATION: PASSED")


if __name__ == "__main__":
    validate_datasets(
        "data/raw/train.csv",
        "data/raw/test.csv",
    )
