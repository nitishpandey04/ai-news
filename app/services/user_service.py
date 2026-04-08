import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def create_user(db: AsyncSession, phone_number: str, display_name: str | None) -> User:
    user = User(phone_number=phone_number, display_name=display_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone_number: str) -> User | None:
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    return result.scalar_one_or_none()


async def deactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user
