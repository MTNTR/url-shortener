import json

import aio_pika

from config import settings

QUEUE_NAME = "click_events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None


async def connect_broker() -> None:
    global _connection, _channel
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()
    await _channel.declare_queue(QUEUE_NAME, durable=True)


async def disconnect_broker() -> None:
    global _connection, _channel
    if _connection:
        await _connection.close()
    _connection = None
    _channel = None


async def publish_click(short_id: str) -> None:
    if _channel is None:
        return
    body = json.dumps({"short_id": short_id}).encode()
    await _channel.default_exchange.publish(
        aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=QUEUE_NAME,
    )
