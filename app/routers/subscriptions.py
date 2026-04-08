import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from app.services import subscription_service, user_service

router = APIRouter(prefix="/api/v1/users", tags=["subscriptions"])


async def _require_user(user_id: uuid.UUID, db: AsyncSession):
    user = await user_service.get_user(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/{user_id}/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    user_id: uuid.UUID,
    body: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    await _require_user(user_id, db)
    sub = await subscription_service.create_or_replace_subscription(
        db, user_id, body.delivery_time, body.timezone, body.topics
    )
    return sub


@router.put("/{user_id}/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    user_id: uuid.UUID,
    body: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
):
    await _require_user(user_id, db)
    sub = await subscription_service.get_active_subscription(db, user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found.")
    return await subscription_service.update_subscription(
        db, sub, body.delivery_time, body.timezone, body.topics
    )


@router.delete("/{user_id}/subscription", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await _require_user(user_id, db)
    sub = await subscription_service.get_active_subscription(db, user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found.")
    await subscription_service.deactivate_subscription(db, sub)
