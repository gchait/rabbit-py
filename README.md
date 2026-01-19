# RabbitMQ Order Processing Demo

A comprehensive demonstration of RabbitMQ concepts using Python. Learn all major RabbitMQ patterns through a practical, working example—all in **one terminal**!

## 🎯 What You'll Learn

| Concept                  | Description                          | Where to See It                    |
| ------------------------ | ------------------------------------ | ---------------------------------- |
| **Direct Exchange**      | Route messages by exact key match    | Orders routed to work queue        |
| **Fanout Exchange**      | Broadcast to all bound queues        | Events → Notifications & Analytics |
| **Topic Exchange**       | Pattern-based routing with wildcards | Logs matching `order.#` pattern    |
| **Work Queues**          | Multiple workers competing for tasks | Order processing                   |
| **Fair Dispatch (QoS)**  | Load balancing with prefetch_count   | Worker distribution                |
| **Manual Ack/Nack**      | Reliable message processing          | Order acknowledgments              |
| **Dead Letter Exchange** | Failed message handling              | Failed orders → DLQ                |
| **Message Persistence**  | Survive broker restarts              | Durable queues & messages          |
| **RPC Pattern**          | Request/Response over messaging      | Inventory checks                   |

## 🚀 Quick Start

### 1. Start RabbitMQ

```bash
pdm run rabbitup
```

Access RabbitMQ Management UI at http://localhost:15672 (user: `guy`, password: `yug`)

### 2. Run the Complete Demo

```bash
pdm run demo
```

**That's it!** This single command:

- Sets up all infrastructure (exchanges, queues, bindings)
- Starts all services (RPC, notifications, analytics, logs, worker)
- Demonstrates RPC pattern with inventory checks
- Publishes and processes orders
- Shows all RabbitMQ patterns in action

Watch the output to see messages flow through different exchanges and queues!

## 📋 Available Commands

### Primary Command

```bash
pdm run demo              # Full demo in one terminal (recommended!)
```

### Individual Component Commands

For experimentation and learning:

```bash
# Consumers
pdm run demo worker [id]  # Start order worker (default: W1)
pdm run demo notification # Start notification service
pdm run demo analytics    # Start analytics service
pdm run demo logs         # Start log consumer

# Producers
pdm run demo produce      # Publish sample orders

# RPC
pdm run demo rpc-server   # Start RPC server
pdm run demo rpc-client   # Test RPC calls
```

## 🏗️ Architecture

```
Producer → Direct Exchange ──(routing_key)──→ Orders Queue → Workers
              (orders.direct)                                    │
                                                                 ├→ Fanout Exchange → Notifications Queue
                                                                 │   (events.fanout) → Analytics Queue
                                                                 │
                                                                 └→ Topic Exchange ──(order.#)──→ Logs Queue
                                                                     (logs.topic)

RPC Client ←────(request/response)────→ RPC Server
           (correlation_id, reply_to)

Failed Messages → Dead Letter Exchange → Dead Letter Queue
                      (orders.dlx)         (orders.failed)
```

## 📖 Concept Explanations

### Direct Exchange

Routes messages based on **exact matching** between routing key and binding key.

**In this demo:** Orders published with `routing_key="order"` go only to the orders queue bound with that key.

**Why use it:** Type-safe routing—each message type goes to its specific queue. Like a postal service sorting mail by exact zip codes.

**Real-world:** Task queues, job processing, request routing.

---

### Fanout Exchange

Broadcasts **every message** to **all** queues bound to it, ignoring routing keys.

**In this demo:** When a worker completes an order, it publishes an event. Both notification AND analytics services receive the same event.

**Why use it:** Pub/Sub pattern—one event triggers multiple independent actions. Like a notification system broadcasting to email, SMS, and push notifications.

**Real-world:** Logging systems, real-time dashboards, cache invalidation, notifications.

---

### Topic Exchange

Routes based on **pattern matching** with wildcards:

- `*` matches exactly one word
- `#` matches zero or more words

**In this demo:** Logs published with keys like `order.created` and `order.completed` both match the pattern `order.#`.

**Why use it:** Flexible, hierarchical routing. More control than fanout, more flexibility than direct.

**Real-world:** Log aggregation (`error.*`, `info.*`), geographic routing (`us.east.*`, `eu.*`), multi-tenant systems.

---

### Work Queues (Competing Consumers)

Multiple workers consume from the **same queue**. Each message goes to **exactly one** worker.

**In this demo:** Multiple workers can process orders. RabbitMQ distributes messages among them.

**Why use it:** Horizontal scaling—handle more work by adding workers. Provides redundancy if a worker crashes.

**Real-world:** Background jobs, video encoding, email sending, image processing.

---

### QoS (Quality of Service) & Fair Dispatch

`prefetch_count=1` means "only give me 1 message at a time—I must ack before getting another."

**In this demo:** Each worker processes one order at a time. Fast workers automatically get more work than slow ones.

**Why use it:**

- **Without it:** Round-robin might give 50 quick tasks to Worker1 and 50 slow tasks to Worker2
- **With it:** True load balancing—fast workers handle more

**Real-world:** Any multi-worker system with variable processing times.

---

### Message Acknowledgments (ack/nack)

Signals from consumer to RabbitMQ about processing status:

- **ack:** "Success—delete this message"
- **nack(requeue=False):** "Failed—send to DLX"
- **nack(requeue=True):** "Failed—try again"

**In this demo:** Workers ack on success, nack on failure. Failed messages go to Dead Letter Queue.

**Why use manual acks:**

- If worker crashes mid-processing, message isn't lost
- RabbitMQ redelivers to another worker
- Auto-ack would delete messages immediately = data loss risk

**Real-world:** Any system where message loss is unacceptable—financial transactions, orders, critical notifications.

---

### Dead Letter Exchange (DLX)

A "backup" exchange where failed messages automatically go.

**In this demo:** Order queue configured with `x-dead-letter-exchange: orders.dlx`. When worker nacks with `requeue=False`, message routes to DLX → DLQ.

**Common triggers:**

1. Message rejected with nack(requeue=False)
2. Message TTL expires
3. Queue reaches max-length

**Why use it:**

- Prevents message loss even when processing repeatedly fails
- Allows debugging—inspect failed messages
- Enables retry logic—process DLQ messages later

**Real-world:** Error handling, delayed retry queues, debugging production issues.

---

### Message Persistence

Messages and queues survive RabbitMQ broker restarts.

**Two parts:**

1. **Durable queues:** Queue definition survives restart
2. **Persistent messages:** Message data survives restart (`delivery_mode=2`)

**In this demo:** All queues declared `durable=True`, all messages published with `delivery_mode=2`.

**Trade-off:** Persistence is slower (disk I/O) but safer.

**Real-world:** Financial transactions, order confirmations, anything that can't be lost.

---

### RPC (Remote Procedure Call) Pattern

Synchronous request/response over asynchronous messaging.

**How it works:**

1. Client generates unique `correlation_id`
2. Client creates exclusive `reply_to` queue for responses
3. Client publishes request with both properties
4. Server processes and responds to `reply_to` queue with same `correlation_id`
5. Client matches response using `correlation_id`

**In this demo:** Client checks inventory, server responds with stock levels.

**Why use it:** When you **need a response** before continuing (e.g., check inventory before processing order).

**When NOT to use:** If you don't need a response, use regular pub/sub—RPC adds complexity and latency.

**Real-world:** API gateways, microservice communication requiring responses, distributed systems.

---

## 📁 Project Structure

```
src/
├── config.py           # Configuration and constants
├── connection.py       # RabbitMQ connection helper
├── setup.py            # Infrastructure setup (exchanges/queues/bindings)
├── demo.py             # Main demo CLI
├── producer.py         # Order publisher
├── worker.py           # Order processor (work queue consumer)
├── notification.py     # Notification service (fanout subscriber)
├── analytics.py        # Analytics service (fanout subscriber)
├── log_consumer.py     # Log service (topic subscriber)
└── rpc.py              # RPC server and client
```

## 🎓 Learning Exercises

### 1. Experiment with Exchange Types

- Run the full demo and observe how direct exchange routes orders
- Notice how fanout broadcasts the same event to notifications AND analytics
- See how topic exchange matches log patterns

### 2. Test Message Reliability

**Challenge:** What happens if a worker crashes mid-processing?

```bash
# Terminal 1
pdm run demo worker W1

# Terminal 2
pdm run demo produce

# In Terminal 1: Kill with Ctrl+C while processing
# Start another worker and see message recovery!
```

### 3. Load Balancing with Multiple Workers

```bash
# Terminal 1
pdm run demo worker W1

# Terminal 2
pdm run demo worker W2

# Terminal 3
pdm run demo produce
```

Watch how messages distribute between workers!

### 4. Dead Letter Queues

Check the management UI at http://localhost:15672 after running the demo. Look for messages in the `orders.failed` queue (10% failure rate is simulated).

### 5. RPC Pattern

```bash
# Terminal 1
pdm run demo rpc-server

# Terminal 2
pdm run demo rpc-client
```

Notice how the client **waits** for responses—synchronous communication over async messaging!

## 🧰 Development Commands

```bash
# Code quality
pdm run fmt        # Format code with ruff
pdm run chk        # Check code with ruff
pdm run typechk    # Type check with mypy
pdm run lint       # Run both checks
pdm run fint       # Format and lint

# RabbitMQ
pdm run rabbitup   # Start RabbitMQ
pdm run rabbitdown # Stop RabbitMQ
```

## ⚠️ Out of Scope (Production Considerations)

This is a **learning demo** focused on core RabbitMQ concepts. The following production-critical features are intentionally NOT implemented:

### Publisher Confirms

**What it is:** Confirmation from RabbitMQ that a message was successfully received and persisted.

**Why it matters:** Without confirms, you have no guarantee your `basic_publish()` succeeded. The broker could reject it, run out of disk, or crash—and you'd never know.

**How to implement:**

```python
channel.confirm_delivery()  # Enable confirm mode
try:
    channel.basic_publish(...)  # Raises exception if not confirmed
except pika.exceptions.UnroutableError:
    # Handle failure
```

**Production impact:** Critical for financial transactions, orders, or any data you can't afford to lose.

---

### Connection Reliability

**Missing features:**

1. **Heartbeats** - No heartbeat monitoring configured. Idle connections may be closed unexpectedly.
2. **Automatic Reconnection** - If connection drops, our consumers/producers don't reconnect.
3. **Connection Timeouts** - No `socket_timeout` or `blocked_connection_timeout` set.

**Why it matters:** Production RabbitMQ connections experience network hiccups, broker restarts, and load-balancer timeouts. Without retry logic, your application stops working.

**How to implement:**

```python
# Add to connection parameters:
parameters = pika.ConnectionParameters(
    host=config.RABBITMQ_HOST,
    heartbeat=600,  # Send heartbeat every 10min
    blocked_connection_timeout=300,
    socket_timeout=10,
)

# Use pika's connection adapters with retry logic
# or libraries like pika-pool for connection pooling
```

---

### Thread Safety

**The issue:** Pika's `BlockingConnection` is NOT thread-safe. Our full demo uses threads, which technically violates this.

**Why it works here:** Each thread creates its own connection/channel. But sharing a connection across threads would cause crashes.

**Production solution:**

- Use one connection per thread
- Or use `SelectConnection` (async, event-driven)
- Or use libraries specifically designed for threading (e.g., `pika-pool`)

---

### Additional Concepts Not Covered

| Concept                   | Why Omitted                        | Production Use                                           |
| ------------------------- | ---------------------------------- | -------------------------------------------------------- |
| **Headers Exchange**      | Rarely used, complex for beginners | Routing based on message headers instead of routing keys |
| **Alternate Exchange**    | Advanced routing scenario          | Fallback for unroutable messages                         |
| **TTL (Time-To-Live)**    | Mentioned but not demonstrated     | Auto-expire old messages                                 |
| **Priority Queues**       | Specialized use case               | Process urgent messages first                            |
| **Lazy Queues**           | Operational optimization           | Move messages to disk early to save RAM                  |
| **Quorum Queues**         | Availability/replication concern   | Replicated queues for high availability                  |
| **Consumer Cancellation** | Edge case handling                 | Graceful shutdown when queue deleted                     |
| **Flow Control**          | Advanced backpressure              | Handle slow consumers gracefully                         |
