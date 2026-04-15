# WhatsApp Webhook Setup

## What this adds

- `whatsapp_webhook.py`: FastAPI webhook service for WhatsApp Cloud API
- `db_utils.py`: shared database helper for extracting and looking up order references
- LLM reply flow using OpenAI Responses API

## Environment variables

Set these before running the webhook service:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini

WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_ACCESS_TOKEN=your_meta_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
ADMIN_WHATSAPP_NUMBERS=60123456789,60111111111

DB_HOST=aws-1-ap-southeast-2.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.jpfqogcehayhetfdxubl
DB_PASSWORD=your_db_password
DB_PORT=5432
DB_SSLMODE=require
```

## Run locally

```bash
uvicorn whatsapp_webhook:app --host 0.0.0.0 --port 8000
```

## Webhook endpoints

- `GET /health`
- `GET /webhook` for Meta webhook verification
- `POST /webhook` for incoming WhatsApp messages

## Current behavior

- If the customer message contains an order number, the service looks up the order in PostgreSQL
- If the order is found, the LLM replies using the verified order details
- If no order is found, the LLM asks the customer to send the full order number
- If the message is general support text, the LLM answers as customer support
- If the sender number is in `ADMIN_WHATSAPP_NUMBERS`, the sender can use admin commands

## Admin commands

Authorized admin numbers can send:

```text
admin help
admin stats
admin recent
admin pending
admin inbox
```

Examples:

- `admin stats` -> users, orders, pending count, total sales
- `admin recent` -> latest 5 orders
- `admin pending` -> latest pending orders
- `admin inbox` -> latest structured customer messages captured from WhatsApp

## Important limitation

Right now the bot is best at order lookup by order number.

It does **not** yet map WhatsApp phone numbers to user accounts in your database.
If you want "check my latest order" without entering an order number, add a phone field to your users table and store the WhatsApp number.

## Deployment note

Your current `Procfile` starts Streamlit only:

```text
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

That means the webhook service should usually be deployed as a separate web service, or you should switch the main deployment architecture to a backend framework that can host both app UI and webhook routes.
