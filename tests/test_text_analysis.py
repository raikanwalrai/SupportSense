from pathlib import Path

import pandas as pd
import pytest

from src.data.text_analysis import (
    analyze_dataset,
    intent_statistics,
    load_dataset,
    tokenize,
    vocabulary_statistics,
)


TRAIN_PATH = Path("data/raw/train.csv")


def test_tokenize():
    tokens = tokenize("I need help with my card")

    assert tokens == [
        "i",
        "need",
        "help",
        "with",
        "my",
        "card",
    ]


def test_load_dataset():
    df = load_dataset(TRAIN_PATH)

    assert len(df) == 10003
    assert list(df.columns) == ["text", "category"]


def test_vocabulary_statistics():
    df = load_dataset(TRAIN_PATH)

    stats = vocabulary_statistics(df)

    assert stats["total_tokens"] > 0
    assert stats["unique_tokens"] > 0
    assert len(stats["top_words"]) == 20


def test_intent_statistics():
    df = load_dataset(TRAIN_PATH)

    stats = intent_statistics(df)

    assert len(stats) == 77
    assert stats["card_arrival"]["records"] == 153


def test_analyze_dataset():
    result = analyze_dataset(TRAIN_PATH)

    assert result["records"] == 10003
    assert result["intent_count"] == 77
    assert "vocabulary" in result
    assert "intent_statistics" in result
    assert "examples" in result


def test_missing_dataset():
    with pytest.raises(FileNotFoundError):
        load_dataset("data/raw/does_not_exist.csv")
