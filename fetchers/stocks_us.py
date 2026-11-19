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
CNBC_US_RSS = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839135"

_RSS_FALLBACKS = [
    ("Yahoo Finance", YAHOO_US_RSS),
    ("CNBC", CNBC_US_RSS),
]

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


async def _fetch_from_rss(source: str, url: str, count: int) -> list[NewsItem]:
    # feedparser.parse is blocking, so run it in a thread to avoid stalling the event loop
    loop = asyncio.get_event_loop()
    try:
        feed = await loop.run_in_executor(None, feedparser.parse, url)
    except Exception as exc:
        raise FetchError(f"Failed to parse RSS feed: {exc}", source=source) from exc

    entries = feed.get("entries", [])
    if not entries:
        raise FetchError("RSS feed returned no entries.", source=source)

    return [
        NewsItem(
            headline=entry.get("title") or "(no title)",
            url=entry.get("link") or None,
            source=source,
        )
        for entry in entries[:count]
    ]


async def fetch(count: int) -> list[NewsItem]:
    try:
        return await _fetch_from_newsapi(count)
    except FetchError as primary_err:
        logger.warning("NewsAPI failed (%s); falling back to RSS feeds.", primary_err)

    last_err: FetchError | None = None
    for source, url in _RSS_FALLBACKS:
        try:
            return await _fetch_from_rss(source, url, count)
        except FetchError as fallback_err:
            last_err = fallback_err
            logger.warning("%s RSS failed (%s); trying next source.", source, fallback_err)

    raise FetchError(
        "All US stock news sources are unavailable.",
        source="stocks_us",
    ) from last_err
