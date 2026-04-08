import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field

ALL_TOPICS = ["finance", "geopolitics", "politics", "sports", "lifestyle"]


class SubscriptionCreate(BaseModel):
    delivery_time: time = Field(..., description="Local delivery time, e.g. 08:30")
    timezone: str = Field(..., description="IANA timezone name, e.g. Asia/Kolkata")
    topics: list[str] = Field(default=ALL_TOPICS)


class SubscriptionUpdate(BaseModel):
    delivery_time: time | None = None
    timezone: str | None = None
    topics: list[str] | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    delivery_time: time
    timezone: str
    topics: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
