import logging

import redis.asyncio as aioredis
from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal
from app.routers import news, subscriptions, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="WhatsApp News Delivery Service", version="0.1.0")

app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(news.router)


@app.get("/health", tags=["health"])
async def health():
    db_ok = False
    redis_ok = False

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "version": "0.1.0",
    }
