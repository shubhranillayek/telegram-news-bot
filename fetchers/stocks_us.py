import asyncio
import logging

import feedparser
import httpx

from config import NEWSAPI_KEY
from fetchers.errors import FetchError
from formatter import NewsItem

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWSAPI_QUERY = "US stock market NYSE NASDAQ"
YAHOO_US_RSS = "https://finance.yahoo.com/news/rssindex"

_HTTP_TIMEOUT = 8


async def _fetch_from_newsapi(count: int) -> list[NewsItem]:
    params = {
        "q": NEWSAPI_QUERY,
        "pageSize": count,
        "apiKey": NEWSAPI_KEY,
        "language": "en",
        "sortBy": "publishedAt",
    }

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(NEWSAPI_URL, params=params)
            resp.raise_for_status()
    except httpx.TimeoutException as exc:
        raise FetchError(f"Request timed out: {exc}", source="NewsAPI") from exc
    except httpx.HTTPStatusError as exc:
        raise FetchError(
            f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            source="NewsAPI",
        ) from exc
    except httpx.RequestError as exc:
        raise FetchError(f"Request error: {exc}", source="NewsAPI") from exc

    try:
        articles = resp.json()["articles"]
    except (KeyError, ValueError) as exc:
        raise FetchError(f"Unexpected response format: {exc}", source="NewsAPI") from exc

    return [
        NewsItem(
            headline=article.get("title") or "(no title)",
            url=article.get("url") or None,
            source="NewsAPI",
        )
        for article in articles[:count]
    ]


async def _fetch_from_yahoo_rss(count: int) -> list[NewsItem]:
    # feedparser.parse is blocking, so run it in a thread to avoid stalling the event loop
    loop = asyncio.get_event_loop()
    try:
        feed = await loop.run_in_executor(None, feedparser.parse, YAHOO_US_RSS)
    except Exception as exc:
        raise FetchError(f"Failed to parse RSS feed: {exc}", source="Yahoo Finance") from exc

    entries = feed.get("entries", [])
    if not entries:
        raise FetchError("RSS feed returned no entries.", source="Yahoo Finance")

    return [
        NewsItem(
            headline=entry.get("title") or "(no title)",
            url=entry.get("link") or None,
            source="Yahoo Finance",
        )
        for entry in entries[:count]
    ]


async def fetch(count: int) -> list[NewsItem]:
    try:
        return await _fetch_from_newsapi(count)
    except FetchError as primary_err:
        logger.warning("NewsAPI failed (%s); falling back to Yahoo Finance RSS.", primary_err)

    try:
        return await _fetch_from_yahoo_rss(count)
    except FetchError as fallback_err:
        raise FetchError(
            "All US stock news sources are unavailable.",
            source="stocks_us",
        ) from fallback_err
