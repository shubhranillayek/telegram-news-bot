import asyncio
import logging

import feedparser

from fetchers.errors import FetchError
from formatter import NewsItem

logger = logging.getLogger(__name__)

# Crypto news comes from free RSS feeds — no API key needed.
# (CoinGecko's /news endpoint moved to its paid Pro tier and returns
# 401 for keyless requests, so it is no longer used here.)
COINDESK_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/"
COINTELEGRAPH_RSS = "https://cointelegraph.com/rss"

_RSS_SOURCES = [
    ("CoinDesk", COINDESK_RSS),
    ("CoinTelegraph", COINTELEGRAPH_RSS),
]


async def _fetch_from_rss(source: str, url: str, count: int) -> list[NewsItem]:
    logger.info("Fetching %d crypto news items from %s RSS", count, source)
    # feedparser.parse is blocking, so run it in a thread to avoid stalling the event loop
    loop = asyncio.get_event_loop()
    try:
        feed = await loop.run_in_executor(None, feedparser.parse, url)
    except Exception as exc:
        raise FetchError(
            f"Failed to parse {source} RSS feed: {exc}", source=source
        ) from exc

    entries = feed.get("entries", [])
    if not entries:
        raise FetchError(f"{source} RSS feed returned no entries.", source=source)

    items = [
        NewsItem(
            headline=entry.get("title") or "(no title)",
            url=entry.get("link") or None,
            source=source,
        )
        for entry in entries[:count]
    ]
    logger.info("Fetched %d crypto news items from %s", len(items), source)
    return items


async def fetch(count: int) -> list[NewsItem]:
    last_err: FetchError | None = None
    for source, url in _RSS_SOURCES:
        try:
            return await _fetch_from_rss(source, url, count)
        except FetchError as err:
            last_err = err
            logger.warning("%s RSS failed (%s); trying next source.", source, err)

    raise FetchError(
        "All crypto news sources are unavailable.",
        source="crypto",
    ) from last_err
