from pathlib import Path

import pytest

from src.distributed.spark_pipeline import (
    SUPPORTSENSE_SCHEMA,
    add_text_length_feature,
    category_distribution,
    create_spark_session,
    load_training_data,
    profile_spark_data,
)


TRAIN_PATH = Path("data/processed/train.csv")


@pytest.fixture(scope="module")
def spark():
    session = create_spark_session()
    yield session
    session.stop()


@pytest.fixture(scope="module")
def train_df(spark):
    return load_training_data(spark, TRAIN_PATH)


def test_spark_session_is_created(spark):
    assert spark.version.startswith("4.")


def test_training_data_is_loaded(spark, train_df):
    assert train_df.count() == 8002
    assert train_df.columns == ["text", "category"]


def test_training_data_has_expected_schema(train_df):
    assert train_df.schema == SUPPORTSENSE_SCHEMA


def test_training_data_has_expected_categories(train_df):
    assert train_df.select("category").distinct().count() == 77


def test_text_length_feature_is_added(train_df):
    result = add_text_length_feature(train_df)

    assert "text_length" in result.columns
    assert result.select("text_length").count() == 8002


def test_spark_profile_returns_basic_statistics(train_df):
    result = add_text_length_feature(train_df)

    profile = profile_spark_data(result)

    assert profile["rows"] == 8002
    assert profile["columns"] == 3
    assert profile["categories"] == 77


def test_missing_training_dataset_raises_error(spark):
    missing_path = Path("data/processed/does_not_exist.csv")

    with pytest.raises(FileNotFoundError):
        load_training_data(spark, missing_path)

def test_spark_profile_contains_data_quality_statistics(train_df):
    result = add_text_length_feature(train_df)

    profile = profile_spark_data(result)

    assert profile["null_text"] == 0
    assert profile["null_category"] == 0
    assert profile["text_length_min"] > 0
    assert profile["text_length_max"] >= profile["text_length_min"]
    assert profile["text_length_mean"] > 0

def test_spark_category_distribution_has_77_categories(train_df):
    result = add_text_length_feature(train_df)

    distribution = (
        result
        .groupBy("category")
        .count()
    )

    assert distribution.count() == 77
    assert distribution.select("count").filter("count <= 0").count() == 0

def test_category_distribution_returns_expected_counts(train_df):
    result = add_text_length_feature(train_df)

    distribution = category_distribution(result)

    assert distribution.count() == 77
    assert "category" in distribution.columns
    assert "count" in distribution.columns

    counts = [
        row["count"]
        for row in distribution.select("count").collect()
    ]

    assert min(counts) > 0
    assert max(counts) >= min(counts)
