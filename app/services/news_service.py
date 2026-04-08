import asyncio
import json
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

MOCK_NEWS: list[dict] = [
    {
        "topic": "finance",
        "headline": "Markets rally on Fed rate-hold comments",
        "summary": "The S&P 500 climbed 1.4% after Fed officials signalled no imminent rate changes, easing recession fears.",
    },
    {
        "topic": "geopolitics",
        "headline": "Peace summit talks resume in Vienna",
        "summary": "Delegates from 14 nations gathered for a third round of negotiations, with mediators cautiously optimistic.",
    },
    {
        "topic": "politics",
        "headline": "Senate passes landmark infrastructure amendment",
        "summary": "A bipartisan bill passed 67-33, allocating $120 billion for roads, bridges, and rural broadband.",
    },
    {
        "topic": "sports",
        "headline": "City FC secures Champions League final berth",
        "summary": "A stoppage-time winner sent City FC through on aggregate, setting up a final against rivals United.",
    },
    {
        "topic": "lifestyle",
        "headline": "Mediterranean diet linked to longer life in 20-year study",
        "summary": "Researchers found a 25% reduction in all-cause mortality among consistent adherents of the diet.",
    },
]


def _redis_key(for_date: date) -> str:
    return f"news:{for_date.isoformat()}"


async def fetch_news_snippets() -> list[dict]:
    """Return 5 mock news snippets. Replace this function body to integrate a real API."""
    await asyncio.sleep(0)  # simulate async I/O
    return MOCK_NEWS


async def get_news_for_today() -> list[dict]:
    """Return today's news, using Redis cache when available."""
    today = datetime.now(ZoneInfo("UTC")).date()
    cache_key = _redis_key(today)

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        cached = await redis.get(cache_key)
        if cached:
            logger.debug("News cache hit for %s", today)
            return json.loads(cached)

        snippets = await fetch_news_snippets()
        await redis.set(cache_key, json.dumps(snippets), ex=23 * 3600)
        logger.info("Fetched and cached news for %s", today)
        return snippets
    except Exception:
        logger.warning("Redis unavailable, fetching news without cache")
        return await fetch_news_snippets()
    finally:
        await redis.aclose()
