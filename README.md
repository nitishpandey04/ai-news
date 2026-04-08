# AI News — WhatsApp News Delivery Service

A daily news digest service that delivers 5 news snippets across Finance, Geopolitics, Politics, Sports, and Lifestyle to users via WhatsApp at their chosen time each day.

## Architecture

```
FastAPI (REST API)
  ├── PostgreSQL  — users, subscriptions, delivery logs, news cache
  ├── Redis       — Celery broker + news cache (TTL 23h)
  ├── Celery Beat — dispatch tick every 5 minutes
  └── Celery Worker — per-user delivery tasks
```

WhatsApp delivery is **mocked by default** (logs to console). Real Meta Cloud API is wired in by setting credentials in `.env`.

## Stack

| Concern | Choice |
|---|---|
| Framework | FastAPI |
| Task queue | Celery + Celery Beat |
| Broker / cache | Redis 7 |
| Database | PostgreSQL 15 |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic |
| Containerisation | Docker + Docker Compose |

## Getting Started

### 1. Clone & configure

```bash
git clone git@github.com:nitishpandey04/ai-news.git
cd ai-news
cp .env.example .env
```

### 2. Start services

```bash
docker compose up --build
```

### 3. Run migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Explore the API

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Health check: [http://localhost:8000/health](http://localhost:8000/health)

## API Reference

### Users

```
POST   /api/v1/users                     Register a new user
GET    /api/v1/users/{user_id}           Get user details
DELETE /api/v1/users/{user_id}           Deactivate user
```

### Subscriptions

```
POST   /api/v1/users/{user_id}/subscription   Create / replace subscription
PUT    /api/v1/users/{user_id}/subscription   Update delivery time / timezone / topics
DELETE /api/v1/users/{user_id}/subscription   Cancel subscription
```

### News

```
GET    /api/v1/news/today    View today's 5 news snippets
```

## Quick Test

**Register a user:**
```bash
curl -s -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "display_name": "Nitish"}'
```

**Subscribe** (set `delivery_time` to ~2 minutes from now to see a quick delivery):
```bash
curl -s -X POST http://localhost:8000/api/v1/users/<USER_ID>/subscription \
  -H "Content-Type: application/json" \
  -d '{"delivery_time": "08:30", "timezone": "Asia/Kolkata"}'
```

Watch the `worker` container logs — a `[WHATSAPP MOCK]` entry will appear when the digest is delivered.

## Enabling Real WhatsApp Delivery

1. Create a [Meta for Developers](https://developers.facebook.com/) app with WhatsApp Business API access.
2. Get your **Phone Number ID** and a **permanent access token**.
3. Create and approve a message template named `daily_news_digest` in Meta Business Suite.
4. Add credentials to `.env`:

```env
WHATSAPP_ACCESS_TOKEN=EAAxxxxx
WHATSAPP_PHONE_NUMBER_ID=1234567890
```

The service auto-detects the credentials and switches from mock to live delivery.

## Project Structure

```
app/
├── main.py              # FastAPI app + health check
├── config.py            # Environment config (pydantic-settings)
├── database.py          # Async SQLAlchemy engine
├── models/              # ORM models (User, Subscription, NewsCache, DeliveryLog)
├── schemas/             # Pydantic request/response schemas
├── routers/             # API route handlers
├── services/
│   ├── news_service.py       # Mock news API + Redis cache
│   ├── whatsapp_service.py   # Mock/real WhatsApp delivery
│   ├── user_service.py
│   └── subscription_service.py
├── tasks/
│   ├── celery_app.py         # Celery + Beat config
│   ├── dispatch_tick.py      # 5-min polling scheduler
│   └── send_news.py          # Per-user delivery task (with retries)
└── utils/
    ├── timezone.py           # next_delivery_utc() helper
    └── formatting.py         # WhatsApp message formatter
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `WHATSAPP_ACCESS_TOKEN` | _(empty)_ | Meta access token — blank = mock mode |
| `WHATSAPP_PHONE_NUMBER_ID` | _(empty)_ | Meta phone number ID |
| `DISPATCH_TICK_INTERVAL_SECONDS` | `300` | How often the scheduler polls (seconds) |
