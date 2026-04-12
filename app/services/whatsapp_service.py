"""WhatsApp delivery service.

Currently MOCKED: formats the digest and logs it instead of calling Meta Cloud API.

To enable real delivery:
1. Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env
2. Create and approve a message template named 'daily_news_digest' in Meta Business Suite
3. Replace the mock branch below with the httpx POST to Meta's graph API
"""
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import settings
from app.utils.formatting import format_digest

logger = logging.getLogger(__name__)

_USE_MOCK = not (settings.whatsapp_access_token and settings.whatsapp_phone_number_id)


async def send_message(phone_number: str, snippets: list[dict]) -> str:
    """Send the daily news digest to a WhatsApp number. Returns a message ID."""
    date_str = datetime.now(ZoneInfo("UTC")).strftime("%A, %B %-d")
    message = format_digest(snippets, date_str)

    if _USE_MOCK:
        mock_id = f"mock-wamid-{uuid.uuid4()}"
        logger.info(
            "[WHATSAPP MOCK] To: %s\nMessage ID: %s\n%s",
            phone_number,
            mock_id,
            message,
        )
        return mock_id

    # --- Real Meta Cloud API path ---
    url = f"https://graph.facebook.com/v19.0/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number.lstrip("+"),
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["messages"][0]["id"]
