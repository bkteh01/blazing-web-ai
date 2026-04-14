from datetime import datetime
from uuid import uuid4

import pandas as pd
import psycopg2
import streamlit as st


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


@st.cache_resource(show_spinner=False)
def get_db_connection():
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
    conn = get_db_connection()
    cursor = conn.cursor()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


if "user" not in st.session_state:
    st.session_state["user"] = None

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False


def generate_order_number():
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"


def ensure_order_number_column():
    try:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'orders'
              AND column_name = 'order_no'
            """
        )
        column_exists = cursor.fetchone() is not None

        if not column_exists:
            cursor.execute(
                """
                ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS order_no VARCHAR(32)
                """
            )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE order_no IS NULL OR order_no = ''
            """
        )
        missing_count = cursor.fetchone()[0]

        if missing_count:
            cursor.execute(
                """
                WITH numbered AS (
                    SELECT ctid, ROW_NUMBER() OVER (ORDER BY ctid) AS rn
                    FROM orders
                    WHERE order_no IS NULL OR order_no = ''
                )
                UPDATE orders
                SET order_no = 'ORD-LEGACY-' || LPAD(numbered.rn::text, 6, '0')
                FROM numbered
                WHERE orders.ctid = numbered.ctid
                """
            )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False


if "order_no_ready" not in st.session_state:
    st.session_state["order_no_ready"] = None


def order_numbers_enabled():
    if st.session_state["order_no_ready"] is None:
        st.session_state["order_no_ready"] = ensure_order_number_column()
    return st.session_state["order_no_ready"]


def user_is_admin(username):
    try:
        cursor.execute(
            "SELECT role FROM users WHERE username=%s",
            (username,),
        )
        result = cursor.fetchone()
        return bool(result and str(result[0]).lower() == "admin")
    except psycopg2.errors.UndefinedColumn:
        conn.rollback()

    try:
        cursor.execute(
            "SELECT is_admin FROM users WHERE username=%s",
            (username,),
        )
        result = cursor.fetchone()
        return bool(result and result[0])
    except psycopg2.errors.UndefinedColumn:
        conn.rollback()

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
    st.markdown('<div class="game-card">', unsafe_allow_html=True)
    st.image(product["image"], use_container_width=True)
    st.markdown(f'<div class="game-title">{product["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="game-meta">{product["price_text"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pill-row">{tags_html}</div>', unsafe_allow_html=True)


def end_card():
    st.markdown("</div>", unsafe_allow_html=True)


def create_order(username, game_name, amount):
    if order_numbers_enabled():
        order_no = generate_order_number()
        cursor.execute(
            "INSERT INTO orders (order_no, user_id, game, amount, status) VALUES (%s, %s, %s, %s, %s)",
            (order_no, username, game_name, amount, "pending"),
        )
        conn.commit()
        return order_no

    cursor.execute(
        "INSERT INTO orders (user_id, game, amount, status) VALUES (%s, %s, %s, %s)",
        (username, game_name, amount, "pending"),
    )
    conn.commit()
    return None


def render_account_shell(title, subtitle):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section(title, subtitle)


def show_user_panel():
    if not st.session_state["user"]:
        return

    st.sidebar.success(f"Signed in as {st.session_state['user']}")

    cursor.execute(
        "SELECT balance FROM users WHERE username=%s",
        (st.session_state["user"],),
    )
    balance = cursor.fetchone()[0]

    if order_numbers_enabled():
        cursor.execute(
            "SELECT order_no, game, amount, status FROM orders WHERE user_id=%s ORDER BY order_no DESC",
            (st.session_state["user"],),
        )
        orders = cursor.fetchall()
    else:
        cursor.execute(
            "SELECT game, amount, status FROM orders WHERE user_id=%s",
            (st.session_state["user"],),
        )
        orders = cursor.fetchall()

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
    if orders:
        if order_numbers_enabled():
            for order_no, game, amount, status in orders:
                st.markdown(
                    f"""
                    <div class="order-item">
                        <div><strong>{game}</strong></div>
                        <div class="tiny-label">Order No: {order_no}</div>
                        <div class="tiny-label">Amount: RM {amount} · Status: {status}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            for game, amount, status in orders:
                st.markdown(
                    f"""
                    <div class="order-item">
                        <div><strong>{game}</strong></div>
                        <div class="tiny-label">Amount: RM {amount} · Status: {status}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("You have no orders yet.")
    end_card()

    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.session_state["is_admin"] = False
        st.rerun()


menu = ["Home", "Login", "Register"]
if st.session_state["is_admin"]:
    menu.append("Admin")

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
                    order_no = create_order(
                        st.session_state["user"],
                        product["name"],
                        product["price"],
                    )
                    if order_no:
                        st.success(f"Order created! Your order number is {order_no}")
                    else:
                        st.success("Order created!")
            end_card()

elif choice == "Register":
    render_hero()
    left, center, right = st.columns([1, 1.3, 1])
    with center:
        render_account_shell("Create Account", "Set up a player account to start ordering top-ups.")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            cursor.execute(
                "INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)",
                (new_user, new_pass, 0),
            )
            conn.commit()
            st.success("Account created!")
        end_card()

elif choice == "Login":
    render_hero()
    left, center, right = st.columns([1, 1.3, 1])
    with center:
        render_account_shell("Login", "Access your wallet, orders, and admin tools from one place.")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (user, password),
            )
            result = cursor.fetchone()

            if result:
                st.session_state["user"] = user
                st.session_state["is_admin"] = user_is_admin(user)
                st.success("Logged in!")
            else:
                st.error("Invalid login")
        end_card()

elif choice == "Admin":
    if not st.session_state["user"] or not st.session_state["is_admin"]:
        st.error("Admin access only")
        st.stop()

    render_hero()
    render_section("Admin Dashboard", "Track players, monitor orders, and update order status.")

    cursor.execute("SELECT username, balance FROM users ORDER BY username")
    users = cursor.fetchall()
    users_df = pd.DataFrame(users, columns=["Username", "Balance"])

    if order_numbers_enabled():
        cursor.execute(
            "SELECT order_no, game, amount, status, user_id FROM orders ORDER BY order_no DESC"
        )
        orders = cursor.fetchall()
        orders_df = pd.DataFrame(
            orders,
            columns=["Order No", "Game", "Amount", "Status", "User"],
        )
    else:
        cursor.execute("SELECT game, amount, status, user_id FROM orders ORDER BY user_id, game")
        orders = cursor.fetchall()
        orders_df = pd.DataFrame(orders, columns=["Game", "Amount", "Status", "User"])

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

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_section("Update Order Status", "Adjust the status of an existing order.")
        try:
            if order_numbers_enabled():
                cursor.execute(
                    "SELECT id, order_no, user_id, game, amount, status FROM orders ORDER BY id DESC"
                )
            else:
                cursor.execute(
                    "SELECT id, user_id, game, amount, status FROM orders ORDER BY id DESC"
                )
            order_rows = cursor.fetchall()
            if order_numbers_enabled():
                order_options = {
                    f"{row[1]} | {row[2]} | {row[3]} | RM{row[4]} | {row[5]}": row[0]
                    for row in order_rows
                }
            else:
                order_options = {
                    f"#{row[0]} | {row[1]} | {row[2]} | RM{row[3]} | {row[4]}": row[0]
                    for row in order_rows
                }

            if order_options:
                selected_label = st.selectbox("Choose an order", list(order_options.keys()))
                new_status = st.selectbox(
                    "New status",
                    ["pending", "paid", "processing", "completed", "cancelled"],
                )

                if st.button("Update Order Status", key="admin_update_order"):
                    cursor.execute(
                        "UPDATE orders SET status=%s WHERE id=%s",
                        (new_status, order_options[selected_label]),
                    )
                    conn.commit()
                    st.success("Order status updated")
                    st.rerun()
            else:
                st.info("No orders yet")
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            st.warning("The orders table has no 'id' column, so status updates are disabled.")
        end_card()


show_user_panel()
