import string
import hashlib

from config import settings
from repository import LinkRepository
from cache import CacheService
from broker import publish_click
from schemas import ShortenResponse, StatsResponse
from logger import get_logger

ALPHABET = string.digits + string.ascii_letters
logger = get_logger(__name__)


def generate_short_id(url: str, record_id: int) -> str:
    raw = f"{url}:{record_id}"
    hash_bytes = hashlib.sha256(raw.encode()).digest()
    num = int.from_bytes(hash_bytes[:8], "big")
    result: list[str] = []
    for _ in range(settings.short_id_length):
        num, remainder = divmod(num, 62)
        result.append(ALPHABET[remainder])
    return "".join(result)


class LinkService:
    def __init__(self, repo: LinkRepository, cache: CacheService) -> None:
        self._repo = repo
        self._cache = cache

    async def shorten(self, original_url: str) -> ShortenResponse:
        existing = await self._repo.get_by_original_url(original_url)
        if existing:
            logger.info(f"Found existing short_id={existing.short_id} for url={original_url}")
            return ShortenResponse(
                short_id=existing.short_id,
                short_url=f"{settings.base_url}/{existing.short_id}",
            )
        link = await self._repo.create(short_id="tmp", original_url=original_url)
        short_id = generate_short_id(original_url, link.id)
        link.short_id = short_id
        logger.info(f"Created short_id={short_id} for url={original_url}")
        await self._repo._session.commit()
        await self._cache.set_url(short_id, original_url)
        return ShortenResponse(
            short_id=short_id,
            short_url=f"{settings.base_url}/{short_id}",
        )

    async def resolve(self, short_id: str) -> str | None:
        cached = await self._cache.get_url(short_id)
        if cached:
            await publish_click(short_id)
            return cached
        link = await self._repo.get_by_short_id(short_id)
        logger.info(f"Resolved short_id={short_id}")
        if not link:
            return None
        await self._cache.set_url(short_id, link.original_url)
        await publish_click(short_id)
        return link.original_url

    async def get_stats(self, short_id: str) -> StatsResponse | None:
        link = await self._repo.get_by_short_id(short_id)
        if not link:
            return None
        return StatsResponse(
            short_id=link.short_id,
            original_url=link.original_url,
            clicks=link.clicks,
        )
