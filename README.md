# RabbitMQ Order Processing Demo

A comprehensive demonstration of RabbitMQ concepts using Python and an e-commerce order processing system. Learn RabbitMQ patterns through a practical, working example!

## 🎯 RabbitMQ Concepts Demonstrated

| Concept                     | Implementation                                        | File                                                   |
| --------------------------- | ----------------------------------------------------- | ------------------------------------------------------ |
| **Direct Exchange**         | Route orders by type (standard/express/international) | `exchanges.py`, `order_producer.py`                    |
| **Fanout Exchange**         | Broadcast events to notification & analytics services | `event_producer.py`, `notification.py`, `analytics.py` |
| **Topic Exchange**          | Pattern-based log routing with hierarchical keys      | `log_consumer.py`                                      |
| **Work Queues**             | Multiple workers competing for orders                 | `order_worker.py`                                      |
| **Fair Dispatch**           | QoS with prefetch_count for load balancing            | `order_worker.py`                                      |
| **Message Acknowledgments** | Manual ack/nack for reliability                       | All consumers                                          |
| **Dead Letter Exchange**    | Handle failed messages automatically                  | `exchanges.py`                                         |
| **Message Persistence**     | Durable queues and persistent messages                | All producers                                          |
| **RPC Pattern**             | Synchronous request/response for inventory checks     | `inventory_rpc.py`                                     |

## 🚀 Quick Start

### 1. Start RabbitMQ

```bash
pdm run rabbitup
```

Access RabbitMQ Management UI at http://localhost:15672 (user: `guy`, password: `yug`)

### 2. Setup Infrastructure

```bash
pdm run python -m src.demo setup
```

This creates all exchanges, queues, and bindings.

### 3. Run the Demo

Open **multiple terminals** and run these commands to see the system in action:

**Terminal 1 - RPC Server:**

```bash
pdm run python -m src.demo rpc-server
```

**Terminal 2 - Notification Service:**

```bash
pdm run python -m src.demo notification
```

**Terminal 3 - Analytics Service:**

```bash
pdm run python -m src.demo analytics
```

**Terminal 4 - Log Service:**

```bash
pdm run python -m src.demo logs
```

**Terminal 5 - Worker for Standard Orders:**

```bash
pdm run python -m src.demo worker standard W1
```

**Terminal 6 - Worker for Express Orders:**

```bash
pdm run python -m src.demo worker express W2
```

**Terminal 7 - Worker for International Orders:**

```bash
pdm run python -m src.demo worker international W3
```

**Terminal 8 - Publish Orders:**

```bash
pdm run python -m src.demo producer
```

Now watch the messages flow through the system! Each service will log what it receives.

### 4. Test RPC Pattern

```bash
pdm run python -m src.demo rpc-client
```

## 📋 Available Commands

```bash
# Infrastructure
pdm run python -m src.demo setup              # Setup exchanges/queues

# Producers
pdm run python -m src.demo producer           # Publish sample orders

# Consumers
pdm run python -m src.demo worker <type> [id] # Start worker (standard|express|international)
pdm run python -m src.demo notification       # Start notification service
pdm run python -m src.demo analytics          # Start analytics service
pdm run python -m src.demo logs               # Start log service

# RPC
pdm run python -m src.demo rpc-server         # Start inventory RPC server
pdm run python -m src.demo rpc-client         # Make RPC requests

# Help
pdm run python -m src.demo                    # Show help
```

## 🏗️ Architecture

```
┌─────────────┐
│  Producer   │
│  (Orders)   │
└──────┬──────┘
       │
       ▼
┌────────────────┐    routing_key     ┌──────────────────┐
│ Direct Exchange├───────────────────▶│ orders.standard  │──▶ Worker 1
│ (orders.direct)│                    └──────────────────┘
└────────────────┘                    ┌──────────────────┐
                 ├───────────────────▶│ orders.express   │──▶ Worker 2
                 │                    └──────────────────┘
                 │                    ┌──────────────────┐
                 └───────────────────▶│orders.international│▶ Worker 3
                                      └──────────────────┘
                                              │
                                              ▼ (on failure)
                                      ┌──────────────────┐
                                      │    Dead Letter   │
                                      │      Queue       │
                                      └──────────────────┘

┌─────────────┐
│   Workers   │─────┐
│ (Publish    │     │
│  Events)    │     ▼
└─────────────┘  ┌────────────────┐           ┌──────────────┐
                 │ Fanout Exchange├──────────▶│ notifications│
                 │ (events.fanout)│           └──────────────┘
                 └────────────────┘           ┌──────────────┐
                                  └───────────▶│  analytics   │
                                              └──────────────┘

                 ┌────────────────┐  order.#  ┌──────────────┐
                 │ Topic Exchange ├──────────▶│   logs.all   │
                 │  (logs.topic)  │           └──────────────┘
                 └────────────────┘

┌─────────────┐        request        ┌──────────────┐
│ RPC Client  │◀─────────────────────▶│  RPC Server  │
│             │        response       │  (Inventory) │
└─────────────┘                       └──────────────┘
```

## 📁 Project Structure

```
src/
├── config.py              # Configuration and constants
├── connection.py          # RabbitMQ connection management
├── exchanges.py           # Exchange/queue/binding setup
├── models.py              # Order and Event data models
├── demo.py                # Main demonstration script
├── producers/
│   ├── order_producer.py  # Publishes orders to direct exchange
│   └── event_producer.py  # Publishes events to fanout/topic exchanges
├── consumers/
│   ├── order_worker.py    # Processes orders (work queue)
│   ├── notification.py    # Fanout subscriber for notifications
│   ├── analytics.py       # Fanout subscriber for analytics
│   └── log_consumer.py    # Topic subscriber for logs
└── rpc/
    └── inventory_rpc.py   # RPC server and client for inventory
```

## 📖 Concept Explanations

### Direct Exchange

**What it does:** Routes messages to queues based on an exact match between the routing key and the queue's binding key.

**How it works in this demo:**

- Producer sends an order with routing key `order.standard`
- Direct exchange checks which queues are bound to `order.standard`
- Message is delivered only to the `orders.standard` queue

**Why use it:** When you need type-safe routing where each message type goes to a specific queue. Perfect for separating different kinds of work (standard vs express vs international orders).

**Real-world use:** Task distribution systems, job queues where different job types need different handlers.

### Fanout Exchange

**What it does:** Broadcasts every message it receives to ALL queues bound to it, ignoring routing keys entirely.

**How it works in this demo:**

- When a worker processes an order, it publishes an event to the fanout exchange
- Both the notification service AND analytics service receive the same event
- Each service processes it independently for different purposes

**Why use it:** Publishing/Subscribe pattern - when multiple services need to react to the same event independently. Like a notification system where one event triggers email, SMS, and push notifications.

**Real-world use:** Logging systems, real-time dashboards, notification services, cache invalidation.

### Topic Exchange

**What it does:** Routes messages based on pattern matching with wildcards:

- `*` (star) matches exactly one word
- `#` (hash) matches zero or more words

**How it works in this demo:**

- Messages published with keys like `order.created.standard` or `order.completed.express`
- Log queue bound with pattern `order.#` receives all messages starting with "order."
- You could bind another queue with `order.*.express` to get only express orders

**Why use it:** Flexible, hierarchical routing. When you need more complex filtering than direct exchange but more structure than fanout.

**Real-world use:** Log aggregation (error._, info._), geographic routing (us.east._, eu.west._), multi-tenant systems.

### Work Queues (Competing Consumers Pattern)

**What it does:** Multiple workers (consumers) pull tasks from the same queue. Each message goes to exactly ONE worker.

**How it works in this demo:**

- Messages sit in `orders.standard` queue
- You can start multiple workers (W1, W2, W3) all consuming from that queue
- RabbitMQ distributes messages among them (by default round-robin)
- If W1 is processing, the next message goes to W2

**Why use it:** Horizontal scaling - handle more work by adding more workers. Also provides redundancy - if one worker crashes, others continue.

**Real-world use:** Background job processing, video encoding, image resizing, email sending.

### QoS (Quality of Service) & Fair Dispatch

**What QoS is:** Quality of Service - settings that control how RabbitMQ delivers messages to consumers.

**prefetch_count explained:**

- `prefetch_count=1` means "only give me 1 message at a time"
- Worker must acknowledge (ack) the message before RabbitMQ sends another
- Without this, RabbitMQ might send 100 messages to one worker at once

**How it works in this demo:**

```python
channel.basic_qos(prefetch_count=1)  # Fair dispatch enabled
```

- Each worker gets one message
- Must complete it (ack) before getting another
- Fast workers process more messages than slow workers

**Why use it:**

- Without it: Round-robin might send 50 quick tasks to Worker1 and 50 slow tasks to Worker2
- With it: Fast workers automatically get more work - true load balancing
- Prevents one worker from hoarding all messages while being slow

**Real-world use:** Any multi-worker system where tasks have variable processing times.

### Message Acknowledgments (ack/nack)

**What they are:** Signals from consumer back to RabbitMQ about message processing status.

**Types:**

- **ack (acknowledge):** "I successfully processed this message, you can delete it"
- **nack (negative acknowledge):** "I couldn't process this, requeue it or send to DLX (Dead Letter Exchange)"
- **reject:** Similar to nack but for single messages

**How it works in this demo:**

```python
# Success
ch.basic_ack(delivery_tag=method.delivery_tag)

# Failure - send to DLX
ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
```

**Why use manual acks:**

- If worker crashes mid-processing, message is NOT lost
- RabbitMQ sees no ack arrived, redelivers message to another worker
- Auto-ack would delete message immediately = potential data loss

**Real-world use:** Any system where message loss is unacceptable - financial transactions, order processing, critical notifications.

### Dead Letter Exchange (DLX)

**What it is:** A "backup" exchange where failed messages automatically go.

**How it works in this demo:**

- Order queues configured with `x-dead-letter-exchange: orders.dlx`
- When worker sends nack with requeue=False, message goes to DLX
- DLX routes to Dead Letter Queue (DLQ) for manual inspection or retry

**Common triggers for DLX:**

1. Message rejected with nack(requeue=False)
2. Message TTL (Time To Live) expires
3. Queue reaches max-length limit

**Why use it:**

- Prevents message loss even when processing fails repeatedly
- Allows debugging - inspect failed messages
- Can implement retry logic - process DLQ messages later

**Real-world use:** Error handling, delayed retry queues, message timeouts, debugging production issues.

### Message Persistence

**What it means:** Messages and queues survive RabbitMQ broker restarts.

**Two parts:**

1. **Durable queues:** Queue definition survives restart
2. **Persistent messages:** Message data survives restart (delivery_mode=2)

**How it works in this demo:**

```python
# Durable queue
channel.queue_declare(queue='orders.standard', durable=True)

# Persistent message
properties = pika.BasicProperties(delivery_mode=2)
channel.basic_publish(..., properties=properties)
```

**Why use it:**

- Without it: Broker restart = all messages lost
- With it: Messages safely stored to disk

**Trade-off:** Persistence is slower (disk I/O) but safer. Use for critical messages.

**Real-world use:** Financial transactions, order confirmations, anything that can't be lost.

### RPC (Remote Procedure Call) Pattern

**What it is:** Synchronous request/response over asynchronous messaging.

**How it works in this demo:**

1. Client generates unique `correlation_id` for request
2. Client creates exclusive `reply_to` queue for responses
3. Client publishes request with both properties
4. Server processes request
5. Server publishes response to `reply_to` queue with same `correlation_id`
6. Client matches response using `correlation_id`

**Key components:**

- **correlation_id:** Unique ID to match request with response (like a tracking number)
- **reply_to:** Queue name where response should be sent
- **exclusive queue:** Auto-deleted callback queue for responses

**Why use it:**

- When you NEED a response (e.g., check inventory before processing order)
- Adds synchronous behavior on top of async messaging
- Client waits for response before continuing

**When NOT to use:** If you don't need a response, use regular pub/sub - RPC adds complexity and latency.

**Real-world use:** API gateways, microservice communication where response is required, distributed systems needing request/reply.

## 🧰 Development Commands

```bash
# Code quality
pdm run fmt        # Format code with ruff
pdm run chk        # Check code with ruff
pdm run typechk    # Type check with mypy
pdm run lint       # Run both checks
pdm run fint       # Format and lint
pdm run test       # Run tests

# RabbitMQ
pdm run rabbitup   # Start RabbitMQ
pdm run rabbitdown # Stop RabbitMQ
```

## 🐛 Troubleshooting

**Connection refused:**

- Ensure RabbitMQ is running: `docker ps | grep rabbitmq`
- Start it: `pdm run rabbitup`

**Messages not being processed:**

- Check if workers are running
- Verify queues exist in management UI (http://localhost:15672)
- Run `setup` command first

**Type errors:**

- Run `pdm run typechk` to see all type issues
- Ensure Python 3.13 is being used

## 📚 Learning Resources

- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- [Pika Documentation](https://pika.readthedocs.io/)
- [Exchange Types Explained](https://www.rabbitmq.com/tutorials/amqp-concepts.html#exchanges)

## 🎓 Learning Exercises

### 1. Understanding Exchange Types

**Exercise:** Observe how each exchange type behaves differently.

- Start the demo and watch how direct exchange routes orders to specific queues
- Notice how fanout exchange sends the SAME event to both notification and analytics
- See how topic exchange uses pattern matching with routing keys

**Key learning:** Each exchange type solves different routing needs - exact match, broadcast all, or pattern-based.

### 2. Message Reliability

**Challenge:** What happens if a worker crashes mid-processing?

- Start a worker and publish orders
- Kill the worker (Ctrl+C) while it's processing
- Notice RabbitMQ redelivers the message to another worker

**Key learning:** Manual acknowledgments prevent message loss. Messages aren't removed until successfully processed.

### 3. Load Balancing with QoS

**Experiment:** See fair dispatch in action.

- Start 2 workers for the same queue type
- Publish several orders
- Watch how messages are distributed

**Key learning:** With `prefetch_count=1`, faster workers automatically get more work. Without it, distribution would be strictly round-robin regardless of processing speed.

### 4. Dead Letter Queues

**Test:** Trigger message failures.

- Check the DLX/DLQ configuration in `exchanges.py`
- Modify a worker to intentionally fail (throw exception)
- Watch failed messages route to the dead letter queue
- Inspect them in the management UI

**Key learning:** DLX provides automatic failure handling - messages aren't lost, they're quarantined for inspection.

### 5. RPC Pattern

**Exploration:** Understand synchronous communication over async messaging.

- Start rpc-server, then run rpc-client
- Notice the client WAITS for responses
- Check how correlation_id matches requests to responses in the code

**Key learning:** RPC adds request/response semantics on top of message queues. Good for when you need an answer, but adds latency.

---

**Happy learning!** 🚀 Experiment, break things, and see how RabbitMQ handles it!
