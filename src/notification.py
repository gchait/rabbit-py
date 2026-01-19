"""Notification service using fanout exchange."""

import json

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from . import config
from .connection import create_connection


def run_notification_service() -> None:
    """
    Receive events from fanout exchange and send notifications.

    Demonstrates fanout pattern where multiple services receive the same event.
    """
    connection = create_connection()
    channel = connection.channel()

    def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """Process incoming events and send notifications."""
        event = json.loads(body)
        order_id = event.get("order_id", "unknown")
        status = event.get("status", "unknown")

        print(f"[Notification] Sending notification: Order {order_id} - {status}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=config.QUEUE_NOTIFICATIONS,
        on_message_callback=callback,
        auto_ack=False,
    )

    print(f"[Notification] Listening on queue: {config.QUEUE_NOTIFICATIONS}")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[Notification] Shutting down...")
        channel.stop_consuming()
    finally:
        connection.close()
