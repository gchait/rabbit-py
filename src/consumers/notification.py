"""Notification consumer subscribing to order events via fanout exchange."""

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from .. import config
from ..models import OrderEvent


def start_notification_service(channel: BlockingChannel) -> None:
    """
    Start notification service that receives all order events.

    This demonstrates:
    - Fanout exchange pattern (pub/sub)
    - All subscribers receive all messages
    - Event-driven architecture for cross-cutting concerns

    Args:
        channel: RabbitMQ channel to consume from.
    """
    print("📧 Notification service started")
    print(f"   Listening to all events from {config.EXCHANGE_EVENTS}")

    def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """
        Process an event notification.

        Args:
            ch: Channel the message was received on.
            method: Delivery method containing routing info.
            properties: Message properties.
            body: Message body.
        """
        event = OrderEvent.from_json(body.decode())
        print(f"   📧 Notification: {event.event_type.value} - {event.message}")

        # In real system, would send email, SMS, push notification, etc.
        _send_notification(event)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=config.QUEUE_NOTIFICATIONS,
        on_message_callback=callback,
        auto_ack=False,
    )

    try:
        print("   [*] Waiting for events. To exit press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n📧 Notification service stopping...")
        channel.stop_consuming()


def _send_notification(event: OrderEvent) -> None:
    """
    Send notification to customer.

    In a real system, this would integrate with email/SMS services.

    Args:
        event: The event to send notification for.
    """
    # Simulate notification logic based on event type
    notification_messages = {
        "order.created": f"Your order {event.order_id} has been received!",
        "order.processing": f"Your order {event.order_id} is being processed.",
        "order.completed": f"Your order {event.order_id} is complete!",
        "order.failed": f"Issue with order {event.order_id}. Customer service will contact you.",
    }

    message = notification_messages.get(event.event_type.value, "Order status update")
    print(f"      → Sending to customer: '{message}'")
