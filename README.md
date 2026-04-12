# ai-news

A minimal WhatsApp news delivery service. Stores a list of phone numbers, fetches today's top news from Perplexity, and sends a digest to every number on demand.

Single file (`main.py`), no database, no scheduler, no cache.

## Setup

1. Copy and fill in credentials:
   ```bash
   cp .env.example .env
   ```
   ```env
   PERPLEXITY_API_KEY=pplx-...
   WHATSAPP_ACCESS_TOKEN=EAA...
   WHATSAPP_PHONE_NUMBER_ID=123...
   ```

2. Start the service:
   ```bash
   docker compose up --build -d
   ```

3. Open the interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/numbers` | List all stored numbers |
| `POST` | `/numbers` | Add a number — body: `{"phone_number": "+91...", "name": "..."}` |
| `DELETE` | `/numbers?phone_number=+91...` | Remove a number |
| `GET` | `/time` | Get the stored delivery time |
| `PUT` | `/time` | Update delivery time — body: `{"delivery_time": "10:00"}` |
| `POST` | `/send` | Fetch news from Perplexity and send to all numbers immediately |
| `GET` | `/health` | Health check |

The delivery time is just a stored value — there is no scheduler. Hit `POST /send` whenever you want a delivery.

## Quick test

```bash
curl -s -X POST http://localhost:8000/numbers \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "name": "Alice"}'

curl -s -X POST http://localhost:8000/send
```

## Storage

All state lives in `data.json` in the project root:

```json
{
  "numbers": [
    {"phone_number": "+919876543210", "name": "Alice"}
  ],
  "delivery_time": "10:00"
}
```

The file is gitignored.

## WhatsApp setup notes

- The recipient number must be added as a **test recipient** in the Meta Developer portal (WhatsApp → API Setup → "To" field) and verified with the code Meta sends to it.
- Meta's temporary access tokens expire after 24 hours. For long-term use, generate a permanent token via a System User in Meta Business Suite.
