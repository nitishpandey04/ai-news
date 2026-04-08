"""dispatch_tick: runs every N seconds (configured via DISPATCH_TICK_INTERVAL_SECONDS).

For each active subscription, checks if the delivery window is now and enqueues
send_news_to_user if not already sent today.
"""
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.delivery_log import DeliveryLog
from app.models.subscription import Subscription
from app.models.user import User
from app.tasks.celery_app import celery_app
from app.utils.timezone import is_due_within

logger = logging.getLogger(__name__)


async def _run_dispatch() -> None:
    async with AsyncSessionLocal() as db:
        subscriptions = await _get_active_subscriptions_with_users(db)
        window = settings.dispatch_tick_interval_seconds

        for sub, user in subscriptions:
            try:
                if not is_due_within(sub.delivery_time, sub.timezone, window):
                    continue
                if await _already_sent_today(db, user.id):
                    logger.debug("Already sent today, skipping user %s", user.id)
                    continue

                logger.info("Enqueuing delivery for user %s (phone: %s)", user.id, user.phone_number)
                from app.tasks.send_news import send_news_to_user  # avoid circular import at module level
                send_news_to_user.delay(str(user.id), str(sub.id))

            except Exception:
                logger.exception("Error processing subscription %s", sub.id)


async def _get_active_subscriptions_with_users(db: AsyncSession) -> list[tuple[Subscription, User]]:
    result = await db.execute(
        select(Subscription, User)
        .join(User, User.id == Subscription.user_id)
        .where(Subscription.is_active == True, User.is_active == True)  # noqa: E712
    )
    return result.all()


async def _already_sent_today(db: AsyncSession, user_id) -> bool:
    today = datetime.now(ZoneInfo("UTC")).date()
    result = await db.execute(
        select(DeliveryLog).where(
            DeliveryLog.user_id == user_id,
            DeliveryLog.status.in_(["sent", "pending"]),
        )
    )
    logs = result.scalars().all()
    return any(log.scheduled_for.date() == today for log in logs)


@celery_app.task(name="app.tasks.dispatch_tick.dispatch_tick")
def dispatch_tick() -> None:
    logger.info("Dispatch tick running")
    asyncio.run(_run_dispatch())
