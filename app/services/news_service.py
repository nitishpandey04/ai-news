import asyncio
import json
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

TOPICS = ["finance", "geopolitics", "politics", "sports", "lifestyle"]

TOPIC_PROMPTS = {
    "finance": "What is the single most important finance or markets news story today? Reply with exactly two lines: first line is the headline, second line is a one-sentence summary.",
    "geopolitics": "What is the single most important geopolitics or international relations news story today? Reply with exactly two lines: first line is the headline, second line is a one-sentence summary.",
    "politics": "What is the single most important politics or government news story today? Reply with exactly two lines: first line is the headline, second line is a one-sentence summary.",
    "sports": "What is the single most important sports news story today? Reply with exactly two lines: first line is the headline, second line is a one-sentence summary.",
    "lifestyle": "What is the single most important lifestyle, health, or culture news story today? Reply with exactly two lines: first line is the headline, second line is a one-sentence summary.",
}


def _redis_key(for_date: date) -> str:
    return f"news:{for_date.isoformat()}"


async def _fetch_topic(client: httpx.AsyncClient, topic: str) -> dict:
    prompt = TOPIC_PROMPTS[topic]
    resp = await client.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    headline = lines[0] if len(lines) > 0 else f"Top {topic} news"
    summary = lines[1] if len(lines) > 1 else headline
    return {"topic": topic, "headline": headline, "summary": summary}


async def fetch_news_snippets() -> list[dict]:
    """Fetch one top news snippet per topic from Perplexity in parallel."""
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_fetch_topic(client, topic) for topic in TOPICS],
            return_exceptions=True,
        )

    snippets = []
    for topic, result in zip(TOPICS, results):
        if isinstance(result, Exception):
            logger.error("Failed to fetch %s news: %s", topic, result)
            snippets.append({"topic": topic, "headline": f"No {topic} news available", "summary": ""})
        else:
            snippets.append(result)
    return snippets


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
