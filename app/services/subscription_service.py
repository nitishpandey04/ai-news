import uuid
from datetime import time

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription


async def get_active_subscription(db: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def create_or_replace_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    delivery_time: time,
    timezone: str,
    topics: list[str],
) -> Subscription:
    # Deactivate any existing active subscription
    await db.execute(
        update(Subscription)
        .where(Subscription.user_id == user_id, Subscription.is_active == True)  # noqa: E712
        .values(is_active=False)
    )
    sub = Subscription(
        user_id=user_id,
        delivery_time=delivery_time,
        timezone=timezone,
        topics=topics,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def update_subscription(
    db: AsyncSession,
    subscription: Subscription,
    delivery_time: time | None,
    timezone: str | None,
    topics: list[str] | None,
) -> Subscription:
    if delivery_time is not None:
        subscription.delivery_time = delivery_time
    if timezone is not None:
        subscription.timezone = timezone
    if topics is not None:
        subscription.topics = topics
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def deactivate_subscription(db: AsyncSession, subscription: Subscription) -> None:
    subscription.is_active = False
    await db.commit()


async def get_all_active_subscriptions(db: AsyncSession) -> list[Subscription]:
    result = await db.execute(
        select(Subscription).where(Subscription.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())
