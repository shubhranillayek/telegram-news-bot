import logging

import httpx

from fetchers.errors import FetchError
from formatter import NewsItem

logger = logging.getLogger(__name__)

COINGECKO_NEWS_URL = "https://api.coingecko.com/api/v3/news"


# no API key needed for CoinGecko public tier
async def fetch(count: int) -> list[NewsItem]:
    logger.info("Fetching %d crypto news items from CoinGecko", count)
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                COINGECKO_NEWS_URL,
                params={"per_page": count},
            )
            resp.raise_for_status()

            data = resp.json()
            articles = data["data"]

            items = [
                NewsItem(
                    headline=article["title"],
                    url=article.get("url"),
                    source="CoinGecko",
                )
                for article in articles[:count]
            ]
            logger.info("Fetched %d crypto news items", len(items))
            return items

    except httpx.TimeoutException as exc:
        raise FetchError(
            f"Request timed out after 8 seconds: {exc}", "CoinGecko"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise FetchError(
            f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}",
            "CoinGecko",
        ) from exc
    except (KeyError, ValueError) as exc:
        raise FetchError(
            f"Failed to parse response: {exc}", "CoinGecko"
        ) from exc
