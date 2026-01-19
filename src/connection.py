"""RabbitMQ connection utilities."""

import pika
from pika.adapters.blocking_connection import BlockingConnection

from . import config


def create_connection() -> BlockingConnection:
    """
    Create a RabbitMQ connection.

    Returns:
        A blocking connection to RabbitMQ.
    """
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)
