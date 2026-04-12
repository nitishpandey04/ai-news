"""send_news_to_user: per-user Celery task that fetches news and delivers via WhatsApp."""
import asyncio
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.config import settings
from app.models.delivery_log import DeliveryLog
from app.models.news_cache import NewsCache
from app.models.subscription import Subscription
from app.models.user import User
from app.services import news_service, whatsapp_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _deliver(user_id: str, subscription_id: str) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        user = await db.get(User, uuid.UUID(user_id))
        sub = await db.get(Subscription, uuid.UUID(subscription_id))

        if not user or not sub:
            logger.error("User or subscription not found: %s / %s", user_id, subscription_id)
            return

        now_utc = datetime.now(ZoneInfo("UTC"))

        # Create a pending delivery log
        log = DeliveryLog(
            user_id=user.id,
            subscription_id=sub.id,
            scheduled_for=now_utc,
            status="pending",
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        try:
            snippets = await news_service.get_news_for_today()

            # Persist news cache reference if available
            from sqlalchemy import select
            nc_result = await db.execute(
                select(NewsCache).where(NewsCache.fetch_date == now_utc.date())
            )
            news_cache = nc_result.scalar_one_or_none()
            if news_cache:
                log.news_cache_id = news_cache.id

            wamid = await whatsapp_service.send_message(user.phone_number, snippets)

            log.status = "sent"
            log.sent_at = datetime.now(ZoneInfo("UTC"))
            log.whatsapp_message_id = wamid
            await db.commit()
            logger.info("Delivered news to %s (wamid: %s)", user.phone_number, wamid)

        except Exception as exc:
            log.status = "failed"
            log.error_detail = str(exc)
            log.retry_count += 1
            await db.commit()
            raise


@celery_app.task(
    name="app.tasks.send_news.send_news_to_user",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_news_to_user(self, user_id: str, subscription_id: str) -> None:
    try:
        asyncio.run(_deliver(user_id, subscription_id))
    except Exception as exc:
        logger.warning("Delivery failed for user %s: %s. Retry %d/3", user_id, exc, self.request.retries)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
