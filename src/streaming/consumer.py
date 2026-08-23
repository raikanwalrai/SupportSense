from __future__ import annotations

import argparse

from kafka import KafkaConsumer

from src.streaming.schema import TicketEvent


DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
DEFAULT_TOPIC = "supportsense.tickets"
DEFAULT_GROUP_ID = "supportsense-consumer"


def create_consumer(
    bootstrap_servers: str,
    topic: str,
    group_id: str,
) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: value.decode("utf-8"),
    )


def consume_tickets(
    consumer: KafkaConsumer,
    max_messages: int,
) -> list[TicketEvent]:
    events: list[TicketEvent] = []

    for message in consumer:
        try:
            event = TicketEvent.from_json(message.value)
        except (ValueError, TypeError) as exc:
            print(
                "===== INVALID KAFKA EVENT ====="
            )
            print(f"Topic     : {message.topic}")
            print(f"Partition : {message.partition}")
            print(f"Offset    : {message.offset}")
            print(f"Error     : {exc}")
            continue

        events.append(event)

        print("===== KAFKA EVENT RECEIVED =====")
        print(f"Event ID  : {event.event_id}")
        print(f"Timestamp : {event.timestamp}")
        print(f"Ticket    : {event.ticket}")
        print(f"Source    : {event.source}")
        print(f"Topic     : {message.topic}")
        print(f"Partition : {message.partition}")
        print(f"Offset    : {message.offset}")

        if len(events) >= max_messages:
            break

    if events:
        consumer.commit()

    return events


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consume SupportSense ticket events from Kafka."
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

    parser.add_argument(
        "--group-id",
        default=DEFAULT_GROUP_ID,
        help="Kafka consumer group ID.",
    )

    parser.add_argument(
        "--max-messages",
        type=int,
        default=1,
        help="Maximum number of valid events to consume.",
    )

    args = parser.parse_args()

    if args.max_messages < 1:
        parser.error("--max-messages must be >= 1")

    consumer = create_consumer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        group_id=args.group_id,
    )

    try:
        consume_tickets(
            consumer=consumer,
            max_messages=args.max_messages,
        )
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
