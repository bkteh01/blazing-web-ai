import os
import traceback
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from openai import OpenAI

from db_utils import (
    extract_order_reference,
    fetch_admin_stats,
    fetch_customer_messages,
    fetch_order_by_reference,
    fetch_pending_orders,
    fetch_recent_orders,
    save_customer_message,
)


app = FastAPI(title="BlazinGM WhatsApp Webhook")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
ADMIN_WHATSAPP_NUMBERS = {
    item.strip()
    for item in os.getenv("ADMIN_WHATSAPP_NUMBERS", "").split(",")
    if item.strip()
}

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def send_whatsapp_message(to_number: str, text: str) -> None:
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="WhatsApp credentials are not configured.")

    response = requests.post(
        f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
        headers={
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": text[:4096]},
        },
        timeout=15,
    )
    response.raise_for_status()


def build_order_context(order_reference: str | None) -> str:
    if not order_reference:
        return (
            "No verified order number was found in the customer message. "
            "Ask the customer to send the full order number, for example "
            "BGM-20260415-143210-8F3A7C91D2BE or BGM-REF-00000123."
        )

    order = fetch_order_by_reference(order_reference)
    if not order:
        return (
            f"The customer mentioned order reference '{order_reference}', "
            "but no matching order was found in the database."
        )

    return (
        "Verified order details from the database:\n"
        f"- Order number: {order['order_no']}\n"
        f"- Username: {order['user_id']}\n"
        f"- Game: {order['game']}\n"
        f"- Amount: RM {order['amount']}\n"
        f"- Status: {order['status']}\n"
    )


def build_direct_order_reply(customer_message: str) -> str | None:
    order_reference = extract_order_reference(customer_message)
    if not order_reference:
        return None

    order = fetch_order_by_reference(order_reference)
    if not order:
        return (
            f"We could not find an order matching {order_reference}. "
            "Please send the full order number exactly as shown in your receipt."
        )

    return (
        "Here is your order status:\n"
        f"Order No: {order['order_no']}\n"
        f"Game: {order['game']}\n"
        f"Amount: RM {order['amount']}\n"
        f"Status: {order['status']}"
    )


def is_admin_sender(sender_number: str) -> bool:
    return sender_number in ADMIN_WHATSAPP_NUMBERS


def build_admin_reply(customer_message: str, sender_number: str) -> str | None:
    if not is_admin_sender(sender_number):
        return None

    text = customer_message.strip().lower()
    if not text.startswith("admin"):
        return None

    if text in {"admin", "admin help"}:
        return (
            "Admin commands:\n"
            "- admin stats\n"
            "- admin recent\n"
            "- admin pending"
        )

    if text == "admin stats":
        stats = fetch_admin_stats()
        return (
            "Admin summary:\n"
            f"Users: {stats['user_count']}\n"
            f"Orders: {stats['order_count']}\n"
            f"Pending: {stats['pending_count']}\n"
            f"Total Sales: RM {stats['total_sales']}"
        )

    if text == "admin recent":
        orders = fetch_recent_orders(limit=5)
        if not orders:
            return "No recent orders found."
        lines = ["Recent orders:"]
        for order in orders:
            lines.append(
                f"{order['order_no']} | {order['user_id']} | {order['game']} | RM {order['amount']} | {order['status']}"
            )
        return "\n".join(lines)

    if text == "admin pending":
        orders = fetch_pending_orders(limit=10)
        if not orders:
            return "No pending orders found."
        lines = ["Pending orders:"]
        for order in orders:
            lines.append(
                f"{order['order_no']} | {order['user_id']} | {order['game']} | RM {order['amount']}"
            )
        return "\n".join(lines)

    if text == "admin inbox":
        messages = fetch_customer_messages(limit=10)
        if not messages:
            return "No customer messages found."
        lines = ["Customer inbox:"]
        for item in messages:
            lines.append(
                f"#{item['id']} | {item['sender_number']} | {item.get('detected_intent') or 'unknown'} | "
                f"{item.get('priority') or 'normal'} | {item.get('order_reference') or '-'}"
            )
            if item.get("summary"):
                lines.append(f"Summary: {item['summary']}")
        return "\n".join(lines)

    return (
        "Unknown admin command.\n"
        "Use: admin help, admin stats, admin recent, admin pending, admin inbox"
    )


def extract_customer_signal(customer_message: str) -> dict[str, str]:
    order_reference = extract_order_reference(customer_message)
    fallback = {
        "detected_intent": "order_lookup" if order_reference else "general_support",
        "order_reference": order_reference or "",
        "summary": customer_message[:200],
        "priority": "normal",
    }

    try:
        response = openai_client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Extract customer support metadata from the message. "
                                "Return strict JSON with keys: detected_intent, order_reference, summary, priority. "
                                "Priority must be one of: low, normal, high, urgent. "
                                "Keep summary under 160 characters."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": customer_message}],
                },
            ],
            text={"format": {"type": "json_object"}},
            max_output_tokens=200,
        )
        import json

        data = json.loads(response.output_text)
        return {
            "detected_intent": data.get("detected_intent", fallback["detected_intent"]),
            "order_reference": data.get("order_reference", fallback["order_reference"]),
            "summary": data.get("summary", fallback["summary"]),
            "priority": data.get("priority", fallback["priority"]),
        }
    except Exception:
        return fallback


def generate_customer_reply(customer_message: str, sender_number: str) -> str:
    admin_reply = build_admin_reply(customer_message, sender_number)
    if admin_reply:
        return admin_reply

    direct_reply = build_direct_order_reply(customer_message)
    if direct_reply:
        return direct_reply

    order_reference = extract_order_reference(customer_message)
    order_context = build_order_context(order_reference)

    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are the WhatsApp customer support assistant for BlazinGM Store. "
                            "Reply in a friendly, concise support tone. "
                            "If verified order details are available, use only those details. "
                            "Do not invent payment confirmation, completion times, or refund status. "
                            "If no valid order is found, ask for the full order number. "
                            "If the customer asks a general question, answer helpfully and briefly."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Customer message:\n{customer_message}\n\n"
                            f"{order_context}\n\n"
                            "Write the WhatsApp reply now."
                        ),
                    }
                ],
            },
        ],
        max_output_tokens=300,
    )
    return response.output_text.strip()


def extract_whatsapp_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                sender = message.get("from")
                text = message.get("text", {}).get("body", "")
                if sender and text:
                    messages.append({"from": sender, "text": text})

    return messages


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed.")


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    messages = extract_whatsapp_messages(payload)

    for item in messages:
        try:
            reply = generate_customer_reply(item["text"], item["from"])
        except Exception as exc:
            print("Webhook reply generation failed:", repr(exc))
            traceback.print_exc()
            reply = (
                "We received your message, but our assistant is temporarily unavailable. "
                "Please send your full order number and our team will help you check it."
            )

        try:
            extracted = extract_customer_signal(item["text"])
            save_customer_message(
                sender_number=item["from"],
                raw_message=item["text"],
                detected_intent=extracted.get("detected_intent"),
                order_reference=extracted.get("order_reference") or None,
                summary=extracted.get("summary"),
                priority=extracted.get("priority"),
                ai_reply=reply,
            )
        except Exception as exc:
            print("Customer message save failed:", repr(exc))
            traceback.print_exc()

        try:
            send_whatsapp_message(item["from"], reply)
        except Exception:
            pass

    return JSONResponse({"received": True})
