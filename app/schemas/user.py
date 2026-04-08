import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    phone_number: str = Field(..., description="E.164 format, e.g. +14155552671")
    display_name: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    phone_number: str
    display_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
