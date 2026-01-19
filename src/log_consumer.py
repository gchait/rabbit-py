"""Log consumer using topic exchange."""

import json

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from . import config
from .connection import create_connection


def run_log_consumer() -> None:
    """
    Consume logs from topic exchange.

    Demonstrates pattern-based routing with wildcards.
    """
    connection = create_connection()
    channel = connection.channel()

    def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """Process incoming log messages."""
        log_data = json.loads(body)
        routing_key = method.routing_key

        print(f"[Log Service] [{routing_key}] {log_data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=config.QUEUE_LOGS,
        on_message_callback=callback,
        auto_ack=False,
    )

    print(f"[Log Service] Listening on queue: {config.QUEUE_LOGS}")
    print("[Log Service] Receiving logs matching pattern: order.#")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[Log Service] Shutting down...")
        channel.stop_consuming()
    finally:
        connection.close()
