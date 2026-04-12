"""WhatsApp news delivery — minimal version.

A single-file FastAPI app that:
  - stores a list of phone numbers and a delivery time in data.json
  - fetches today's top news per topic from Perplexity
  - sends a digest to all stored numbers via Meta WhatsApp Cloud API

There is no scheduler. Hit POST /send to deliver right now.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------- Config ----------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    perplexity_api_key: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""


settings = Settings()

DATA_FILE = Path("data.json")
DEFAULT_DATA = {"numbers": []}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


# ---------- Storage ----------
def load_data() -> dict:
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))
    return json.loads(DATA_FILE.read_text())


def save_data(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2))


# ---------- News (Perplexity) ----------
TOPICS = ["finance", "geopolitics", "politics", "sports", "lifestyle"]


async def _fetch_topic(client: httpx.AsyncClient, topic: str) -> dict:
    prompt = (
        f"What is the single most important {topic} news story today? "
        "Reply with exactly two lines: line 1 = headline, line 2 = one-sentence summary."
    )
    resp = await client.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return {
        "topic": topic,
        "headline": lines[0] if lines else f"Top {topic} news",
        "summary": lines[1] if len(lines) > 1 else "",
    }


async def fetch_news() -> list[dict]:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_fetch_topic(client, t) for t in TOPICS],
            return_exceptions=True,
        )
    snippets = []
    for topic, r in zip(TOPICS, results):
        if isinstance(r, Exception):
            logger.error("Failed to fetch %s news: %s", topic, r)
            snippets.append({"topic": topic, "headline": f"No {topic} news", "summary": ""})
        else:
            snippets.append(r)
    return snippets


# ---------- Formatting ----------
TOPIC_EMOJI = {
    "finance": "💰",
    "geopolitics": "🌍",
    "politics": "🏛️",
    "sports": "⚽",
    "lifestyle": "✨",
}


def format_digest(snippets: list[dict]) -> str:
    date_str = datetime.now().strftime("%A, %B %-d")
    lines = [f"📰 *Your Daily News Digest — {date_str}*", ""]
    for s in snippets:
        emoji = TOPIC_EMOJI.get(s["topic"], "•")
        lines.append(f"{emoji} *{s['topic'].capitalize()}*: {s['headline']}")
        if s["summary"]:
            lines.append(f"   {s['summary']}")
        lines.append("")
    return "\n".join(lines)


# ---------- WhatsApp ----------
async def send_whatsapp(phone_number: str, message: str) -> str:
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


# ---------- API ----------
app = FastAPI(title="WhatsApp News (Minimal)", version="1.0.0")


class NumberIn(BaseModel):
    phone_number: str = Field(..., description="E.164, e.g. +919818659521")
    name: str | None = None


def _normalize(phone: str) -> str:
    return phone if phone.startswith("+") else "+" + phone


@app.get("/numbers")
def list_numbers():
    return load_data()["numbers"]


@app.post("/numbers", status_code=201)
def add_number(body: NumberIn):
    data = load_data()
    phone = _normalize(body.phone_number)
    if any(n["phone_number"] == phone for n in data["numbers"]):
        raise HTTPException(409, "Phone number already exists")
    entry = {"phone_number": phone, "name": body.name}
    data["numbers"].append(entry)
    save_data(data)
    return entry


@app.delete("/numbers", status_code=204)
def remove_number(phone_number: str):
    data = load_data()
    phone = _normalize(phone_number)
    before = len(data["numbers"])
    data["numbers"] = [n for n in data["numbers"] if n["phone_number"] != phone]
    if len(data["numbers"]) == before:
        raise HTTPException(404, "Phone number not found")
    save_data(data)


@app.post("/send")
async def send_now():
    """Fetch fresh news and deliver to all stored numbers immediately."""
    data = load_data()
    if not data["numbers"]:
        raise HTTPException(400, "No numbers registered")

    snippets = await fetch_news()
    message = format_digest(snippets)

    results = []
    for n in data["numbers"]:
        try:
            wamid = await send_whatsapp(n["phone_number"], message)
            results.append({"phone_number": n["phone_number"], "status": "sent", "wamid": wamid})
            logger.info("Sent to %s (%s)", n["phone_number"], wamid)
        except Exception as e:
            results.append({"phone_number": n["phone_number"], "status": "failed", "error": str(e)})
            logger.error("Failed to send to %s: %s", n["phone_number"], e)
    return {"results": results}


@app.get("/health")
def health():
    return {"status": "ok"}
