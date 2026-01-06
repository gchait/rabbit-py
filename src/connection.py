"""RabbitMQ connection management utilities."""

from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from . import config


def create_connection() -> BlockingConnection:
    """
    Create a new RabbitMQ connection.

    Returns:
        A blocking connection to RabbitMQ.
    """
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        virtual_host=config.RABBITMQ_VHOST,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


def create_channel(connection: BlockingConnection) -> BlockingChannel:
    """
    Create a new channel from an existing connection.

    Args:
        connection: An active RabbitMQ connection.

    Returns:
        A new channel for the connection.
    """
    return connection.channel()


def with_connection(func: Callable[[BlockingChannel], None]) -> None:
    """
    Execute a function with a RabbitMQ connection and channel.

    This context manager handles connection lifecycle automatically.

    Args:
        func: Function to execute with the channel as an argument.
    """
    connection = create_connection()
    try:
        channel = create_channel(connection)
        func(channel)
    finally:
        connection.close()
