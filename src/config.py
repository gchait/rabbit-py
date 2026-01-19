"""RabbitMQ configuration."""

from typing import Final

# Connection
RABBITMQ_HOST: Final[str] = "localhost"
RABBITMQ_PORT: Final[int] = 5672
RABBITMQ_USER: Final[str] = "guy"
RABBITMQ_PASSWORD: Final[str] = "yug"

# Exchanges
EXCHANGE_ORDERS: Final[str] = "orders.direct"
EXCHANGE_EVENTS: Final[str] = "events.fanout"
EXCHANGE_LOGS: Final[str] = "logs.topic"
EXCHANGE_DLX: Final[str] = "orders.dlx"

# Queues
QUEUE_ORDERS: Final[str] = "orders"
QUEUE_NOTIFICATIONS: Final[str] = "notifications"
QUEUE_ANALYTICS: Final[str] = "analytics"
QUEUE_LOGS: Final[str] = "logs.all"
QUEUE_RPC: Final[str] = "rpc.inventory"
QUEUE_DLQ: Final[str] = "orders.failed"
