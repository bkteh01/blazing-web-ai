import os
import re

import psycopg2
from psycopg2.extras import RealDictCursor


DEFAULT_DB_CONFIG = {
    "host": os.getenv("DB_HOST", "aws-1-ap-southeast-2.pooler.supabase.com"),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres.jpfqogcehayhetfdxubl"),
    "password": os.getenv("DB_PASSWORD", "BlazinGM@2026#Secure"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
    "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
}


ORDER_REF_PATTERN = re.compile(
    r"\b(?:BGM-\d{8}-\d{6}-[A-Z0-9]{12}|BGM-REF-\d{8}|ORD-[A-Z0-9-]+)\b",
    re.IGNORECASE,
)


def open_db_connection():
    return psycopg2.connect(**DEFAULT_DB_CONFIG)


def ensure_customer_messages_table():
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS customer_messages (
                    id BIGSERIAL PRIMARY KEY,
                    sender_number VARCHAR(32) NOT NULL,
                    raw_message TEXT NOT NULL,
                    detected_intent VARCHAR(64),
                    order_reference VARCHAR(64),
                    summary TEXT,
                    priority VARCHAR(32),
                    ai_reply TEXT,
                    admin_reply TEXT,
                    replied_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                ALTER TABLE customer_messages
                ADD COLUMN IF NOT EXISTS admin_reply TEXT
                """
            )
            cursor.execute(
                """
                ALTER TABLE customer_messages
                ADD COLUMN IF NOT EXISTS replied_at TIMESTAMPTZ
                """
            )
        conn.commit()
    finally:
        conn.close()


def extract_order_reference(text):
    if not text:
        return None
    match = ORDER_REF_PATTERN.search(text.upper())
    return match.group(0) if match else None


def fetch_order_by_reference(order_reference):
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, COALESCE(order_no, ''), user_id, game, amount, status
                    FROM orders
                    WHERE order_no = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (order_reference,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "order_no": row[1] or f"BGM-REF-{int(row[0]):08d}",
                        "user_id": row[2],
                        "game": row[3],
                        "amount": row[4],
                        "status": row[5],
                    }
            except psycopg2.Error:
                conn.rollback()

            if order_reference.startswith("BGM-REF-"):
                try:
                    order_id = int(order_reference.replace("BGM-REF-", ""))
                except ValueError:
                    return None

                cursor.execute(
                    """
                    SELECT id, user_id, game, amount, status
                    FROM orders
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (order_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "order_no": f"BGM-REF-{int(row[0]):08d}",
                        "user_id": row[1],
                        "game": row[2],
                        "amount": row[3],
                        "status": row[4],
                    }

            return None
    finally:
        conn.close()


def fetch_admin_stats():
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            pending_count = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM orders")
            total_sales = cursor.fetchone()[0]

            return {
                "user_count": user_count,
                "order_count": order_count,
                "pending_count": pending_count,
                "total_sales": total_sales,
            }
    finally:
        conn.close()


def fetch_recent_orders(limit=5):
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, COALESCE(order_no, ''), user_id, game, amount, status
                    FROM orders
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "order_no": row[1] or f"BGM-REF-{int(row[0]):08d}",
                        "user_id": row[2],
                        "game": row[3],
                        "amount": row[4],
                        "status": row[5],
                    }
                    for row in rows
                ]
            except psycopg2.Error:
                conn.rollback()
                cursor.execute(
                    """
                    SELECT id, user_id, game, amount, status
                    FROM orders
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "order_no": f"BGM-REF-{int(row[0]):08d}",
                        "user_id": row[1],
                        "game": row[2],
                        "amount": row[3],
                        "status": row[4],
                    }
                    for row in rows
                ]
    finally:
        conn.close()


def fetch_pending_orders(limit=10):
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, COALESCE(order_no, ''), user_id, game, amount, status
                    FROM orders
                    WHERE status = 'pending'
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "order_no": row[1] or f"BGM-REF-{int(row[0]):08d}",
                        "user_id": row[2],
                        "game": row[3],
                        "amount": row[4],
                        "status": row[5],
                    }
                    for row in rows
                ]
            except psycopg2.Error:
                conn.rollback()
                cursor.execute(
                    """
                    SELECT id, user_id, game, amount, status
                    FROM orders
                    WHERE status = 'pending'
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "order_no": f"BGM-REF-{int(row[0]):08d}",
                        "user_id": row[1],
                        "game": row[2],
                        "amount": row[3],
                        "status": row[4],
                    }
                    for row in rows
                ]
    finally:
        conn.close()


def save_customer_message(
    sender_number,
    raw_message,
    detected_intent=None,
    order_reference=None,
    summary=None,
    priority=None,
    ai_reply=None,
):
    ensure_customer_messages_table()
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO customer_messages
                (sender_number, raw_message, detected_intent, order_reference, summary, priority, ai_reply)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    sender_number,
                    raw_message,
                    detected_intent,
                    order_reference,
                    summary,
                    priority,
                    ai_reply,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def fetch_customer_messages(limit=20):
    ensure_customer_messages_table()
    conn = open_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, sender_number, raw_message, detected_intent, order_reference,
                       summary, priority, ai_reply, admin_reply, replied_at, created_at
                FROM customer_messages
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cursor.fetchall()
    finally:
        conn.close()


def save_admin_reply(message_id, admin_reply):
    ensure_customer_messages_table()
    conn = open_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customer_messages
                SET admin_reply = %s,
                    replied_at = NOW()
                WHERE id = %s
                """,
                (admin_reply, message_id),
            )
        conn.commit()
    finally:
        conn.close()
