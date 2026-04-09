from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repository import LinkRepository
from cache import CacheService
from service import LinkService
from schemas import ShortenRequest, ShortenResponse, StatsResponse

router = APIRouter()


def get_link_service(session: AsyncSession = Depends(get_session)) -> LinkService:
    return LinkService(repo=LinkRepository(session), cache=CacheService())


@router.post("/shorten", response_model=ShortenResponse)
async def shorten(body: ShortenRequest, svc: LinkService = Depends(get_link_service)) -> ShortenResponse:
    return await svc.shorten(str(body.url))


@router.get("/stats/{short_id}", response_model=StatsResponse)
async def stats(short_id: str, svc: LinkService = Depends(get_link_service)) -> StatsResponse:
    result = await svc.get_stats(short_id)
    if not result:
        raise HTTPException(status_code=404, detail="Link not found")
    return result


@router.get("/{short_id}")
async def redirect(short_id: str, svc: LinkService = Depends(get_link_service)) -> RedirectResponse:
    url = await svc.resolve(short_id)
    if not url:
        raise HTTPException(status_code=404, detail="Link not found")
    return RedirectResponse(url=url, status_code=307)
