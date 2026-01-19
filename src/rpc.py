"""RPC pattern for inventory checks."""

import json
import uuid
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from . import config
from .connection import create_connection


def run_rpc_server() -> None:
    """Run the RPC server that responds to inventory check requests."""
    connection = create_connection()
    channel = connection.channel()

    def on_request(
        ch: BlockingChannel,
        method: Basic.Deliver,
        props: BasicProperties,
        body: bytes,
    ) -> None:
        """Handle incoming RPC requests."""
        request = json.loads(body)
        product_id = request.get("product_id", "unknown")

        # Simulate inventory check (in reality, would query database)
        in_stock = product_id not in ["PROD-999"]
        quantity = 42 if in_stock else 0

        response = {
            "product_id": product_id,
            "in_stock": in_stock,
            "quantity": quantity,
        }

        print(f"[RPC Server] Inventory check for {product_id}: {quantity} units")

        # Send response back to reply_to queue with correlation_id
        if props.reply_to:
            ch.basic_publish(
                exchange="",
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=json.dumps(response),
            )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=config.QUEUE_RPC, on_message_callback=on_request)

    print(f"[RPC Server] Listening on queue: {config.QUEUE_RPC}")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[RPC Server] Shutting down...")
        channel.stop_consuming()
    finally:
        connection.close()


def check_inventory(product_id: str) -> dict[str, Any]:
    """
    Make an RPC call to check inventory for a product.

    Args:
        product_id: Product ID to check.

    Returns:
        Response dict with inventory information.
    """
    connection = create_connection()
    channel = connection.channel()

    # Create exclusive callback queue for responses
    result = channel.queue_declare(queue="", exclusive=True)
    callback_queue = result.method.queue

    # Generate unique correlation ID for this request
    corr_id = str(uuid.uuid4())

    # Storage for response
    response: dict[str, Any] = {}

    def on_response(
        ch: BlockingChannel,
        method: Basic.Deliver,
        props: BasicProperties,
        body: bytes,
    ) -> None:
        """Handle RPC response."""
        if props.correlation_id == corr_id:
            response.update(json.loads(body))
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=callback_queue,
        on_message_callback=on_response,
        auto_ack=False,
    )

    # Send request
    request = {"product_id": product_id}
    channel.basic_publish(
        exchange="",
        routing_key=config.QUEUE_RPC,
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id,
        ),
        body=json.dumps(request),
    )

    print(f"[RPC Client] Checking inventory for {product_id}...")

    # Wait for response
    connection.process_data_events(time_limit=5)

    connection.close()

    if not response:
        raise TimeoutError(f"RPC timeout: no response received for {product_id}")

    return response
