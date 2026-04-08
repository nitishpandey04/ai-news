from datetime import datetime
from zoneinfo import ZoneInfo

TOPIC_EMOJI = {
    "finance": "💰",
    "geopolitics": "🌍",
    "politics": "🏛️",
    "sports": "⚽",
    "lifestyle": "✨",
}


def format_digest(snippets: list[dict], date_str: str | None = None) -> str:
    if date_str is None:
        date_str = datetime.now(ZoneInfo("UTC")).strftime("%A, %B %-d")

    lines = [f"📰 *Your Daily News Digest — {date_str}*", ""]
    for s in snippets:
        emoji = TOPIC_EMOJI.get(s.get("topic", ""), "•")
        topic = s.get("topic", "").capitalize()
        headline = s.get("headline", "")
        summary = s.get("summary", "")
        lines.append(f"{emoji} *{topic}*: {headline}")
        lines.append(f"   {summary}")
        lines.append("")

    lines.append("_Reply STOP to unsubscribe._")
    return "\n".join(lines)
