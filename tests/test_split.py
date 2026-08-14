from pathlib import Path

import pandas as pd
import pytest

from src.data.split import (
    RANDOM_STATE,
    VALIDATION_SIZE,
    create_train_validation_split,
    load_dataset,
)


TRAIN_PATH = Path("data/raw/train.csv")


def test_split_preserves_all_intents():
    df = load_dataset(TRAIN_PATH)

    train_df, validation_df = create_train_validation_split(df)

    assert train_df["category"].nunique() == 77
    assert validation_df["category"].nunique() == 77


def test_split_has_expected_record_counts():
    df = load_dataset(TRAIN_PATH)

    train_df, validation_df = create_train_validation_split(df)

    assert len(train_df) == 8002
    assert len(validation_df) == 2001
    assert len(train_df) + len(validation_df) == len(df)


def test_split_contains_no_duplicate_rows():
    df = load_dataset(TRAIN_PATH)

    train_df, validation_df = create_train_validation_split(df)

    assert train_df.duplicated().sum() == 0
    assert validation_df.duplicated().sum() == 0


def test_train_and_validation_have_no_text_overlap():
    df = load_dataset(TRAIN_PATH)

    train_df, validation_df = create_train_validation_split(df)

    train_text = set(train_df["text"])
    validation_text = set(validation_df["text"])

    assert train_text.isdisjoint(validation_text)


def test_split_is_reproducible():
    df = load_dataset(TRAIN_PATH)

    train_a, validation_a = create_train_validation_split(
        df,
        random_state=RANDOM_STATE,
    )

    train_b, validation_b = create_train_validation_split(
        df,
        random_state=RANDOM_STATE,
    )

    pd.testing.assert_frame_equal(train_a, train_b)
    pd.testing.assert_frame_equal(validation_a, validation_b)


def test_split_is_stratified():
    df = load_dataset(TRAIN_PATH)

    train_df, validation_df = create_train_validation_split(
        df,
        validation_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
    )

    train_counts = train_df["category"].value_counts()
    validation_counts = validation_df["category"].value_counts()

    assert set(train_counts.index) == set(validation_counts.index)

    for intent in train_counts.index:
        total = train_counts[intent] + validation_counts[intent]

        validation_ratio = validation_counts[intent] / total

        assert abs(validation_ratio - VALIDATION_SIZE) <= 0.05


def test_missing_dataset_raises_error():
    with pytest.raises(FileNotFoundError):
        load_dataset("data/raw/does_not_exist.csv")
