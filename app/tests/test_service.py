from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from service import LinkService, generate_short_id
from models import Link


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock, mock_cache: AsyncMock) -> LinkService:
    return LinkService(repo=mock_repo, cache=mock_cache)


def test_generate_short_id_is_stable() -> None:
    a = generate_short_id("https://example.com", 1)
    b = generate_short_id("https://example.com", 1)
    assert a == b


def test_generate_short_id_differs_by_id() -> None:
    a = generate_short_id("https://example.com", 1)
    b = generate_short_id("https://example.com", 2)
    assert a != b


@pytest.mark.asyncio
async def test_shorten_creates_link(svc: LinkService, mock_repo: AsyncMock, mock_cache: AsyncMock) -> None:
    mock_repo.get_by_original_url.return_value = None
    fake_link = MagicMock(spec=Link)
    fake_link.id = 1000
    fake_link.original_url = "https://example.com"
    mock_repo.create.return_value = fake_link
    mock_repo._session = AsyncMock()

    result = await svc.shorten("https://example.com")

    mock_repo.create.assert_called_once()
    mock_cache.set_url.assert_called_once()
    assert result.short_id is not None


@pytest.mark.asyncio
async def test_shorten_returns_existing(svc: LinkService, mock_repo: AsyncMock, mock_cache: AsyncMock) -> None:
    fake_link = MagicMock(spec=Link)
    fake_link.short_id = "abc1234"
    fake_link.original_url = "https://example.com"
    mock_repo.get_by_original_url.return_value = fake_link

    result = await svc.shorten("https://example.com")

    mock_repo.create.assert_not_called()
    assert result.short_id == "abc1234"


@pytest.mark.asyncio
async def test_resolve_returns_cached_url(svc: LinkService, mock_cache: AsyncMock) -> None:
    mock_cache.get_url.return_value = "https://example.com"

    with patch("service.publish_click", new_callable=AsyncMock):
        result = await svc.resolve("abc1234")

    assert result == "https://example.com"
    mock_cache.get_url.assert_called_once_with("abc1234")


@pytest.mark.asyncio
async def test_resolve_falls_back_to_db(svc: LinkService, mock_repo: AsyncMock, mock_cache: AsyncMock) -> None:
    mock_cache.get_url.return_value = None
    fake_link = MagicMock(spec=Link)
    fake_link.original_url = "https://example.com"
    mock_repo.get_by_short_id.return_value = fake_link

    with patch("service.publish_click", new_callable=AsyncMock):
        result = await svc.resolve("abc1234")

    assert result == "https://example.com"
    mock_repo.get_by_short_id.assert_called_once_with("abc1234")
    mock_cache.set_url.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_returns_none_for_missing(svc: LinkService, mock_repo: AsyncMock, mock_cache: AsyncMock) -> None:
    mock_cache.get_url.return_value = None
    mock_repo.get_by_short_id.return_value = None

    with patch("service.publish_click", new_callable=AsyncMock):
        result = await svc.resolve("missing")

    assert result is None


@pytest.mark.asyncio
async def test_get_stats(svc: LinkService, mock_repo: AsyncMock) -> None:
    fake_link = MagicMock(spec=Link)
    fake_link.short_id = "abc1234"
    fake_link.original_url = "https://example.com"
    fake_link.clicks = 42
    mock_repo.get_by_short_id.return_value = fake_link

    result = await svc.get_stats("abc1234")

    assert result is not None
    assert result.clicks == 42
    assert result.original_url == "https://example.com"