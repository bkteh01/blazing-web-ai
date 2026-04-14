import streamlit as st
import psycopg2

# 页面设置
st.set_page_config(
    page_title="BlazinGM Dashboard",
    page_icon="🎮",
    layout="wide"
)

# ✅ 直接写死连接（测试用）
try:
    conn = psycopg2.connect(
        host="aws-1-ap-southeast-2.pooler.supabase.com",
        database="postgres",
        user="postgres.jpfqogcehayhetfdxubl",  # ❗重点
        password="BlazinGM@2026#Secure",
        port=5432,
        sslmode="require"
    )

    st.success("✅ Database connected successfully!")

except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    st.stop()

# ======================
# Session 初始化
# ======================
if "user" not in st.session_state:
    st.session_state["user"] = None

# ======================
# 标题
# ======================
st.title("🎮 BlazinGM Dashboard")

# ======================
# Sidebar 菜单
# ======================
menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

# ======================
# 注册
# ======================
if choice == "Register":
    st.subheader("🆕 Create Account")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        cursor.execute(
            "INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)",
            (new_user, new_pass, 0)
        )
        conn.commit()

        st.success("✅ Account created!")

# ======================
# 登录
# ======================
elif choice == "Login":
    st.subheader("🔐 Login")

    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (user, password)
        )
        result = cursor.fetchone()

        if result:
            st.session_state["user"] = user
            st.success("✅ Logged in!")
        else:
            st.error("❌ Invalid login")

# ======================
# 登录后系统
# ======================
if st.session_state["user"]:

    st.success(f"Welcome {st.session_state['user']} 👋")

    # ======================
    # 钱包
    # ======================
    st.subheader("💰 Wallet")

    cursor.execute(
        "SELECT balance FROM users WHERE username=%s",
        (st.session_state["user"],)
    )
    balance = cursor.fetchone()[0]

    st.write(f"Balance: RM {balance}")

    # ======================
    # 创建订单
    # ======================
    st.subheader("🎮 Create Order")

    game = st.text_input("Game Name")
    amount = st.number_input("Amount", min_value=1)

    if st.button("Submit Order"):
        cursor.execute(
            "INSERT INTO orders (user_id, game, amount, status) VALUES (%s, %s, %s, %s)",
            (st.session_state["user"], game, amount, "pending")
        )
        conn.commit()

        st.success("✅ Order created!")

    # ======================
    # 查看订单
    # ======================
    st.subheader("📄 My Orders")

    cursor.execute(
        "SELECT game, amount, status FROM orders WHERE user_id=%s",
        (st.session_state["user"],)
    )

    orders = cursor.fetchall()

    for o in orders:
        st.write(f"🎮 {o[0]} | 💰 RM{o[1]} | 📦 {o[2]}")

    # ======================
    # 登出
    # ======================
    if st.button("Logout"):
        st.session_state["user"] = None
        st.rerun()