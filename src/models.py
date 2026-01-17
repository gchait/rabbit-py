"""Data models for orders and events."""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class OrderType(str, Enum):
    """Types of orders that can be processed."""

    STANDARD = "standard"
    EXPRESS = "express"
    INTERNATIONAL = "international"


class EventType(str, Enum):
    """Types of events that can occur."""

    ORDER_CREATED = "order.created"
    ORDER_PROCESSING = "order.processing"
    ORDER_COMPLETED = "order.completed"
    ORDER_FAILED = "order.failed"


@dataclass
class Order:
    """Represents a customer order."""

    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    order_type: OrderType

    def to_json(self) -> str:
        """
        Serialize the order to JSON string.

        Returns:
            JSON string representation of the order.
        """
        data = asdict(self)
        data["order_type"] = self.order_type.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "Order":
        """
        Deserialize an order from JSON string.

        Args:
            json_str: JSON string containing order data.

        Returns:
            An Order instance.
        """
        data = json.loads(json_str)
        data["order_type"] = OrderType(data["order_type"])
        return cls(**data)


@dataclass
class OrderEvent:
    """Represents an event related to an order."""

    event_type: EventType
    order_id: str
    message: str
    metadata: dict[str, Any] | None = None

    def to_json(self) -> str:
        """
        Serialize the event to JSON string.

        Returns:
            JSON string representation of the event.
        """
        data = asdict(self)
        data["event_type"] = self.event_type.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "OrderEvent":
        """
        Deserialize an event from JSON string.

        Args:
            json_str: JSON string containing event data.

        Returns:
            An OrderEvent instance.
        """
        data = json.loads(json_str)
        data["event_type"] = EventType(data["event_type"])
        return cls(**data)
