"""Configuration settings for RabbitMQ connection and exchanges."""

from typing import Final

# RabbitMQ Connection Settings
RABBITMQ_HOST: Final[str] = "localhost"
RABBITMQ_PORT: Final[int] = 5672
RABBITMQ_USER: Final[str] = "guy"
RABBITMQ_PASSWORD: Final[str] = "yug"
RABBITMQ_VHOST: Final[str] = "/"

# Exchange Names
EXCHANGE_ORDERS: Final[str] = "orders.direct"
EXCHANGE_EVENTS: Final[str] = "events.fanout"
EXCHANGE_LOGS: Final[str] = "logs.topic"
EXCHANGE_DLX: Final[str] = "orders.dlx"

# Queue Names
QUEUE_STANDARD_ORDERS: Final[str] = "orders.standard"
QUEUE_EXPRESS_ORDERS: Final[str] = "orders.express"
QUEUE_INTERNATIONAL_ORDERS: Final[str] = "orders.international"
QUEUE_NOTIFICATIONS: Final[str] = "notifications"
QUEUE_ANALYTICS: Final[str] = "analytics"
QUEUE_LOGS: Final[str] = "logs.all"
QUEUE_DLQ: Final[str] = "orders.failed"
QUEUE_INVENTORY_RPC: Final[str] = "rpc.inventory"

# Routing Keys
ROUTING_KEY_STANDARD: Final[str] = "order.standard"
ROUTING_KEY_EXPRESS: Final[str] = "order.express"
ROUTING_KEY_INTERNATIONAL: Final[str] = "order.international"

# Message TTL (milliseconds)
MESSAGE_TTL: Final[int] = 60000  # 1 minute

# Worker Settings
PREFETCH_COUNT: Final[int] = 1  # Fair dispatch - one message at a time
