import redis.asyncio as redis

from config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class CacheService:
    def __init__(self, client: redis.Redis = redis_client) -> None:
        self._client = client
        self._ttl = settings.cache_ttl

    async def get_url(self, short_id: str) -> str | None:
        return await self._client.get(f"url:{short_id}")

    async def set_url(self, short_id: str, original_url: str) -> None:
        await self._client.set(f"url:{short_id}", original_url, ex=self._ttl)

    async def get_clicks(self, short_id: str) -> int | None:
        val = await self._client.get(f"clicks:{short_id}")
        return int(val) if val is not None else None

    async def set_clicks(self, short_id: str, clicks: int) -> None:
        await self._client.set(f"clicks:{short_id}", clicks, ex=self._ttl)
