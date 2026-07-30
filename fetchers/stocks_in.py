import asyncio
import logging

import feedparser
import httpx

from config import NEWSAPI_KEY
from fetchers.errors import FetchError
from formatter import NewsItem

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"
YAHOO_IN_RSS = "https://finance.yahoo.com/rss/headline?s=^BSESN"

_NEWSAPI_QUERY = "BSE OR NSE OR Sensex OR Nifty OR Indian stock market"


async def _fetch_from_newsapi(count: int) -> list[NewsItem]:
    logger.info("Fetching %d Indian stock news items from NewsAPI", count)
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                NEWSAPI_URL,
                params={
                    "q": _NEWSAPI_QUERY,
                    "pageSize": count,
                    "apiKey": NEWSAPI_KEY,
                    "language": "en",
                    "sortBy": "publishedAt",
                },
            )
            resp.raise_for_status()

            data = resp.json()
            articles = data["articles"]

            items = [
                NewsItem(
                    headline=article["title"],
                    url=article.get("url"),
                    source="NewsAPI",
                )
                for article in articles[:count]
            ]
            logger.info("Fetched %d Indian stock news items from NewsAPI", len(items))
            return items

    except httpx.TimeoutException as exc:
        raise FetchError(
            f"Request timed out after 8 seconds: {exc}", "NewsAPI"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise FetchError(
            f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}",
            "NewsAPI",
        ) from exc
    except (KeyError, ValueError) as exc:
        raise FetchError(
            f"Failed to parse response: {exc}", "NewsAPI"
        ) from exc


async def _fetch_from_yahoo_rss(count: int) -> list[NewsItem]:
    logger.info(
        "Falling back to Yahoo Finance RSS for Indian stock news (%d items)", count
    )
    # feedparser.parse is blocking, so run it in a thread to avoid stalling the event loop
    loop = asyncio.get_event_loop()
    try:
        feed = await loop.run_in_executor(None, feedparser.parse, YAHOO_IN_RSS)

        if feed.bozo and not feed.entries:
            raise FetchError(
                f"Failed to parse Yahoo Finance RSS feed: {feed.bozo_exception}",
                "Yahoo Finance",
            )

        items = [
            NewsItem(
                headline=entry.title,
                url=entry.link,
                source="Yahoo Finance",
            )
            for entry in feed.entries[:count]
        ]

        if not items:
            raise FetchError(
                "Yahoo Finance RSS feed returned no entries", "Yahoo Finance"
            )

        logger.info(
            "Fetched %d Indian stock news items from Yahoo Finance RSS", len(items)
        )
        return items

    except FetchError:
        raise
    except Exception as exc:
        raise FetchError(
            f"Unexpected error reading Yahoo Finance RSS: {exc}", "Yahoo Finance"
        ) from exc


async def fetch(count: int) -> list[NewsItem]:
    try:
        return await _fetch_from_newsapi(count)
    except FetchError as primary_err:
        logger.warning(
            "NewsAPI fetch failed (%s); falling back to Yahoo Finance RSS",
            primary_err,
        )

    try:
        return await _fetch_from_yahoo_rss(count)
    except FetchError:
        logger.error(
            "Both NewsAPI and Yahoo Finance RSS failed for Indian stock news"
        )
        raise
