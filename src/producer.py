"""Order producer."""

import json
import time

import pika
from pika.adapters.blocking_connection import BlockingChannel

from . import config


def publish_orders(channel: BlockingChannel) -> None:
    """
    Publish sample orders to the queue.

    Args:
        channel: RabbitMQ channel to publish on.
    """
    orders = [
        {
            "order_id": "ORD-001",
            "customer_id": "CUST-101",
            "product": "Widget A",
            "quantity": 2,
        },
        {
            "order_id": "ORD-002",
            "customer_id": "CUST-102",
            "product": "Widget B",
            "quantity": 5,
        },
        {
            "order_id": "ORD-003",
            "customer_id": "CUST-103",
            "product": "Widget C",
            "quantity": 1,
        },
        {
            "order_id": "ORD-004",
            "customer_id": "CUST-104",
            "product": "Widget D",
            "quantity": 3,
        },
    ]

    properties = pika.BasicProperties(
        delivery_mode=2,  # Persistent
        content_type="application/json",
    )

    for order in orders:
        # Publish order to direct exchange
        channel.basic_publish(
            exchange=config.EXCHANGE_ORDERS,
            routing_key="order",
            body=json.dumps(order),
            properties=properties,
        )
        print(f"📦 Published order {order['order_id']}")

        # Publish log to topic exchange (demonstrates topic routing)
        log_message = {
            "event": "order.created",
            "order_id": order["order_id"],
            "timestamp": time.time(),
        }
        channel.basic_publish(
            exchange=config.EXCHANGE_LOGS,
            routing_key="order.created",  # Topic pattern
            body=json.dumps(log_message),
            properties=properties,
        )

        time.sleep(0.5)

    print("\n✅ All orders published!")
