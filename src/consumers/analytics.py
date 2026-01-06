"""Analytics consumer subscribing to order events via fanout exchange."""

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from .. import config
from ..models import OrderEvent


def start_analytics_service(channel: BlockingChannel) -> None:
    """
    Start analytics service that receives all order events.

    This demonstrates:
    - Fanout exchange pattern (pub/sub)
    - Multiple independent subscribers receiving same messages
    - Decoupled services for different concerns (notification vs analytics)

    Args:
        channel: RabbitMQ channel to consume from.
    """
    print("📊 Analytics service started")
    print(f"   Listening to all events from {config.EXCHANGE_EVENTS}")

    def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """
        Process an event for analytics.

        Args:
            ch: Channel the message was received on.
            method: Delivery method containing routing info.
            properties: Message properties.
            body: Message body.
        """
        event = OrderEvent.from_json(body.decode())
        print(
            f"   📊 Analytics: Recording {event.event_type.value} for order {event.order_id}"
        )

        # In real system, would write to data warehouse, update dashboards, etc.
        _record_metric(event)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=config.QUEUE_ANALYTICS,
        on_message_callback=callback,
        auto_ack=False,
    )

    try:
        print("   [*] Waiting for events. To exit press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n📊 Analytics service stopping...")
        channel.stop_consuming()


def _record_metric(event: OrderEvent) -> None:
    """
    Record analytics metric.

    In a real system, this would push to time-series DB, data warehouse, etc.

    Args:
        event: The event to record.
    """
    # Simulate analytics recording
    if event.metadata and "processing_time" in event.metadata:
        processing_time = event.metadata["processing_time"]
        print(f"      → Metric: Order processing time = {processing_time:.2f}s")
    elif event.metadata and "worker_id" in event.metadata:
        worker_id = event.metadata["worker_id"]
        print(f"      → Metric: Event from worker {worker_id}")
    else:
        print(f"      → Metric: Event count for {event.event_type.value}")
