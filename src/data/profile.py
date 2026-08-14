from pathlib import Path

import pandas as pd


def profile_dataset(path: str | Path) -> dict:
    """
    Generate a reusable statistical profile for a SupportSense dataset.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Dataset is empty: {path}")

    text_lengths = df["text"].fillna("").str.len()
    word_counts = (
        df["text"]
        .fillna("")
        .str.split()
        .str.len()
    )

    intent_counts = df["category"].value_counts()

    profile = {
        "file": str(path),
        "records": len(df),
        "columns": list(df.columns),
        "intent_count": df["category"].nunique(),
        "null_text": int(df["text"].isna().sum()),
        "null_category": int(df["category"].isna().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_texts": int(df["text"].duplicated().sum()),
        "text_length": {
            "min": int(text_lengths.min()),
            "max": int(text_lengths.max()),
            "mean": float(text_lengths.mean()),
            "median": float(text_lengths.median()),
        },
        "word_count": {
            "min": int(word_counts.min()),
            "max": int(word_counts.max()),
            "mean": float(word_counts.mean()),
            "median": float(word_counts.median()),
        },
        "intent_distribution": {
            "min": int(intent_counts.min()),
            "max": int(intent_counts.max()),
            "mean": float(intent_counts.mean()),
            "median": float(intent_counts.median()),
        },
    }

    return profile


def print_profile(profile: dict) -> None:
    """Print a human-readable dataset profile."""

    print("=" * 60)
    print("SupportSense Dataset Profile")
    print("=" * 60)

    print(f"File          : {profile['file']}")
    print(f"Records       : {profile['records']}")
    print(f"Columns       : {profile['columns']}")
    print(f"Intent count  : {profile['intent_count']}")

    print("\nData quality")
    print("-" * 60)
    print(f"Null text     : {profile['null_text']}")
    print(f"Null category : {profile['null_category']}")
    print(f"Duplicate rows: {profile['duplicate_rows']}")
    print(f"Duplicate text: {profile['duplicate_texts']}")

    print("\nText length")
    print("-" * 60)
    for key, value in profile["text_length"].items():
        print(f"{key:10s}: {value:.2f}" if isinstance(value, float) else f"{key:10s}: {value}")

    print("\nWord count")
    print("-" * 60)
    for key, value in profile["word_count"].items():
        print(f"{key:10s}: {value:.2f}" if isinstance(value, float) else f"{key:10s}: {value}")

    print("\nIntent distribution")
    print("-" * 60)
    for key, value in profile["intent_distribution"].items():
        print(f"{key:10s}: {value:.2f}" if isinstance(value, float) else f"{key:10s}: {value}")


if __name__ == "__main__":
    train_profile = profile_dataset("data/raw/train.csv")
    test_profile = profile_dataset("data/raw/test.csv")

    print("\nTRAIN")
    print_profile(train_profile)

    print("\nTEST")
    print_profile(test_profile)
