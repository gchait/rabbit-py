"""RPC implementation for inventory checks."""

import json
import random
import uuid
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from .. import config


class InventoryRPCServer:
    """RPC server that responds to inventory check requests."""

    def __init__(self, channel: BlockingChannel) -> None:
        """
        Initialize the RPC server.

        Args:
            channel: RabbitMQ channel to use for RPC.
        """
        self.channel = channel

    def start(self) -> None:
        """
        Start the RPC server.

        This demonstrates:
        - RPC pattern (request/response)
        - Correlation ID for matching requests and responses
        - Reply-to queue for responses
        - Synchronous-style communication over async messaging
        """
        print("🔍 Inventory RPC server started")
        print(f"   Listening on queue: {config.QUEUE_INVENTORY_RPC}")

        self.channel.basic_consume(
            queue=config.QUEUE_INVENTORY_RPC,
            on_message_callback=self._on_request,
        )

        try:
            print("   [*] Waiting for RPC requests. To exit press CTRL+C")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\n🔍 Inventory RPC server stopping...")
            self.channel.stop_consuming()

    def _on_request(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """
        Handle an RPC request.

        Args:
            ch: Channel the message was received on.
            method: Delivery method containing routing info.
            properties: Message properties with correlation_id and reply_to.
            body: Request body.
        """
        request = json.loads(body.decode())
        product_id = request.get("product_id")
        quantity = request.get("quantity")

        print(
            f"   🔍 RPC request: Check inventory for product {product_id}, quantity {quantity}"
        )

        # Simulate inventory check
        available = self._check_inventory(product_id, quantity)

        response = {
            "product_id": product_id,
            "quantity": quantity,
            "available": available,
            "stock_level": random.randint(0, 100),
        }

        # Send response back to reply_to queue with same correlation_id
        if properties.reply_to:
            ch.basic_publish(
                exchange="",
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id,
                ),
                body=json.dumps(response),
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"      → Response sent: available={available}")

    def _check_inventory(self, product_id: str, quantity: int) -> bool:
        """
        Check if inventory is available.

        Args:
            product_id: The product to check.
            quantity: Quantity requested.

        Returns:
            True if inventory is available, False otherwise.
        """
        # Simulate inventory check (random for demo)
        return random.random() > 0.2


class InventoryRPCClient:
    """RPC client for making inventory check requests."""

    def __init__(self, channel: BlockingChannel) -> None:
        """
        Initialize the RPC client.

        Args:
            channel: RabbitMQ channel to use for RPC.
        """
        self.channel = channel

        # Declare exclusive callback queue for responses
        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.response: dict[str, Any] | None = None
        self.correlation_id: str | None = None

        # Start consuming responses
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True,
        )

    def _on_response(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """
        Handle RPC response.

        Args:
            ch: Channel the message was received on.
            method: Delivery method containing routing info.
            properties: Message properties with correlation_id.
            body: Response body.
        """
        if self.correlation_id == properties.correlation_id:
            self.response = json.loads(body.decode())

    def check_inventory(self, product_id: str, quantity: int) -> dict[str, Any]:
        """
        Check inventory availability via RPC.

        This demonstrates the RPC pattern where we wait for a response.

        Args:
            product_id: The product to check.
            quantity: Quantity to check.

        Returns:
            Dictionary with inventory availability information.
        """
        # Generate unique correlation ID for this request
        self.correlation_id = str(uuid.uuid4())
        self.response = None

        request = {
            "product_id": product_id,
            "quantity": quantity,
        }

        # Send request with reply_to and correlation_id
        self.channel.basic_publish(
            exchange="",
            routing_key=config.QUEUE_INVENTORY_RPC,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.correlation_id,
            ),
            body=json.dumps(request),
        )

        # Wait for response (synchronous-style over async messaging)
        while self.response is None:
            self.channel.connection.process_data_events(time_limit=1)

        return self.response
