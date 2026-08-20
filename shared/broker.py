import json
import asyncio
from aio_pika import connect_robust, Message, ExchangeType

import os
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")

async def get_connection():
    """Устанавливает соединение с RabbitMQ."""
    return await connect_robust(RABBITMQ_URL)

async def publish_task(task: dict):
    """Публикует задание в очередь 'tasks'."""
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            Message(json.dumps(task).encode(), delivery_mode=2),  # persistent
            routing_key="tasks",
        )

async def publish_result(result: dict):
    """Публикует результат в очередь 'results'."""
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            Message(json.dumps(result).encode(), delivery_mode=2),
            routing_key="results",
        )

async def declare_queues():
    """Создаёт очереди (вызывается при старте)."""
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("tasks", durable=True)
        await channel.declare_queue("results", durable=True)
