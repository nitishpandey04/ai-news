from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def next_delivery_utc(delivery_time: time, tz_name: str) -> datetime:
    """Return the next UTC datetime for a given local delivery_time + IANA timezone.

    If today's slot has already passed, returns tomorrow's slot.
    """
    tz = ZoneInfo(tz_name)
    today: date = datetime.now(tz).date()
    local_dt = datetime.combine(today, delivery_time, tzinfo=tz)
    if local_dt < datetime.now(tz):
        local_dt = datetime.combine(today + timedelta(days=1), delivery_time, tzinfo=tz)
    return local_dt.astimezone(ZoneInfo("UTC"))


def is_due_within(delivery_time: time, tz_name: str, window_seconds: int) -> bool:
    """Return True if next delivery falls within [now, now + window_seconds)."""
    now_utc = datetime.now(ZoneInfo("UTC"))
    next_utc = next_delivery_utc(delivery_time, tz_name)
    delta = (next_utc - now_utc).total_seconds()
    return 0 <= delta < window_seconds
