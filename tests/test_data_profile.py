from pathlib import Path

from src.data.profile import profile_dataset


TRAIN_PATH = Path("data/raw/train.csv")
TEST_PATH = Path("data/raw/test.csv")


def test_train_profile_basic_statistics():
    profile = profile_dataset(TRAIN_PATH)

    assert profile["records"] == 10003
    assert profile["intent_count"] == 77
    assert profile["null_text"] == 0
    assert profile["null_category"] == 0
    assert profile["duplicate_rows"] == 0
    assert profile["duplicate_texts"] == 0


def test_test_profile_basic_statistics():
    profile = profile_dataset(TEST_PATH)

    assert profile["records"] == 3080
    assert profile["intent_count"] == 77
    assert profile["null_text"] == 0
    assert profile["null_category"] == 0
    assert profile["duplicate_rows"] == 0
    assert profile["duplicate_texts"] == 0


def test_train_text_statistics():
    profile = profile_dataset(TRAIN_PATH)

    assert profile["text_length"]["min"] == 13
    assert profile["text_length"]["max"] == 433
    assert profile["word_count"]["min"] == 2
    assert profile["word_count"]["max"] == 79


def test_train_intent_distribution():
    profile = profile_dataset(TRAIN_PATH)

    assert profile["intent_distribution"]["min"] == 35
    assert profile["intent_distribution"]["max"] == 187


def test_test_intent_distribution_is_balanced():
    profile = profile_dataset(TEST_PATH)

    assert profile["intent_distribution"]["min"] == 40
    assert profile["intent_distribution"]["max"] == 40
    assert profile["intent_distribution"]["mean"] == 40
    assert profile["intent_distribution"]["median"] == 40


def test_missing_dataset_raises_error():
    missing_path = Path("data/raw/does_not_exist.csv")

    try:
        profile_dataset(missing_path)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")
