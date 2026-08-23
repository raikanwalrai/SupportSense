from __future__ import annotations

import os
from typing import Any

import requests
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
DEFAULT_TOPIC = "supportsense.tickets"

DEFAULT_RUNNER_URL = os.getenv(
    "SUPPORTSENSE_RUNNER_URL",
    "http://127.0.0.1:8000",
)

DEFAULT_LOG_LEVEL = os.getenv(
    "SUPPORTSENSE_SPARK_LOG_LEVEL",
    "WARN",
).upper()


def create_spark_session() -> SparkSession:
    """Create the local Spark session for SupportSense streaming."""

    return (
        SparkSession.builder
        .master("local[2]")
        .appName("SupportSense-Kafka-Streaming")
        .config("spark.sql.shuffle.partitions", "2")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.2",
        )
        .getOrCreate()
    )


def read_kafka_stream(
    spark: SparkSession,
    bootstrap_servers: str = DEFAULT_BOOTSTRAP_SERVERS,
    topic: str = DEFAULT_TOPIC,
) -> DataFrame:
    """Create a Spark Structured Streaming DataFrame from Kafka."""

    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", bootstrap_servers)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )


def parse_ticket_events(df: DataFrame) -> DataFrame:
    """Parse SupportSense TicketEvent JSON from Kafka."""

    return (
        df.select(
            F.col("timestamp").alias("kafka_timestamp"),
            F.col("partition"),
            F.col("offset"),
            F.col("value").cast("string").alias("value"),
        )
        .select(
            "kafka_timestamp",
            "partition",
            "offset",
            F.get_json_object(
                "value",
                "$.event_id",
            ).alias("event_id"),
            F.get_json_object(
                "value",
                "$.timestamp",
            ).alias("event_timestamp"),
            F.get_json_object(
                "value",
                "$.ticket",
            ).alias("ticket"),
            F.get_json_object(
                "value",
                "$.source",
            ).alias("source"),
        )
    )


def predict_ticket(
    ticket: str,
    runner_url: str = DEFAULT_RUNNER_URL,
) -> dict[str, Any]:
    """Send one ticket to the existing SupportSense Runner."""

    response = requests.post(
        f"{runner_url.rstrip('/')}/predict",
        json={"ticket": ticket},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def process_batch(
    batch_df: DataFrame,
    batch_id: int,
    runner_url: str = DEFAULT_RUNNER_URL,
) -> None:
    """Forward each ticket in a Spark micro-batch to the Runner."""

    rows = (
        batch_df
        .select(
            "event_id",
            "event_timestamp",
            "ticket",
            "source",
            "partition",
            "offset",
        )
        .collect()
    )

    if not rows:
        return

    print()
    print("-" * 70)
    print(f" Spark batch: {batch_id}")
    print(f" Tickets received: {len(rows)}")
    print("-" * 70)

    for row in rows:
        try:
            result = predict_ticket(
                ticket=row["ticket"],
                runner_url=runner_url,
            )

            prediction = result.get("prediction")
            decision = result.get("decision", {})

            print(
                f"[SUCCESS] "
                f"event_id={row['event_id']} | "
                f"partition={row['partition']} | "
                f"offset={row['offset']} | "
                f"prediction={prediction} | "
                f"action={decision.get('action_id')} | "
                f"risk={decision.get('risk')}"
            )

        except Exception as exc:
            print(
                f"[ERROR] "
                f"event_id={row['event_id']} | "
                f"ticket={row['ticket']!r} | "
                f"{type(exc).__name__}: {exc}"
            )


def main() -> None:
    spark = create_spark_session()
    spark.sparkContext.setLogLevel(DEFAULT_LOG_LEVEL)

    try:
        kafka_stream = read_kafka_stream(spark)
        events = parse_ticket_events(kafka_stream)

        query = (
            events.writeStream
            .foreachBatch(
                lambda batch_df, batch_id: process_batch(
                    batch_df,
                    batch_id,
                    DEFAULT_RUNNER_URL,
                )
            )
            .option(
                "checkpointLocation",
                "/tmp/supportsense-kafka-runner-checkpoint",
            )
            .trigger(processingTime="5 seconds")
            .start()
        )

        print()
        print("=" * 70)
        print(" SupportSense: Kafka → Spark → Runner")
        print("=" * 70)
        print(f" Kafka       : {DEFAULT_BOOTSTRAP_SERVERS}")
        print(f" Topic       : {DEFAULT_TOPIC}")
        print(f" Runner      : {DEFAULT_RUNNER_URL}")
        print(f" Log level   : {DEFAULT_LOG_LEVEL}")
        print(" Waiting for NEW tickets...")
        print("=" * 70)
        print()

        query.awaitTermination()

    except KeyboardInterrupt:
        print()
        print("Stopping Spark streaming...")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
