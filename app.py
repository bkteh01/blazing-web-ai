import os
from datetime import datetime
from uuid import uuid4

import pandas as pd
import psycopg2
import requests
from psycopg2 import extensions
import streamlit as st

from db_utils import ensure_customer_messages_table, save_admin_reply


st.set_page_config(
    page_title="BlazinGM Store",
    page_icon="🎮",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #07111f;
        --panel: rgba(12, 26, 44, 0.88);
        --panel-2: rgba(17, 35, 58, 0.92);
        --line: rgba(124, 168, 255, 0.18);
        --text: #edf4ff;
        --muted: #9fb3cc;
        --accent: #ff7a18;
        --accent-2: #ffd166;
    }

    html, body, [class*="css"] {
        font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 122, 24, 0.20), transparent 28%),
            radial-gradient(circle at top right, rgba(99, 102, 241, 0.22), transparent 32%),
            linear-gradient(180deg, #040a14 0%, #07111f 52%, #091728 100%);
        color: var(--text);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(6, 16, 30, 0.95), rgba(8, 21, 38, 0.98));
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea {
        background: rgba(8, 19, 33, 0.92);
        color: var(--text);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stButton > button {
        width: 100%;
        border: 0;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        color: #08111d;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        box-shadow: 0 10px 30px rgba(255, 122, 24, 0.24);
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(18, 34, 56, 0.95), rgba(10, 22, 38, 0.95));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 0.8rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
    }

    .hero-card {
        overflow: hidden;
        padding: 2rem;
        border-radius: 28px;
        border: 1px solid var(--line);
        background:
            radial-gradient(circle at 85% 20%, rgba(255, 209, 102, 0.25), transparent 20%),
            linear-gradient(135deg, rgba(15, 32, 56, 0.95), rgba(8, 20, 36, 0.92));
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.26);
        margin-bottom: 1.4rem;
    }

    .hero-kicker {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(255, 122, 24, 0.14);
        color: #ffd7b0;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .hero-title {
        margin: 0.9rem 0 0.45rem;
        font-size: 3rem;
        line-height: 1;
        color: var(--text);
    }

    .hero-text {
        max-width: 720px;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.65;
    }

    .section-title {
        margin: 1.1rem 0 0.35rem;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text);
    }

    .section-subtitle {
        color: var(--muted);
        margin-bottom: 1rem;
    }

    .game-card,
    .glass-card,
    .account-card,
    .order-item {
        border: 1px solid var(--line);
        background: linear-gradient(180deg, var(--panel), var(--panel-2));
        box-shadow: 0 18px 46px rgba(0, 0, 0, 0.18);
    }

    .game-card {
        padding: 1rem;
        min-height: 430px;
        border-radius: 24px;
    }

    .glass-card {
        padding: 1.2rem;
        border-radius: 22px;
    }

    .game-title {
        margin-top: 0.9rem;
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text);
    }

    .game-meta,
    .tiny-label {
        color: var(--muted);
    }

    .pill-row {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        margin-bottom: 0.9rem;
    }

    .pill {
        padding: 0.28rem 0.7rem;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.04);
        color: #d6e4ff;
        font-size: 0.8rem;
    }

    .account-card,
    .order-item {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        margin-bottom: 0.8rem;
        background: rgba(255, 255, 255, 0.03);
    }

    .wallet-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-2);
        margin: 0.35rem 0 0;
    }

    .tiny-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


PRODUCTS = [
    {
        "key": "ml",
        "name": "Mobile Legends",
        "image": "images/ml.png",
        "price": 10,
        "price_text": "Top-up from RM10",
        "tags": ["Fast Delivery", "SEA Favorite", "Starter RM10"],
    },
    {
        "key": "pubg",
        "name": "PUBG Mobile",
        "image": "images/pubg.png",
        "price": 10,
        "price_text": "Top-up from RM10",
        "tags": ["Instant UC", "Battle Ready", "Starter RM10"],
    },
    {
        "key": "hok",
        "name": "Honor Of Kings",
        "image": "images/hok.png",
        "price": 10,
        "price_text": "Top-up from RM10",
        "tags": ["Popular MOBA", "Mobile First", "Starter RM10"],
    },
]


def open_db_connection():
    return psycopg2.connect(
        host="aws-1-ap-southeast-2.pooler.supabase.com",
        database="postgres",
        user="postgres.jpfqogcehayhetfdxubl",
        password="BlazinGM@2026#Secure",
        port=5432,
        sslmode="require",
        connect_timeout=5,
    )


try:
    conn = open_db_connection()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


def send_whatsapp_text_message(to_number, text):
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    if not access_token or not phone_number_id:
        raise ValueError("WhatsApp environment variables are not configured.")

    response = requests.post(
        f"https://graph.facebook.com/v22.0/{phone_number_id}/messages",
        headers={
            "Authorization": f"Bearer {access_token}",
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


if "user" not in st.session_state:
    st.session_state["user"] = None

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if "session_token" not in st.session_state:
    st.session_state["session_token"] = None

if "login_token_ready" not in st.session_state:
    st.session_state["login_token_ready"] = None


def reset_failed_transaction():
    global conn
    try:
        if conn.closed:
            conn = open_db_connection()
        if conn.get_transaction_status() == extensions.TRANSACTION_STATUS_INERROR:
            conn.rollback()
    except Exception:
        conn = open_db_connection()


def ensure_login_token_column():
    try:
        return fetch_one(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'users'
              AND column_name = 'login_token'
            LIMIT 1
            """
        ) is not None
    except Exception:
        return False


def login_token_enabled():
    if st.session_state["login_token_ready"] is None:
        st.session_state["login_token_ready"] = ensure_login_token_column()
    return st.session_state["login_token_ready"]


def fetch_one(query, params=None):
    reset_failed_transaction()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    except Exception:
        conn.rollback()
        raise


def fetch_all(query, params=None):
    reset_failed_transaction()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except Exception:
        conn.rollback()
        raise


def execute_write(query, params=None):
    reset_failed_transaction()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise


def set_active_login_token(username, token):
    if not login_token_enabled():
        return
    execute_write(
        "UPDATE users SET login_token=%s WHERE username=%s",
        (token, username),
    )


def clear_active_login_token(username, token):
    if not login_token_enabled():
        return
    execute_write(
        "UPDATE users SET login_token=NULL WHERE username=%s AND login_token=%s",
        (username, token),
    )


def session_still_valid():
    if not st.session_state["user"]:
        return True
    if not login_token_enabled() or not st.session_state["session_token"]:
        return True

    token_row = fetch_one(
        "SELECT login_token FROM users WHERE username=%s",
        (st.session_state["user"],),
    )
    current_token = token_row[0] if token_row else None
    return current_token == st.session_state["session_token"]


def force_logout_due_to_other_login():
    st.session_state["user"] = None
    st.session_state["is_admin"] = False
    st.session_state["session_token"] = None
    st.warning("This account was logged in on another device. You have been signed out.")
    st.stop()


def generate_order_number():
    return f"BGM-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:12].upper()}"


def build_fallback_order_ref(order_id):
    return f"BGM-REF-{int(order_id):08d}"


def ensure_order_number_column():
    try:
        return fetch_one(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'orders'
              AND column_name = 'order_no'
            """
        ) is not None
    except Exception:
        return False


if "order_no_ready" not in st.session_state:
    st.session_state["order_no_ready"] = None


def order_numbers_enabled():
    if st.session_state["order_no_ready"] is None:
        st.session_state["order_no_ready"] = ensure_order_number_column()
    return st.session_state["order_no_ready"]


def user_is_admin(username):
    return username.lower() == "admin"


def render_hero():
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Instant Top-up Platform</div>
            <div class="hero-title">BlazinGM Store</div>
            <div class="hero-text">
                Fast game reloads, cleaner checkout, and a sharper dashboard for both players and admins.
                Everything is organized around a premium storefront feel instead of the default Streamlit layout.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title, subtitle):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_game_card(product):
    tags_html = "".join([f'<span class="pill">{tag}</span>' for tag in product["tags"]])
    st.image(product["image"], use_container_width=True)
    st.markdown(f"**{product['name']}**")
    st.caption(product["price_text"])
    st.markdown(f'<div class="pill-row">{tags_html}</div>', unsafe_allow_html=True)


def end_card():
    st.markdown("</div>", unsafe_allow_html=True)


def create_order(username, game_name, amount):
    if order_numbers_enabled():
        order_no = generate_order_number()
        try:
            result = fetch_one(
                "INSERT INTO orders (order_no, user_id, game, amount, status) VALUES (%s, %s, %s, %s, %s) RETURNING id, order_no",
                (order_no, username, game_name, amount, "pending"),
            )
            conn.commit()
            return result[1] if result and result[1] else order_no
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            st.session_state["order_no_ready"] = False

    try:
        result = fetch_one(
            "INSERT INTO orders (user_id, game, amount, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (username, game_name, amount, "pending"),
        )
        conn.commit()
        return build_fallback_order_ref(result[0]) if result and result[0] is not None else None
    except Exception:
        conn.rollback()
        execute_write(
            "INSERT INTO orders (user_id, game, amount, status) VALUES (%s, %s, %s, %s)",
            (username, game_name, amount, "pending"),
        )
        return None


def render_account_shell(title, subtitle):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section(title, subtitle)


def show_user_panel():
    if not st.session_state["user"]:
        return

    st.sidebar.success(f"Signed in as {st.session_state['user']}")

    balance_row = fetch_one(
        "SELECT balance FROM users WHERE username=%s",
        (st.session_state["user"],),
    )
    balance = balance_row[0] if balance_row else 0

    try:
        orders = fetch_all(
            "SELECT id, order_no, game, amount, status FROM orders WHERE user_id=%s ORDER BY id DESC",
            (st.session_state["user"],),
        )
        orders_with_ref = [
            (order_no or build_fallback_order_ref(order_id), game, amount, status)
            for order_id, order_no, game, amount, status in orders
        ]
    except Exception:
        orders = fetch_all(
            "SELECT id, game, amount, status FROM orders WHERE user_id=%s ORDER BY id DESC",
            (st.session_state["user"],),
        )
        orders_with_ref = [
            (build_fallback_order_ref(order_id), game, amount, status)
            for order_id, game, amount, status in orders
        ]

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section("Wallet", "Your account snapshot updates in real time.")
    st.markdown(
        f"""
        <div class="account-card">
            <div class="tiny-label">Current Balance</div>
            <div class="wallet-value">RM {balance}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section("My Orders", "Recent purchases and their current processing status.")
    if orders_with_ref:
        for order_ref, game, amount, status in orders_with_ref:
            st.markdown(
                f"""
                <div class="order-item">
                    <div><strong>{game}</strong></div>
                    <div class="tiny-label">Full Order No: {order_ref}</div>
                    <div class="tiny-label">Amount: RM {amount} · Status: {status}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("You have no orders yet.")
    end_card()

    if st.sidebar.button("Logout"):
        try:
            clear_active_login_token(
                st.session_state["user"],
                st.session_state["session_token"],
            )
        except Exception:
            pass
        st.session_state["user"] = None
        st.session_state["is_admin"] = False
        st.session_state["session_token"] = None
        st.rerun()


menu = ["Home", "Login", "Register"]
if st.session_state["is_admin"]:
    menu.append("Admin")

if st.session_state["user"] and not session_still_valid():
    force_logout_due_to_other_login()

st.sidebar.markdown("## BlazinGM")
st.sidebar.caption("Gaming top-up console")
choice = st.sidebar.selectbox("Menu", menu)


if choice == "Home":
    render_hero()
    render_section("Popular Games", "Choose a title and launch a top-up flow in one click.")

    columns = st.columns(3)
    for column, product in zip(columns, PRODUCTS):
        with column:
            render_game_card(product)
            if st.button("Top Up Now", key=f"topup_{product['key']}"):
                if not st.session_state["user"]:
                    st.warning("Please login first")
                else:
                    try:
                        order_no = create_order(
                            st.session_state["user"],
                            product["name"],
                            product["price"],
                        )
                        if order_no:
                            st.success(f"Order created! Full order number: {order_no}")
                        else:
                            st.success("Order created!")
                    except Exception as e:
                        st.error(f"Order failed: {e}")

elif choice == "Register":
    render_hero()
    left, center, right = st.columns([1, 1.3, 1])
    with center:
        render_account_shell("Create Account", "Set up a player account to start ordering top-ups.")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            try:
                execute_write(
                    "INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)",
                    (new_user, new_pass, 0),
                )
                st.success("Account created!")
            except Exception as e:
                st.error(f"Register failed: {e}")
        end_card()

elif choice == "Login":
    render_hero()
    left, center, right = st.columns([1, 1.3, 1])
    with center:
        render_account_shell("Login", "Access your wallet, orders, and admin tools from one place.")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            try:
                result = fetch_one(
                    "SELECT username FROM users WHERE username=%s AND password=%s",
                    (user, password),
                )

                if result:
                    session_token = uuid4().hex
                    set_active_login_token(user, session_token)
                    st.session_state["user"] = user
                    st.session_state["is_admin"] = user_is_admin(user)
                    st.session_state["session_token"] = session_token
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid login")
            except Exception as e:
                st.error(f"Login failed: {e}")
        end_card()

elif choice == "Admin":
    if not st.session_state["user"] or not st.session_state["is_admin"]:
        st.error("Admin access only")
        st.stop()

    try:
        render_hero()
        render_section("Admin Dashboard", "Track players, monitor orders, and update order status.")

        users = fetch_all("SELECT username, balance FROM users ORDER BY username")
        users_df = pd.DataFrame(users, columns=["Username", "Balance"])

        try:
            orders = fetch_all(
                "SELECT id, order_no, game, amount, status, user_id FROM orders ORDER BY id DESC"
            )
            orders_df = pd.DataFrame(
                [
                    (
                        order_no or build_fallback_order_ref(order_id),
                        game,
                        amount,
                        status,
                        user_id,
                    )
                    for order_id, order_no, game, amount, status, user_id in orders
                ],
                columns=["Order No", "Game", "Amount", "Status", "User"],
            )
        except Exception:
            orders = fetch_all("SELECT id, game, amount, status, user_id FROM orders ORDER BY id DESC")
            orders_df = pd.DataFrame(
                [
                    (build_fallback_order_ref(order_id), game, amount, status, user_id)
                    for order_id, game, amount, status, user_id in orders
                ],
                columns=["Order No", "Game", "Amount", "Status", "User"],
            )

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Users", len(users_df))
        col_b.metric("Orders", len(orders_df))
        col_c.metric(
            "Pending Orders",
            int((orders_df["Status"] == "pending").sum()) if not orders_df.empty else 0,
        )

        left, right = st.columns([1.2, 1])
        with left:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section("Users", "Registered players and their current balances.")
            st.dataframe(users_df, use_container_width=True)
            end_card()

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section("Orders", "All orders across the platform.")
            st.dataframe(orders_df, use_container_width=True)
            end_card()

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section("Customer Inbox", "Structured customer messages captured from WhatsApp.")
            try:
                ensure_customer_messages_table()
                inbox_rows = fetch_all(
                    """
                    SELECT id, sender_number, raw_message, detected_intent, order_reference,
                           summary, priority, admin_reply, replied_at, created_at
                    FROM customer_messages
                    ORDER BY id DESC
                    LIMIT 20
                    """
                )
                inbox_df = pd.DataFrame(
                    inbox_rows,
                    columns=[
                        "ID",
                        "Sender",
                        "Raw Message",
                        "Intent",
                        "Order Ref",
                        "Summary",
                        "Priority",
                        "Admin Reply",
                        "Replied At",
                        "Created At",
                    ],
                )
                if inbox_df.empty:
                    st.info("No customer messages yet.")
                else:
                    st.dataframe(inbox_df, use_container_width=True)

                    message_options = {
                        f"#{row[0]} | {row[1]} | {row[5] or row[2][:40]}": {
                            "id": row[0],
                            "sender": row[1],
                            "raw_message": row[2],
                            "admin_reply": row[7] or "",
                        }
                        for row in inbox_rows
                    }

                    selected_message_label = st.selectbox(
                        "Choose a customer message to reply",
                        list(message_options.keys()),
                        key="customer_inbox_reply_select",
                    )
                    selected_message = message_options[selected_message_label]

                    st.text_area(
                        "Customer message",
                        value=selected_message["raw_message"],
                        height=120,
                        disabled=True,
                        key="customer_inbox_raw_message",
                    )

                    admin_reply_text = st.text_area(
                        "Reply to customer",
                        value=selected_message["admin_reply"],
                        height=120,
                        key=f"customer_reply_text_{selected_message['id']}",
                    )

                    if st.button("Send WhatsApp Reply", key="send_customer_inbox_reply"):
                        try:
                            send_whatsapp_text_message(
                                selected_message["sender"],
                                admin_reply_text,
                            )
                            save_admin_reply(selected_message["id"], admin_reply_text)
                            st.success("Reply sent to customer on WhatsApp.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send WhatsApp reply: {e}")
            except Exception as e:
                st.info(f"Customer inbox not ready yet: {e}")
            end_card()

        with right:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section("Update Order Status", "Adjust the status of an existing order.")
            try:
                try:
                    order_rows = fetch_all(
                        "SELECT id, order_no, user_id, game, amount, status FROM orders ORDER BY id DESC"
                    )
                    order_options = {
                        f"Order: {row[1] or build_fallback_order_ref(row[0])} | User: {row[2]} | {row[3]} | RM{row[4]} | {row[5]}": row[0]
                        for row in order_rows
                    }
                except Exception:
                    order_rows = fetch_all(
                        "SELECT id, user_id, game, amount, status FROM orders ORDER BY id DESC"
                    )
                    order_options = {
                        f"Order: {build_fallback_order_ref(row[0])} | User: {row[1]} | {row[2]} | RM{row[3]} | {row[4]}": row[0]
                        for row in order_rows
                    }

                if order_options:
                    selected_label = st.selectbox("Choose an order", list(order_options.keys()))
                    new_status = st.selectbox(
                        "New status",
                        ["pending", "paid", "processing", "completed", "cancelled"],
                    )

                    if st.button("Update Order Status", key="admin_update_order"):
                        execute_write(
                            "UPDATE orders SET status=%s WHERE id=%s",
                            (new_status, order_options[selected_label]),
                        )
                        st.success("Order status updated")
                        st.rerun()
                else:
                    st.info("No orders yet")
            except psycopg2.errors.UndefinedColumn:
                st.warning("The orders table has no 'id' column, so status updates are disabled.")
            end_card()
    except Exception as e:
        st.error(f"Admin dashboard failed: {e}")


if choice != "Admin":
    show_user_panel()
elif st.session_state["user"]:
    st.sidebar.success(f"Signed in as {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        try:
            clear_active_login_token(
                st.session_state["user"],
                st.session_state["session_token"],
            )
        except Exception:
            pass
        st.session_state["user"] = None
        st.session_state["is_admin"] = False
        st.session_state["session_token"] = None
        st.rerun()
