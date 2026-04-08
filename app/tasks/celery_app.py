from celery import Celery
from celery.schedules import timedelta

from app.config import settings

celery_app = Celery(
    "whatsapp_news",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.dispatch_tick",
        "app.tasks.send_news",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "dispatch-tick": {
            "task": "app.tasks.dispatch_tick.dispatch_tick",
            "schedule": timedelta(seconds=settings.dispatch_tick_interval_seconds),
        },
    },
)
