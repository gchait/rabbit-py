"""Order worker consumer."""

import json
import random
import time

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from . import config


def start_worker(channel: BlockingChannel, worker_id: str) -> None:
    """
    Start an order worker that processes orders from the queue.

    Demonstrates:
    - Work queues (competing consumers)
    - Fair dispatch with QoS (prefetch_count=1)
    - Manual acknowledgments
    - Dead letter exchange on failure

    Args:
        channel: RabbitMQ channel to consume from.
        worker_id: Identifier for this worker instance.
    """
    # Fair dispatch: only take 1 message at a time
    channel.basic_qos(prefetch_count=1)

    print(f"👷 Worker {worker_id} started")
    print(f"   Consuming from: {config.QUEUE_ORDERS}")
    print("   Fair dispatch enabled (prefetch_count=1)\n")

    def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """
        Process an order message.

        Args:
            ch: Channel the message was received on.
            method: Delivery method.
            properties: Message properties.
            body: Message body.
        """
        try:
            order = json.loads(body.decode())
            print(f"   Worker {worker_id} processing {order['order_id']}")

            # Simulate processing work
            processing_time = random.uniform(0.5, 2.0)
            time.sleep(processing_time)

            # Simulate random failures (10% chance)
            if random.random() < 0.1:
                raise RuntimeError(f"Processing failed for {order['order_id']}")

            print(
                f"   ✓ Worker {worker_id} completed {order['order_id']} ({processing_time:.2f}s)"
            )

            # Publish event to fanout exchange
            event = {
                "order_id": order["order_id"],
                "status": "completed",
                "worker_id": worker_id,
                "processing_time": processing_time,
            }
            ch.basic_publish(
                exchange=config.EXCHANGE_EVENTS,
                routing_key="",
                body=json.dumps(event),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            # Publish log to topic exchange (demonstrates topic routing)
            log_message = {
                "event": "order.completed",
                "order_id": order["order_id"],
                "worker_id": worker_id,
                "timestamp": time.time(),
            }
            ch.basic_publish(
                exchange=config.EXCHANGE_LOGS,
                routing_key="order.completed",  # Topic pattern
                body=json.dumps(log_message),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            # Acknowledge successful processing
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"   ✗ Worker {worker_id} failed: {e}")
            # Negative acknowledge - send to Dead Letter Exchange
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(
        queue=config.QUEUE_ORDERS,
        on_message_callback=callback,
        auto_ack=False,  # Manual acknowledgments
    )

    try:
        print("   [*] Waiting for orders. Press CTRL+C to exit\n")
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n👷 Worker {worker_id} stopping...")
        channel.stop_consuming()
