"""Producer for publishing orders to RabbitMQ."""

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src import config
from src.models import Order, OrderType


def publish_order(channel: BlockingChannel, order: Order) -> None:
    """
    Publish an order to the appropriate queue via direct exchange.

    This demonstrates:
    - Direct exchange routing based on routing keys
    - Message persistence (delivery_mode=2)
    - Content type specification

    Args:
        channel: RabbitMQ channel to publish on.
        order: The order to publish.
    """
    routing_key = _get_routing_key(order.order_type)

    properties = pika.BasicProperties(
        delivery_mode=2,  # Make message persistent
        content_type="application/json",
    )

    channel.basic_publish(
        exchange=config.EXCHANGE_ORDERS,
        routing_key=routing_key,
        body=order.to_json(),
        properties=properties,
    )

    print(
        f"📦 Published order {order.order_id} ({order.order_type.value}) with routing key: {routing_key}"
    )


def _get_routing_key(order_type: OrderType) -> str:
    """
    Determine the routing key based on order type.

    Args:
        order_type: The type of the order.

    Returns:
        The appropriate routing key for the order type.
    """
    mapping = {
        OrderType.STANDARD: config.ROUTING_KEY_STANDARD,
        OrderType.EXPRESS: config.ROUTING_KEY_EXPRESS,
        OrderType.INTERNATIONAL: config.ROUTING_KEY_INTERNATIONAL,
    }
    return mapping[order_type]
