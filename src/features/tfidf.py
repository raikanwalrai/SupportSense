from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


DEFAULT_NGRAM_RANGE = (1, 2)
DEFAULT_MIN_DF = 2
DEFAULT_MAX_DF = 0.95
DEFAULT_SUBLINEAR_TF = True


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


def create_tfidf_vectorizer() -> TfidfVectorizer:
    """Create the standard SupportSense TF-IDF vectorizer."""

    return TfidfVectorizer(
        lowercase=True,
        ngram_range=DEFAULT_NGRAM_RANGE,
        min_df=DEFAULT_MIN_DF,
        max_df=DEFAULT_MAX_DF,
        sublinear_tf=DEFAULT_SUBLINEAR_TF,
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
