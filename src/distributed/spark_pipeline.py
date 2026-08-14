from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
)


SUPPORTSENSE_SCHEMA = StructType(
    [
        StructField("text", StringType(), True),
        StructField("category", StringType(), True),
    ]
)


DEFAULT_TRAIN_PATH = "data/processed/train.csv"


def create_spark_session() -> SparkSession:
    """Create the local Spark session for SupportSense."""

    return (
        SparkSession.builder
        .master("local[2]")
        .appName("SupportSense-Spark")
        .getOrCreate()
    )


def load_training_data(
    spark: SparkSession,
    path: str | Path = DEFAULT_TRAIN_PATH,
):
    """Load the SupportSense training dataset."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {path}"
        )

    return (
             spark.read
             .option("header", True)
             .option("multiLine", True)
             .option("quote", '"')
             .option("escape", '"')
             .schema(SUPPORTSENSE_SCHEMA)
            .csv(str(path))
     )

def profile_spark_data(df) -> dict:
    """Return basic distributed dataset statistics."""

    statistics = df.agg(
        F.count("*").alias("rows"),
        F.sum(
            F.when(F.col("text").isNull(), 1).otherwise(0)
        ).alias("null_text"),
        F.sum(
            F.when(F.col("category").isNull(), 1).otherwise(0)
        ).alias("null_category"),
        F.min("text_length").alias("text_length_min"),
        F.max("text_length").alias("text_length_max"),
        F.avg("text_length").alias("text_length_mean"),
    ).collect()[0]

    return {
        "rows": statistics["rows"],
        "columns": len(df.columns),
        "categories": df.select("category").distinct().count(),
        "null_text": statistics["null_text"],
        "null_category": statistics["null_category"],
        "text_length_min": statistics["text_length_min"],
        "text_length_max": statistics["text_length_max"],
        "text_length_mean": statistics["text_length_mean"],
    }


def add_text_length_feature(df):
    """Add a simple text-length feature."""

    return df.withColumn(
        "text_length",
        F.length(F.col("text")),
    )

def category_distribution(df):
    """Return the number of records per support category."""

    return (
        df
        .groupBy("category")
        .count()
        .orderBy("category")
    )

def run_spark_pipeline(
    path: str | Path = DEFAULT_TRAIN_PATH,
) -> dict:

    spark = create_spark_session()

    try:
        df = load_training_data(spark, path)

        df = add_text_length_feature(df)

        profile = profile_spark_data(df)

        return {
            "dataframe": df,
            "profile": profile,
            "schema": df.schema,
        }

    finally:
        spark.stop()


if __name__ == "__main__":
    result = run_spark_pipeline()

    print()
    print("=" * 70)
    print("SupportSense Spark Pipeline")
    print("=" * 70)

    print()
    print("## Dataset")

    print(f"Rows       : {result['profile']['rows']}")
    print(f"Columns    : {result['profile']['columns']}")
    print(f"Categories : {result['profile']['categories']}")

    print()
    print("## Schema")

    result["schema"].simpleString()
    print(result["schema"].simpleString())
