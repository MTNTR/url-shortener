from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from database import engine
from models import Base
from broker import connect_broker, disconnect_broker
from router import router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await connect_broker()
    yield
    await disconnect_broker()
    await engine.dispose()


app = FastAPI(title="URL Shortener", lifespan=lifespan)
app.include_router(router)
