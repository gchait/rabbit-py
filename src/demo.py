"""Main demonstration script showcasing RabbitMQ concepts."""

import sys
import time

from .connection import create_channel, create_connection
from .consumers.analytics import start_analytics_service
from .consumers.log_consumer import start_log_service
from .consumers.notification import start_notification_service
from .consumers.order_worker import get_queue_for_order_type, start_worker
from .exchanges import setup_infrastructure
from .models import EventType, Order, OrderEvent, OrderType
from .producers.event_producer import publish_event, publish_log
from .producers.order_producer import publish_order
from .rpc.inventory_rpc import InventoryRPCClient, InventoryRPCServer


def demo_setup() -> None:
    """Set up RabbitMQ infrastructure."""
    print("\n" + "=" * 80)
    print("DEMO: Setting up RabbitMQ infrastructure")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        setup_infrastructure(channel)
    finally:
        connection.close()

    print("\n✅ Infrastructure setup complete!")
    time.sleep(1)


def demo_producer() -> None:
    """Demonstrate order production with different types."""
    print("\n" + "=" * 80)
    print("DEMO: Publishing orders via Direct Exchange")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)

        orders = [
            Order("ORD-001", "CUST-101", "PROD-A", 2, OrderType.STANDARD),
            Order("ORD-002", "CUST-102", "PROD-B", 5, OrderType.EXPRESS),
            Order("ORD-003", "CUST-103", "PROD-C", 1, OrderType.INTERNATIONAL),
            Order("ORD-004", "CUST-104", "PROD-D", 3, OrderType.STANDARD),
        ]

        for order in orders:
            # Publish order creation event
            event = OrderEvent(
                event_type=EventType.ORDER_CREATED,
                order_id=order.order_id,
                message=f"Order created for customer {order.customer_id}",
                metadata={"product_id": order.product_id, "quantity": order.quantity},
            )
            publish_event(channel, event)
            publish_log(channel, event, order.order_type.value)

            # Publish order to appropriate queue
            publish_order(channel, order)
            time.sleep(0.5)

    finally:
        connection.close()

    print("\n✅ All orders published!")
    time.sleep(2)


def demo_worker(
    worker_id: str, order_type: OrderType, should_fail: bool = False
) -> None:
    """
    Run an order worker.

    Args:
        worker_id: Identifier for this worker.
        order_type: Type of orders this worker processes.
        should_fail: Whether to simulate failures.
    """
    print("\n" + "=" * 80)
    print(f"DEMO: Starting Worker {worker_id} for {order_type.value} orders")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        queue_name = get_queue_for_order_type(order_type)
        start_worker(channel, queue_name, worker_id, should_fail)
    finally:
        connection.close()


def demo_notification_service() -> None:
    """Run the notification service."""
    print("\n" + "=" * 80)
    print("DEMO: Starting Notification Service (Fanout Subscriber)")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        start_notification_service(channel)
    finally:
        connection.close()


def demo_analytics_service() -> None:
    """Run the analytics service."""
    print("\n" + "=" * 80)
    print("DEMO: Starting Analytics Service (Fanout Subscriber)")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        start_analytics_service(channel)
    finally:
        connection.close()


def demo_log_service() -> None:
    """Run the log service."""
    print("\n" + "=" * 80)
    print("DEMO: Starting Log Service (Topic Exchange)")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        start_log_service(channel)
    finally:
        connection.close()


def demo_rpc_server() -> None:
    """Run the RPC server."""
    print("\n" + "=" * 80)
    print("DEMO: Starting Inventory RPC Server")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        server = InventoryRPCServer(channel)
        server.start()
    finally:
        connection.close()


def demo_rpc_client() -> None:
    """Demonstrate RPC client making requests."""
    print("\n" + "=" * 80)
    print("DEMO: Making RPC inventory checks")
    print("=" * 80)

    connection = create_connection()
    try:
        channel = create_channel(connection)
        client = InventoryRPCClient(channel)

        products = [
            ("PROD-A", 2),
            ("PROD-B", 5),
            ("PROD-C", 1),
        ]

        for product_id, quantity in products:
            print(f"\n🔍 Checking inventory for {product_id}, quantity {quantity}...")
            result = client.check_inventory(product_id, quantity)
            print(f"   Result: {result}")
            time.sleep(1)

    finally:
        connection.close()

    print("\n✅ RPC demo complete!")


def print_usage() -> None:
    """Print usage instructions."""
    print("\n" + "=" * 80)
    print("RABBITMQ ORDER PROCESSING DEMO")
    print("=" * 80)
    print("\nThis demo showcases key RabbitMQ concepts:")
    print("  • Direct Exchange - Route orders by type")
    print("  • Fanout Exchange - Broadcast events to multiple subscribers")
    print("  • Topic Exchange - Pattern-based log routing")
    print("  • Work Queues - Competing consumers with fair dispatch")
    print("  • Dead Letter Exchange - Handle failed messages")
    print("  • Message Acknowledgments - Reliable processing")
    print("  • RPC Pattern - Synchronous request/response")
    print("\nUsage:")
    print("  pdm run python -m src.demo setup              # Setup infrastructure")
    print("  pdm run python -m src.demo producer           # Publish orders")
    print("  pdm run python -m src.demo worker <type> [id] # Start order worker")
    print(
        "  pdm run python -m src.demo notification       # Start notification service"
    )
    print("  pdm run python -m src.demo analytics          # Start analytics service")
    print("  pdm run python -m src.demo logs               # Start log service")
    print("  pdm run python -m src.demo rpc-server         # Start RPC server")
    print("  pdm run python -m src.demo rpc-client         # Make RPC calls")
    print("\nOrder types: standard, express, international")
    print("\nRecommended flow:")
    print("  1. Run 'setup' in one terminal")
    print("  2. Start 'rpc-server' in another terminal (for inventory checks)")
    print("  3. Start 'notification', 'analytics', 'logs' in separate terminals")
    print("  4. Start multiple 'worker' instances with different IDs")
    print("  5. Run 'producer' to send orders and watch them flow through!")
    print("  6. Test 'rpc-client' to see synchronous RPC pattern")
    print("=" * 80 + "\n")


def main() -> None:
    """Main entry point for the demo."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    try:
        if command == "setup":
            demo_setup()
        elif command == "producer":
            demo_producer()
        elif command == "worker":
            if len(sys.argv) < 3:
                print(
                    "Error: worker requires order type (standard|express|international)"
                )
                print("Usage: pdm run python -m src.demo worker <type> [id]")
                return
            order_type_str = sys.argv[2]
            worker_id = sys.argv[3] if len(sys.argv) > 3 else "W1"
            try:
                order_type = OrderType(order_type_str)
                demo_worker(worker_id, order_type)
            except ValueError:
                print(f"Error: Invalid order type '{order_type_str}'")
                print("Valid types: standard, express, international")
        elif command == "notification":
            demo_notification_service()
        elif command == "analytics":
            demo_analytics_service()
        elif command == "logs":
            demo_log_service()
        elif command == "rpc-server":
            demo_rpc_server()
        elif command == "rpc-client":
            demo_rpc_client()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
