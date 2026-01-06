"""Exchange, queue, and binding setup for RabbitMQ."""

from pika.adapters.blocking_connection import BlockingChannel

from src import config


def setup_infrastructure(channel: BlockingChannel) -> None:
    """
    Declare all exchanges, queues, and bindings.

    This demonstrates proper RabbitMQ infrastructure setup including
    exchange types, queue durability, dead letter exchanges, and bindings.

    Args:
        channel: RabbitMQ channel to use for declarations.
    """
    # Declare Dead Letter Exchange first (needed as dependency)
    channel.exchange_declare(
        exchange=config.EXCHANGE_DLX,
        exchange_type="fanout",
        durable=True,
    )

    # Declare Dead Letter Queue
    channel.queue_declare(
        queue=config.QUEUE_DLQ,
        durable=True,
    )

    # Bind DLQ to DLX
    channel.queue_bind(
        queue=config.QUEUE_DLQ,
        exchange=config.EXCHANGE_DLX,
    )

    # Declare Direct Exchange for order routing
    channel.exchange_declare(
        exchange=config.EXCHANGE_ORDERS,
        exchange_type="direct",
        durable=True,
    )

    # Declare order queues with DLX configuration
    dlx_args = {
        "x-dead-letter-exchange": config.EXCHANGE_DLX,
    }

    channel.queue_declare(
        queue=config.QUEUE_STANDARD_ORDERS,
        durable=True,
        arguments=dlx_args,
    )
    channel.queue_declare(
        queue=config.QUEUE_EXPRESS_ORDERS,
        durable=True,
        arguments=dlx_args,
    )
    channel.queue_declare(
        queue=config.QUEUE_INTERNATIONAL_ORDERS,
        durable=True,
        arguments=dlx_args,
    )

    # Bind order queues to direct exchange with routing keys
    channel.queue_bind(
        queue=config.QUEUE_STANDARD_ORDERS,
        exchange=config.EXCHANGE_ORDERS,
        routing_key=config.ROUTING_KEY_STANDARD,
    )
    channel.queue_bind(
        queue=config.QUEUE_EXPRESS_ORDERS,
        exchange=config.EXCHANGE_ORDERS,
        routing_key=config.ROUTING_KEY_EXPRESS,
    )
    channel.queue_bind(
        queue=config.QUEUE_INTERNATIONAL_ORDERS,
        exchange=config.EXCHANGE_ORDERS,
        routing_key=config.ROUTING_KEY_INTERNATIONAL,
    )

    # Declare Fanout Exchange for event broadcasting
    channel.exchange_declare(
        exchange=config.EXCHANGE_EVENTS,
        exchange_type="fanout",
        durable=True,
    )

    # Declare event subscriber queues
    channel.queue_declare(
        queue=config.QUEUE_NOTIFICATIONS,
        durable=True,
    )
    channel.queue_declare(
        queue=config.QUEUE_ANALYTICS,
        durable=True,
    )

    # Bind subscriber queues to fanout exchange
    # With fanout, all queues receive all messages regardless of routing key
    channel.queue_bind(
        queue=config.QUEUE_NOTIFICATIONS,
        exchange=config.EXCHANGE_EVENTS,
    )
    channel.queue_bind(
        queue=config.QUEUE_ANALYTICS,
        exchange=config.EXCHANGE_EVENTS,
    )

    # Declare Topic Exchange for flexible log routing
    channel.exchange_declare(
        exchange=config.EXCHANGE_LOGS,
        exchange_type="topic",
        durable=True,
    )

    # Declare log queue
    channel.queue_declare(
        queue=config.QUEUE_LOGS,
        durable=True,
    )

    # Bind with topic pattern to match all logs
    # Pattern: order.{created|processing|completed|failed}.{standard|express|international}
    channel.queue_bind(
        queue=config.QUEUE_LOGS,
        exchange=config.EXCHANGE_LOGS,
        routing_key="order.#",
    )

    # Declare RPC queue for inventory service
    channel.queue_declare(
        queue=config.QUEUE_INVENTORY_RPC,
        durable=False,  # RPC queues typically don't need durability
    )

    print("✓ RabbitMQ infrastructure setup complete")
    print(
        f"  - Exchanges: {config.EXCHANGE_ORDERS} (direct), {config.EXCHANGE_EVENTS} (fanout), {config.EXCHANGE_LOGS} (topic)"
    )
    print("  - Order queues: standard, express, international (with DLX)")
    print("  - Event subscribers: notifications, analytics")
    print(f"  - RPC queue: {config.QUEUE_INVENTORY_RPC}")
