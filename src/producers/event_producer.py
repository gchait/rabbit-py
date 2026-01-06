"""Producer for publishing events to RabbitMQ."""

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src import config
from src.models import OrderEvent


def publish_event(channel: BlockingChannel, event: OrderEvent) -> None:
    """
    Publish an event to all subscribers via fanout exchange.

    This demonstrates:
    - Fanout exchange broadcasting to all bound queues
    - Event-driven architecture pattern
    - No routing key needed (fanout ignores it)

    Args:
        channel: RabbitMQ channel to publish on.
        event: The event to publish.
    """
    properties = pika.BasicProperties(
        delivery_mode=2,
        content_type="application/json",
    )

    channel.basic_publish(
        exchange=config.EXCHANGE_EVENTS,
        routing_key="",  # Fanout exchange ignores routing key
        body=event.to_json(),
        properties=properties,
    )

    print(f"📢 Broadcasted event: {event.event_type.value} for order {event.order_id}")


def publish_log(
    channel: BlockingChannel, event: OrderEvent, order_type_str: str
) -> None:
    """
    Publish a log message to the topic exchange.

    This demonstrates:
    - Topic exchange with hierarchical routing keys
    - Pattern-based message routing

    Args:
        channel: RabbitMQ channel to publish on.
        event: The event to log.
        order_type_str: Order type for routing key construction.
    """
    # Build hierarchical routing key: order.{event}.{type}
    routing_key = f"{event.event_type.value}.{order_type_str}"

    properties = pika.BasicProperties(
        delivery_mode=2,
        content_type="application/json",
    )

    channel.basic_publish(
        exchange=config.EXCHANGE_LOGS,
        routing_key=routing_key,
        body=event.to_json(),
        properties=properties,
    )

    print(f"📝 Logged event with routing key: {routing_key}")
