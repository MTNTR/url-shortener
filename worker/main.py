import asyncio
import json

import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from models import Link
from logger import get_logger

logger = get_logger("worker")

QUEUE_NAME = "click_events"

engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=5)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        data = json.loads(message.body.decode())
        short_id = data["short_id"]
        async with async_session() as session:
            stmt = select(Link).where(Link.short_id == short_id)
            result = await session.execute(stmt)
            link = result.scalar_one_or_none()
            if link:
                link.clicks += 1
                logger.info(f"Click recorded for short_id={short_id}, total={link.clicks}")
                await session.commit()


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=100)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.consume(process_message)
    logger.info("Worker started, consuming click_events")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
