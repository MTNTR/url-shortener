from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Link


class LinkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, short_id: str, original_url: str) -> Link:
        link = Link(short_id=short_id, original_url=original_url)
        self._session.add(link)
        await self._session.commit()
        await self._session.refresh(link)
        return link

    async def get_by_short_id(self, short_id: str) -> Link | None:
        stmt = select(Link).where(Link.short_id == short_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_clicks(self, short_id: str, count: int = 1) -> None:
        link = await self.get_by_short_id(short_id)
        if link:
            link.clicks += count
            await self._session.commit()

    async def get_by_original_url(self, original_url: str) -> Link | None:
        stmt = select(Link).where(Link.original_url == original_url)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


