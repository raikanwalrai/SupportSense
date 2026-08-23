from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TicketEvent:
    """Canonical event received from the SupportSense ticket stream."""

    event_id: str
    timestamp: str
    ticket: str
    source: str = "customer"

    @classmethod
    def create(
        cls,
        ticket: str,
        source: str = "customer",
    ) -> "TicketEvent":
        """Create a new ticket event with a unique ID and UTC timestamp."""
        ticket = ticket.strip()

        if not ticket:
            raise ValueError("ticket must not be empty")

        if not source.strip():
            raise ValueError("source must not be empty")

        return cls(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            ticket=ticket,
            source=source.strip(),
        )

    def to_dict(self) -> dict[str, str]:
        """Return the event as a JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the event as JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> "TicketEvent":
        """Validate and construct an event from a dictionary."""
        required = {"event_id", "timestamp", "ticket", "source"}

        missing = required - payload.keys()
        if missing:
            raise ValueError(
                f"Missing required event fields: {sorted(missing)}"
            )

        event_id = payload["event_id"]
        ticket = payload["ticket"]
        timestamp = payload["timestamp"]
        source = payload["source"]

        try:
            UUID(event_id)
        except (ValueError, TypeError, AttributeError):
            raise ValueError("event_id must be a valid UUID") from None

        if not isinstance(ticket, str) or not ticket.strip():
            raise ValueError("ticket must not be empty")

        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must not be empty")

        if not isinstance(timestamp, str) or not timestamp.strip():
            raise ValueError("timestamp must not be empty")

        return cls(
            event_id=event_id,
            timestamp=timestamp,
            ticket=ticket.strip(),
            source=source.strip(),
        )

    @classmethod
    def from_json(cls, payload: str) -> "TicketEvent":
        """Deserialize and validate a JSON event."""
        data = json.loads(payload)

        if not isinstance(data, dict):
            raise ValueError("event JSON must contain an object")

        return cls.from_dict(data)
