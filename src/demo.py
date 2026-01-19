"""RabbitMQ demonstration CLI."""

import sys
import threading
import time
from collections.abc import Callable

from .analytics import run_analytics_service
from .connection import create_connection
from .log_consumer import run_log_consumer
from .notification import run_notification_service
from .producer import publish_orders
from .rpc import check_inventory, run_rpc_server
from .setup import setup_infrastructure
from .worker import start_worker


def run_full_demo() -> None:
    """Run complete demo with all components in a single terminal."""
    print("🚀 Starting RabbitMQ Full Demo\n")
    print("=" * 60)

    # Setup infrastructure
    connection = create_connection()
    channel = connection.channel()
    setup_infrastructure(channel)
    connection.close()

    print("\n📋 Starting all services...\n")

    # Track stop flag for error handling
    stop_event = threading.Event()

    def run_service(name: str, func: Callable[[], None]) -> None:
        """Run a service in thread with error handling."""
        try:
            print(f"   ✓ {name} started")
            func()
        except Exception as e:
            if not stop_event.is_set():
                print(f"   ✗ {name} error: {e}")

    # Start RPC server
    rpc_thread = threading.Thread(
        target=run_service,
        args=("RPC Server", run_rpc_server),
        daemon=True,
    )
    rpc_thread.start()
    time.sleep(0.5)

    # Start notification service
    notif_thread = threading.Thread(
        target=run_service,
        args=("Notification Service", run_notification_service),
        daemon=True,
    )
    notif_thread.start()
    time.sleep(0.3)

    # Start analytics service
    analytics_thread = threading.Thread(
        target=run_service,
        args=("Analytics Service", run_analytics_service),
        daemon=True,
    )
    analytics_thread.start()
    time.sleep(0.3)

    # Start log consumer
    log_thread = threading.Thread(
        target=run_service,
        args=("Log Service", run_log_consumer),
        daemon=True,
    )
    log_thread.start()
    time.sleep(0.3)

    # Start worker
    def worker_wrapper() -> None:
        conn = create_connection()
        ch = conn.channel()
        start_worker(ch, "W1")

    worker_thread = threading.Thread(
        target=run_service,
        args=("Order Worker", worker_wrapper),
        daemon=True,
    )
    worker_thread.start()
    time.sleep(1)

    print("\n" + "=" * 60)
    print("\n💡 All services running! Now demonstrating RabbitMQ patterns...\n")
    time.sleep(1)

    # Demonstrate RPC pattern
    print("=" * 60)
    print("📞 RPC Pattern Demo (Request/Response)")
    print("=" * 60)
    for product_id in ["PROD-123", "PROD-999", "PROD-456"]:
        result = check_inventory(product_id)
        if result:
            status = "✓ IN STOCK" if result.get("in_stock") else "✗ OUT OF STOCK"
            print(f"   {product_id}: {status} ({result.get('quantity', 0)} units)")
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("📦 Publishing Orders (Direct Exchange → Work Queue)")
    print("=" * 60)

    # Publish orders
    connection = create_connection()
    channel = connection.channel()
    try:
        publish_orders(channel)
    finally:
        connection.close()

    print("\n" + "=" * 60)
    print("⏳ Processing orders... (watch the logs above)")
    print("=" * 60)
    print("\nYou should see:")
    print("  • Worker processing orders (Direct Exchange → Work Queue)")
    print("  • Notifications & Analytics receiving events (Fanout Exchange)")
    print("  • Logs matching pattern 'order.#' (Topic Exchange)")
    print("\nPress CTRL+C to exit...")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down all services...")
        stop_event.set()


def main() -> None:
    """Main entry point for the demo."""
    if len(sys.argv) < 2:
        print("RabbitMQ Order Processing Demo\n")
        print("Usage:")
        print(
            "  pdm run demo                # Run full demo (all patterns in one terminal)"
        )
        print("  pdm run demo worker [id]    # Start order worker (default: W1)")
        print("  pdm run demo notification   # Start notification service")
        print("  pdm run demo analytics      # Start analytics service")
        print("  pdm run demo logs           # Start log consumer")
        print("  pdm run demo rpc-server     # Start RPC server")
        print("  pdm run demo rpc-client     # Test RPC client")
        print("  pdm run demo produce        # Publish sample orders\n")
        print("💡 Tip: Run 'pdm run demo' for a complete demonstration!")
        return

    command = sys.argv[1]

    try:
        if command == "full" or command == "all":
            run_full_demo()
            return

        # Services that manage their own connections
        if command == "notification":
            run_notification_service()
            return
        elif command == "analytics":
            run_analytics_service()
            return
        elif command == "logs":
            run_log_consumer()
            return
        elif command == "rpc-server":
            run_rpc_server()
            return

        # Commands that need a connection
        connection = create_connection()
        channel = connection.channel()

        # Auto-setup infrastructure on first run
        setup_infrastructure(channel)

        if command == "worker":
            worker_id = sys.argv[2] if len(sys.argv) > 2 else "W1"
            start_worker(channel, worker_id)
        elif command == "rpc-client":
            for product_id in ["PROD-123", "PROD-999", "PROD-456"]:
                result = check_inventory(product_id)
                print(f"Result: {result}")
        elif command == "produce":
            publish_orders(channel)
        else:
            print(f"Unknown command: {command}")
            return

        connection.close()

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Default to full demo if no args
    if len(sys.argv) == 1:
        sys.argv.append("full")
    main()
