"""Log consumer using topic exchange for pattern-based routing."""

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from src import config
from src.models import OrderEvent


def start_log_service(channel: BlockingChannel) -> None:
    """
    Start log service that receives logs via topic exchange.

    This demonstrates:
    - Topic exchange with hierarchical routing keys
    - Pattern-based message routing (order.#)
    - Flexible subscription patterns

    The routing key pattern follows: order.{event_type}.{order_type}
    Examples:
      - order.created.standard
      - order.processing.express
      - order.completed.international

    Args:
        channel: RabbitMQ channel to consume from.
    """
    print("📝 Log service started")
    print(f"   Listening to logs from {config.EXCHANGE_LOGS} with pattern 'order.#'")

    def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """
        Process a log message.

        Args:
            ch: Channel the message was received on.
            method: Delivery method containing routing info.
            properties: Message properties.
            body: Message body.
        """
        event = OrderEvent.from_json(body.decode())
        routing_key = method.routing_key

        # Parse routing key components
        parts = routing_key.split(".")
        order_type = parts[2] if len(parts) >= 3 else "unknown"

        print(f"   📝 Log [{routing_key}]: {event.message}")
        print(f"      Order: {event.order_id}, Type: {order_type}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=config.QUEUE_LOGS,
        on_message_callback=callback,
        auto_ack=False,
    )

    try:
        print("   [*] Waiting for logs. To exit press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n📝 Log service stopping...")
        channel.stop_consuming()
