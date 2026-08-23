from __future__ import annotations

import argparse
import time

from kafka import KafkaProducer

from src.streaming.schema import TicketEvent


DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
DEFAULT_TOPIC = "supportsense.tickets"


def create_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: value.encode("utf-8"),
        acks="all",
        retries=5,
    )


def publish_ticket(
    producer: KafkaProducer,
    topic: str,
    ticket: str,
    source: str = "customer",
) -> TicketEvent:
    event = TicketEvent.create(
        ticket=ticket,
        source=source,
    )

    future = producer.send(
        topic,
        value=event.to_json(),
    )

    metadata = future.get(timeout=10)

    print("===== KAFKA EVENT PUBLISHED =====")
    print(f"Event ID : {event.event_id}")
    print(f"Timestamp: {event.timestamp}")
    print(f"Ticket   : {event.ticket}")
    print(f"Source   : {event.source}")
    print(f"Topic    : {metadata.topic}")
    print(f"Partition: {metadata.partition}")
    print(f"Offset   : {metadata.offset}")

    return event


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish SupportSense ticket events to Kafka."
    )

    parser.add_argument(
        "--ticket",
        required=True,
        help="Customer ticket text.",
    )

    parser.add_argument(
        "--source",
        default="customer",
        help="Ticket source.",
    )

    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help="Kafka topic.",
    )

    parser.add_argument(
        "--bootstrap-servers",
        default=DEFAULT_BOOTSTRAP_SERVERS,
        help="Kafka bootstrap servers.",
    )

    args = parser.parse_args()

    producer = create_producer(args.bootstrap_servers)

    try:
        publish_ticket(
            producer=producer,
            topic=args.topic,
            ticket=args.ticket,
            source=args.source,
        )

        producer.flush()

    finally:
        producer.close()


if __name__ == "__main__":
    main()
