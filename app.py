import streamlit as st
import psycopg2
import os

# ======================
# 页面设置（必须最前）
# ======================
st.set_page_config(
    page_title="BlazinGM Dashboard",
    page_icon="🎮",
    layout="wide"
)

# ======================
# 数据库连接（Railway + Supabase）
# ======================
@st.cache_resource
def get_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        st.error("❌ DATABASE_URL not found")
        st.stop()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.stop()

conn = get_connection()
c = conn.cursor()

# ======================
# Session 初始化
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ======================
# 登录函数
# ======================
def login_page():
    # 页面标题
    st.markdown("## 🎮 BlazinGM")

    # 居中布局
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # 卡片背景
        st.markdown("""
        <div style="
            padding:25px;
            border-radius:12px;
            background:#1E222A;
            box-shadow:0px 4px 20px rgba(0,0,0,0.4);
        ">
        """, unsafe_allow_html=True)

        st.markdown("### 🔐 Login")

        # 登录
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            c.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (login_user, login_pass)
            )
            user = c.fetchone()

            if user:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.markdown("---")

        # 注册
        st.markdown("### Register")

        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")

        if st.button("Register"):
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (new_user, new_pass)
            )
            conn.commit()
            st.success("User registered!")

        st.markdown("</div>", unsafe_allow_html=True)

# ======================
# Admin 页面
# ======================
def admin_page():
    import pandas as pd

    st.title("🎮 BlazinGM Admin Dashboard")

    # 读取订单
    c.execute("SELECT * FROM orders")
    orders = c.fetchall()

    if orders:
        df = pd.DataFrame(orders, columns=["ID", "User", "Game", "Amount", "Status"])
        df["Amount"] = df["Amount"].astype(int)

        # ======================
        # 🔥 KPI 卡片
        # ======================
        total_orders = len(df)
        total_revenue = df["Amount"].sum()
        pending_orders = len(df[df["Status"] == "Pending"])
        completed_orders = len(df[df["Status"] == "Completed"])

        col1, col2, col3, col4 = st.columns(4)

        col1.markdown(f"""
        <div style="padding:20px; border-radius:10px; background:#1E222A">
        <h4>📦 Orders</h4>
        <h2>{total_orders}</h2>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div style="padding:20px; border-radius:10px; background:#1E222A">
        <h4>💰 Revenue</h4>
        <h2>RM {total_revenue}</h2>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
        <div style="padding:20px; border-radius:10px; background:#1E222A">
        <h4>⏳ Pending</h4>
        <h2>{pending_orders}</h2>
        </div>
        """, unsafe_allow_html=True)

        col4.markdown(f"""
        <div style="padding:20px; border-radius:10px; background:#1E222A">
        <h4>✅ Completed</h4>
        <h2>{completed_orders}</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ======================
        # 📊 图表
        # ======================
        st.subheader("📊 Order Status Overview")
        status_counts = df["Status"].value_counts()
        st.bar_chart(status_counts)

        st.markdown("---")

        # ======================
        # 📋 订单卡片 UI
        # ======================
        st.subheader("📋 All Orders")

        for order in orders:
            st.markdown(f"""
            <div style="
                padding:15px;
                border-radius:10px;
                background:#1E222A;
                margin-bottom:10px;
            ">
            <b>Order ID:</b> {order[0]}<br>
            <b>User:</b> {order[1]}<br>
            <b>Game:</b> {order[2]}<br>
            <b>Amount:</b> RM {order[3]}<br>
            <b>Status:</b> {order[4]}
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if order[4] != "Completed":
                    if st.button("✅ Complete", key=f"c{order[0]}"):
                        c.execute("UPDATE orders SET status='Completed' WHERE id=?", (order[0],))
                        conn.commit()
                        st.rerun()

            with col2:
                if st.button("❌ Delete", key=f"d{order[0]}"):
                    c.execute("DELETE FROM orders WHERE id=?", (order[0],))
                    conn.commit()
                    st.rerun()

    else:
        st.info("No orders yet")

# ======================
# 🎮 产品首页
# ======================
def product_page():
    st.subheader("🎮 Select Game")

    st.markdown("""
    <style>
    .game-card {
        border-radius:12px;
        overflow:hidden;
        background:#1E222A;
        padding:10px;
        text-align:center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .game-card:hover {
        transform: scale(1.03);
        box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
    }

    .game-title {
        margin-top:10px;
        font-size:16px;
        font-weight:bold;
    }
    </style>
    """, unsafe_allow_html=True)

    games = [
        ("Genshin Impact", "https://image.api.playstation.com/vulcan/ap/rnd/202508/2602/30935168a0f21b6710dc2bd7bb37c23ed937fb9fa747d84c.png"),
        ("MLBB", "https://play-lh.googleusercontent.com/sJtCcM4BsuwJbei9PSmBprb6V9_hdk1RHRSbccLD0xcM-klrZVVQ2RuWT2iOfAPo8dQZO1iwO7DGnwmYpsKJuQ"),
        ("PUBG Mobile", "https://play-lh.googleusercontent.com/_hITCaObfE2LSkWq9_ydYMmUXxVfexoRc5qA8GJy0GtSg_ee3ZKqwGPGa7KOjuG2j7E"),
        ("Honor of Kings", "https://play-lh.googleusercontent.com/hEm5NVeEv7UfFJaK8GZdfWe7p3DB_VvYx57qIEHbR0tMV_NToziH0Vbgd6CxLiWF-iURpAe-jsC_UGUDt0diPQ"),
    ]

    cols = st.columns(4)

    def game_card(title, image, key):
        st.markdown(f"""
        <div class="game-card">
            <img src="{image}" style="width:100%; border-radius:10px;">
            <div class="game-title">{title}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Top Up", key=key):
            st.session_state.selected_game = title

    for i, (name, img) in enumerate(games):
        with cols[i]:
            game_card(name, img, f"g{i}")

# ======================
# 👤 用户页面（完整版本）
# ======================
def user_page():
    st.title("🎮 BlazinGM Store")

    # ======================
    # 💰 Balance
    # ======================
    if st.session_state.logged_in:
        c.execute("SELECT balance FROM users WHERE username=?", (st.session_state.username,))
        balance = c.fetchone()[0]
        st.markdown(f"### 💰 Balance: RM {balance}")
    else:
        st.info("👀 You are browsing as guest")

    st.markdown("---")

    # ======================
    # 🎮 产品选择
    # ======================
    if "selected_game" not in st.session_state:
        st.subheader("Select Game")

        col1, col2, col3, col4 = st.columns(4)

        games = [
            ("Genshin Impact", "https://image.api.playstation.com/vulcan/ap/rnd/202508/2602/30935168a0f21b6710dc2bd7bb37c23ed937fb9fa747d84c.png"),
            ("MLBB", "https://play-lh.googleusercontent.com/sJtCcM4BsuwJbei9PSmBprb6V9_hdk1RHRSbccLD0xcM-klrZVVQ2RuWT2iOfAPo8dQZO1iwO7DGnwmYpsKJuQ"),
            ("PUBG Mobile", "https://play-lh.googleusercontent.com/_hITCaObfE2LSkWq9_ydYMmUXxVfexoRc5qA8GJy0GtSg_ee3ZKqwGPGa7KOjuG2j7E"),
            ("Honor of Kings", "https://play-lh.googleusercontent.com/hEm5NVeEv7UfFJaK8GZdfWe7p3DB_VvYx57qIEHbR0tMV_NToziH0Vbgd6CxLiWF-iURpAe-jsC_UGUDt0diPQ"),
        ]

        cols = [col1, col2, col3, col4]

        for i, (name, img) in enumerate(games):
            with cols[i]:
                st.image(img, use_container_width=True)
                st.markdown(f"**{name}**")

                if st.button("Top Up", key=f"game_{i}"):
                    st.session_state.selected_game = name
                    st.rerun()

        return

    # ======================
    # 🎯 充值页面
    # ======================
    game = st.session_state.selected_game

    if st.button("⬅ Back"):
        del st.session_state.selected_game
        st.rerun()

    st.subheader(f"🎯 Top Up - {game}")

    user_id = st.text_input("Enter Game UID")
    amount = st.selectbox("Select Amount", ["10", "20", "50", "100"])

    # ======================
    # 💳 下单
    # ======================
    if st.button("Confirm Top Up"):

        if not st.session_state.logged_in:
            st.warning("⚠️ Please login first")

        else:
            if user_id:

                c.execute("SELECT balance FROM users WHERE username=?", (st.session_state.username,))
                balance = c.fetchone()[0]

                if balance >= int(amount):

                    c.execute(
                        "UPDATE users SET balance = balance - ? WHERE username=?",
                        (int(amount), st.session_state.username)
                    )

                    c.execute(
                        "INSERT INTO orders (user_id, game, amount, status) VALUES (?, ?, ?, ?)",
                        (st.session_state.username, game, amount, "Pending")
                    )

                    conn.commit()

                    st.success(f"✅ Order placed! RM {amount} deducted")
                    st.rerun()

                else:
                    st.error("❌ Not enough balance")

            else:
                st.error("Please enter UID")

    st.markdown("---")

    # ======================
    # 📋 Orders
    # ======================
    if st.session_state.logged_in:
        st.subheader("My Orders")

        c.execute("SELECT * FROM orders WHERE user_id=?", (st.session_state.username,))
        orders = c.fetchall()

        if orders:
            for order in orders:
                st.markdown(f"""
                <div style="
                    padding:10px;
                    border-radius:8px;
                    background:#1E222A;
                    margin-bottom:8px;
                ">
                🎮 {order[2]} | 💰 RM {order[3]} | 📌 {order[4]}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No orders yet")
            
# ======================
# 主入口（最终优化版）
# ======================

# 初始化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ======================
# 🎨 Sidebar UI
# ======================
st.sidebar.markdown("## 🎮 BlazinGM")
st.sidebar.markdown("---")

# ======================
# 👤 所有人都可以浏览
# ======================
user_page()

# ======================
# 👑 Admin Panel（仅管理员）
# ======================
if st.session_state.logged_in and st.session_state.username == "admin":

    st.sidebar.markdown("### ⚙️ Admin Panel")

    page = st.sidebar.radio(
        "📂 Navigation",
        ["Dashboard", "Orders", "Users"]
    )

    # Dashboard
    if page == "Dashboard":
        admin_page()

    # Orders
    elif page == "Orders":
        st.markdown("## 📦 Orders Management")

        c.execute("SELECT * FROM orders")
        orders = c.fetchall()

        if orders:
            for order in orders:
                st.markdown(f"""
                <div style="
                    padding:15px;
                    border-radius:10px;
                    background:#1E222A;
                    margin-bottom:10px;
                ">
                <b>ID:</b> {order[0]}<br>
                <b>User:</b> {order[1]}<br>
                <b>Game:</b> {order[2]}<br>
                <b>Amount:</b> RM {order[3]}<br>
                <b>Status:</b> {order[4]}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No orders yet")

    # Users
    elif page == "Users":
        st.markdown("## 👤 User Management")

        c.execute("SELECT * FROM users")
        users = c.fetchall()

        if users:
            for user in users:
                st.markdown(f"""
                <div style="
                    padding:15px;
                    border-radius:10px;
                    background:#1E222A;
                    margin-bottom:10px;
                ">
                <b>User ID:</b> {user[0]}<br>
                <b>Username:</b> {user[1]}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No users found")

# ======================
# 🔐 登录 / 注册（未登录）
# ======================
if not st.session_state.logged_in:

    # 登录
    st.sidebar.markdown("### 🔐 Login")

    login_user = st.sidebar.text_input("Username", key="login_user")
    login_pass = st.sidebar.text_input("Password", type="password", key="login_pass")

    if st.sidebar.button("Login"):
        c.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (login_user, login_pass)
        )
        user = c.fetchone()

        if user:
            st.session_state.logged_in = True
            st.session_state.username = login_user
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid username or password")

    st.sidebar.markdown("---")

    # 注册（你缺的功能）
    st.sidebar.markdown("### 📝 Register")

    new_user = st.sidebar.text_input("New Username", key="reg_user")
    new_pass = st.sidebar.text_input("New Password", type="password", key="reg_pass")

    if st.sidebar.button("Register"):

        if new_user and new_pass:
            try:
                c.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (new_user, new_pass)
                )
                conn.commit()
                st.sidebar.success("✅ Registered! Please login")

            except Exception:
                st.sidebar.error("❌ Username already exists")

        else:
            st.sidebar.warning("Please fill all fields")

# ======================
# 🔓 已登录状态
# ======================
else:
    st.sidebar.markdown(f"👋 Welcome, **{st.session_state.username}**")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()