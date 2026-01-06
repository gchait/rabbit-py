"""Worker consumer for processing orders from queues."""

import random
import time

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from src import config
from src.models import EventType, Order, OrderEvent, OrderType
from src.producers.event_producer import publish_event, publish_log


def start_worker(
    channel: BlockingChannel, queue_name: str, worker_id: str, should_fail: bool = False
) -> None:
    """
    Start an order worker that processes orders from a queue.

    This demonstrates:
    - Work queues (competing consumers pattern)
    - Fair dispatch with prefetch count (QoS)
    - Manual message acknowledgments
    - Proper error handling with nack and requeue
    - Dead letter queue integration

    Args:
        channel: RabbitMQ channel to consume from.
        queue_name: Name of the queue to consume from.
        worker_id: Identifier for this worker instance.
        should_fail: Whether to simulate failures for DLX demonstration.
    """
    # Set QoS - only take 1 message at a time (fair dispatch)
    channel.basic_qos(prefetch_count=config.PREFETCH_COUNT)

    print(f"👷 Worker {worker_id} started, consuming from {queue_name}")
    print(f"   Prefetch count: {config.PREFETCH_COUNT} (fair dispatch enabled)")

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
            method: Delivery method containing routing info.
            properties: Message properties.
            body: Message body.
        """
        try:
            order = Order.from_json(body.decode())
            print(f"   Worker {worker_id} received order {order.order_id}")

            # Publish processing event
            event = OrderEvent(
                event_type=EventType.ORDER_PROCESSING,
                order_id=order.order_id,
                message=f"Processing by worker {worker_id}",
                metadata={"worker_id": worker_id},
            )
            publish_event(ch, event)
            publish_log(ch, event, order.order_type.value)

            # Simulate processing work
            processing_time = random.uniform(0.5, 2.0)
            time.sleep(processing_time)

            # Simulate failure for DLX demonstration
            if should_fail and random.random() < 0.3:
                raise Exception(
                    f"Simulated processing failure for order {order.order_id}"
                )

            # Processing successful
            print(
                f"   ✓ Worker {worker_id} completed order {order.order_id} in {processing_time:.2f}s"
            )

            # Publish completion event
            event = OrderEvent(
                event_type=EventType.ORDER_COMPLETED,
                order_id=order.order_id,
                message=f"Completed by worker {worker_id}",
                metadata={"worker_id": worker_id, "processing_time": processing_time},
            )
            publish_event(ch, event)
            publish_log(ch, event, order.order_type.value)

            # Acknowledge message - it will be removed from queue
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"   ✗ Worker {worker_id} failed to process order: {e}")

            # Publish failure event
            try:
                order = Order.from_json(body.decode())
                event = OrderEvent(
                    event_type=EventType.ORDER_FAILED,
                    order_id=order.order_id,
                    message=f"Failed: {str(e)}",
                    metadata={"worker_id": worker_id},
                )
                publish_event(ch, event)
                publish_log(ch, event, order.order_type.value)
            except Exception:
                pass

            # Negative acknowledge with no requeue - send to DLX
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    # Start consuming
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=False,  # Manual acknowledgment for reliability
    )

    try:
        print("   [*] Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n👷 Worker {worker_id} stopping...")
        channel.stop_consuming()


def get_queue_for_order_type(order_type: OrderType) -> str:
    """
    Get the queue name for a given order type.

    Args:
        order_type: The type of order.

    Returns:
        The queue name for that order type.
    """
    mapping = {
        OrderType.STANDARD: config.QUEUE_STANDARD_ORDERS,
        OrderType.EXPRESS: config.QUEUE_EXPRESS_ORDERS,
        OrderType.INTERNATIONAL: config.QUEUE_INTERNATIONAL_ORDERS,
    }
    return mapping[order_type]
