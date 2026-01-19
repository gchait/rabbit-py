"""RabbitMQ infrastructure setup."""

from pika.adapters.blocking_connection import BlockingChannel

from . import config


def setup_infrastructure(channel: BlockingChannel) -> None:
    """
    Declare all exchanges, queues, and bindings.

    Args:
        channel: RabbitMQ channel to use for declarations.
    """
    # Dead Letter Exchange and Queue
    channel.exchange_declare(
        exchange=config.EXCHANGE_DLX,
        exchange_type="fanout",
        durable=True,
    )
    channel.queue_declare(queue=config.QUEUE_DLQ, durable=True)
    channel.queue_bind(queue=config.QUEUE_DLQ, exchange=config.EXCHANGE_DLX)

    # Direct Exchange for orders
    channel.exchange_declare(
        exchange=config.EXCHANGE_ORDERS,
        exchange_type="direct",
        durable=True,
    )
    channel.queue_declare(
        queue=config.QUEUE_ORDERS,
        durable=True,
        arguments={"x-dead-letter-exchange": config.EXCHANGE_DLX},
    )
    channel.queue_bind(
        queue=config.QUEUE_ORDERS,
        exchange=config.EXCHANGE_ORDERS,
        routing_key="order",
    )

    # Fanout Exchange for events (broadcasts to multiple services)
    channel.exchange_declare(
        exchange=config.EXCHANGE_EVENTS,
        exchange_type="fanout",
        durable=True,
    )
    channel.queue_declare(queue=config.QUEUE_NOTIFICATIONS, durable=True)
    channel.queue_declare(queue=config.QUEUE_ANALYTICS, durable=True)
    channel.queue_bind(
        queue=config.QUEUE_NOTIFICATIONS, exchange=config.EXCHANGE_EVENTS
    )
    channel.queue_bind(queue=config.QUEUE_ANALYTICS, exchange=config.EXCHANGE_EVENTS)

    # Topic Exchange for logs (pattern-based routing)
    channel.exchange_declare(
        exchange=config.EXCHANGE_LOGS,
        exchange_type="topic",
        durable=True,
    )
    channel.queue_declare(queue=config.QUEUE_LOGS, durable=True)
    channel.queue_bind(
        queue=config.QUEUE_LOGS,
        exchange=config.EXCHANGE_LOGS,
        routing_key="order.#",  # Matches all order-related logs
    )

    # RPC Queue for inventory checks
    channel.queue_declare(queue=config.QUEUE_RPC, durable=True)

    print("✓ RabbitMQ infrastructure ready")
