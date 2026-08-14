import pandas as pd
import pytest

from src.data.validate import (
    validate_content,
    validate_duplicates,
    validate_intents,
)


def test_valid_content_passes():
    df = pd.DataFrame(
        {
            "text": ["I need help"],
            "category": ["card_arrival"],
        }
    )

    errors = validate_content(df, "Test")

    assert errors == []


def test_null_text_is_detected():
    df = pd.DataFrame(
        {
            "text": [None],
            "category": ["card_arrival"],
        }
    )

    errors = validate_content(df, "Test")

    assert any("null text" in error for error in errors)


def test_empty_text_is_detected():
    df = pd.DataFrame(
        {
            "text": ["   "],
            "category": ["card_arrival"],
        }
    )

    errors = validate_content(df, "Test")

    assert any("empty text" in error for error in errors)


def test_duplicate_rows_are_detected():
    df = pd.DataFrame(
        {
            "text": ["I need help", "I need help"],
            "category": ["card_arrival", "card_arrival"],
        }
    )

    errors = validate_duplicates(df, df.copy())

    assert any("duplicate" in error.lower() for error in errors)


def test_train_test_text_overlap_is_detected():
    train = pd.DataFrame(
        {
            "text": ["I need help"],
            "category": ["card_arrival"],
        }
    )

    test = pd.DataFrame(
        {
            "text": ["I need help"],
            "category": ["card_arrival"],
        }
    )

    errors = validate_duplicates(train, test)

    assert any("shared between train and test" in error for error in errors)


def test_matching_intent_vocabularies_pass():
    train = pd.DataFrame(
        {
            "text": ["a", "b"],
            "category": ["intent_a", "intent_b"],
        }
    )

    test = pd.DataFrame(
        {
            "text": ["c", "d"],
            "category": ["intent_a", "intent_b"],
        }
    )

    # This test uses only two classes, so temporarily override
    # the expected count inside the module.
    import src.data.validate as validator

    original_count = validator.EXPECTED_INTENT_COUNT
    validator.EXPECTED_INTENT_COUNT = 2

    try:
        errors = validate_intents(train, test)
        assert errors == []
    finally:
        validator.EXPECTED_INTENT_COUNT = original_count
