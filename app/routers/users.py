import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subscription import SubscriptionResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import subscription_service, user_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await user_service.get_user_by_phone(db, body.phone_number)
    if existing:
        raise HTTPException(status_code=409, detail="Phone number already registered.")
    return await user_service.create_user(db, body.phone_number, body.display_name)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await user_service.deactivate_user(db, user)
