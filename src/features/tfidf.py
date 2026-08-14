from pathlib import Path
from typing import Any

from src.config.experiment_config import (    
	load_experiment_config,    
	validate_experiment_config,
)

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def load_split(path: str | Path) -> pd.DataFrame:
    """Load a processed text classification split."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    required_columns = {"text", "category"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError(f"Dataset is empty: {path}")

    return df

def create_tfidf_vectorizer(
    config: dict[str, Any] | None = None,
) -> TfidfVectorizer:
    """Create the SupportSense TF-IDF vectorizer."""

    if config is None:
        config = load_experiment_config(
            "configs/experiments.yaml"
        )

    validate_experiment_config(config)

    feature_config = config["features"]

    if feature_config["type"] != "tfidf":
        raise ValueError(
            "Feature configuration must specify 'tfidf'."
        )

    return TfidfVectorizer(
        lowercase=True,
        ngram_range=tuple(feature_config["ngram_range"]),
        min_df=feature_config["min_df"],
        max_df=feature_config["max_df"],
        sublinear_tf=feature_config["sublinear_tf"],
    )


















def fit_tfidf(
    vectorizer: TfidfVectorizer,
    texts: pd.Series,
):
    """Fit TF-IDF using training text and return transformed features."""

    return vectorizer.fit_transform(texts)


def transform_tfidf(
    vectorizer: TfidfVectorizer,
    texts: pd.Series,
):
    """Transform text using an already-fitted TF-IDF vectorizer."""

    return vectorizer.transform(texts)


if __name__ == "__main__":
    train_path = "data/processed/train.csv"

    train_df = load_split(train_path)

    vectorizer = create_tfidf_vectorizer()

    X_train = fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    print()
    print("=" * 70)
    print("SupportSense TF-IDF Feature Analysis")
    print("=" * 70)

    print(f"Training records : {X_train.shape[0]}")
    print(f"TF-IDF features  : {X_train.shape[1]}")
    print(f"Matrix shape     : {X_train.shape}")
    print(f"Non-zero values  : {X_train.nnz}")
