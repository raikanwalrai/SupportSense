from pathlib import Path

import pandas as pd
import pytest

from src.features.tfidf import (
    create_tfidf_vectorizer,
    fit_tfidf,
    load_split,
    transform_tfidf,
)


TRAIN_PATH = Path("data/processed/train.csv")
VALIDATION_PATH = Path("data/processed/validation.csv")


def test_load_split():
    df = load_split(TRAIN_PATH)

    assert len(df) == 8002
    assert set(df.columns) == {"text", "category"}


def test_missing_split_raises_error():
    with pytest.raises(FileNotFoundError):
        load_split("data/processed/does_not_exist.csv")


def test_tfidf_vectorizer_configuration():
    vectorizer = create_tfidf_vectorizer()

    assert vectorizer.lowercase is True
    assert vectorizer.ngram_range == (1, 2)
    assert vectorizer.min_df == 2
    assert vectorizer.max_df == 0.95
    assert vectorizer.sublinear_tf is True


def test_fit_tfidf_creates_features():
    df = load_split(TRAIN_PATH)

    vectorizer = create_tfidf_vectorizer()

    X_train = fit_tfidf(
        vectorizer,
        df["text"],
    )

    assert X_train.shape[0] == len(df)
    assert X_train.shape[1] > 0
    assert X_train.nnz > 0
    assert hasattr(vectorizer, "vocabulary_")


def test_transform_uses_fitted_vectorizer():
    train_df = load_split(TRAIN_PATH)
    validation_df = load_split(VALIDATION_PATH)

    vectorizer = create_tfidf_vectorizer()

    X_train = fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    X_validation = transform_tfidf(
        vectorizer,
        validation_df["text"],
    )

    assert X_train.shape[1] == X_validation.shape[1]
    assert X_validation.shape[0] == len(validation_df)
    assert X_validation.nnz > 0


def test_train_and_validation_share_same_feature_space():
    train_df = load_split(TRAIN_PATH)
    validation_df = load_split(VALIDATION_PATH)

    vectorizer = create_tfidf_vectorizer()

    fit_tfidf(
        vectorizer,
        train_df["text"],
    )

    X_validation = transform_tfidf(
        vectorizer,
        validation_df["text"],
    )

    assert X_validation.shape[1] == len(vectorizer.vocabulary_)

def test_tfidf_vectorizer_accepts_custom_configuration():
    config = {
        "experiment": {
            "name": "test_experiment",
            "random_state": 42,
            "primary_metric": "macro_f1",
        },
        "data": {
            "train_path": "data/processed/train.csv",
            "validation_path": "data/processed/validation.csv",
        },
        "features": {
            "type": "tfidf",
            "ngram_range": [1, 1],
            "min_df": 5,
            "max_df": 0.90,
            "sublinear_tf": False,
        },
        "model": {
            "type": "logistic_regression",
            "max_iter": 1000,
            "random_state": 42,
        },
    }

    vectorizer = create_tfidf_vectorizer(config)

    assert vectorizer.ngram_range == (1, 1)
    assert vectorizer.min_df == 5
    assert vectorizer.max_df == 0.90
    assert vectorizer.sublinear_tf is False
