import base64
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

import pandas as pd
import psycopg2
import requests
from psycopg2 import extensions
import streamlit as st

from db_utils import ensure_customer_messages_table, save_admin_reply


st.set_page_config(
    page_title="BlazinGM",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #07111a;
        --panel: rgba(11, 21, 34, 0.92);
        --panel-2: rgba(15, 28, 43, 0.96);
        --line: rgba(110, 227, 255, 0.12);
        --text: #edf7ff;
        --muted: #90a8bc;
        --accent: #69e3ff;
        --accent-2: #b7fff4;
        --button-bg: linear-gradient(135deg, #68e2ff, #9bffd8);
        --button-text: #06111c;
        --button-shadow: 0 12px 28px rgba(71, 207, 255, 0.16);
    }

    html, body, [class*="css"] {
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    @keyframes fade-up {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes soft-float {
        0% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-4px);
        }
        100% {
            transform: translateY(0);
        }
    }

    @keyframes glow-shift {
        0% {
            box-shadow: 0 28px 70px rgba(0, 0, 0, 0.28);
        }
        50% {
            box-shadow: 0 32px 78px rgba(85, 106, 138, 0.22);
        }
        100% {
            box-shadow: 0 28px 70px rgba(0, 0, 0, 0.28);
        }
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(105, 227, 255, 0.14), transparent 24%),
            radial-gradient(circle at top right, rgba(155, 255, 216, 0.10), transparent 22%),
            linear-gradient(180deg, #040b12 0%, #08131d 44%, #0c1825 100%);
        color: var(--text);
        animation: fade-up 0.55s ease-out;
    }

    header[data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }

    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        display: none;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        padding-bottom: 2.2rem;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    .top-nav-wrap {
        margin-bottom: 1.35rem;
        padding: 0.82rem 0.95rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(10, 16, 24, 0.78);
        backdrop-filter: blur(14px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
    }

    .top-nav-brand {
        color: #f7fbff;
        font-size: 1.02rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .top-nav-sub {
        color: #8b9aac;
        font-size: 0.8rem;
        margin-top: 0.18rem;
    }

    .top-nav-menu {
        color: #9aa9b9;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .top-nav-wrap div[data-testid="stPopover"] > button {
        min-width: 44px;
        width: 44px;
        height: 44px;
        padding: 0 !important;
        border-radius: 999px !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        background: rgba(255, 255, 255, 0.03) !important;
        color: #eaf4ff !important;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.14);
    }

    .top-nav-wrap div[data-testid="stPopover"] > button:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }

    div[data-testid="stPopoverContent"] {
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(11, 18, 28, 0.98);
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.22);
        animation: fade-up 0.18s ease-out;
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea {
        background: rgba(8, 19, 31, 0.96);
        color: #edf7ff;
        border: 1px solid rgba(105, 227, 255, 0.14);
        border-radius: 12px;
    }

    .stButton > button {
        width: auto;
        min-width: 140px;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 12px;
        padding: 0.6rem 0.95rem;
        color: #dbe7f3;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.025);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.14);
        transition: transform 0.18s ease, filter 0.18s ease, box-shadow 0.18s ease;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #f4fbff !important;
        transform: translateY(-1px);
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.18);
    }

    .stFormSubmitButton > button {
        width: 100%;
        min-width: 0;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 12px;
        padding: 0.72rem 1rem;
        color: #dbe7f3;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.025);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.14);
        transition: transform 0.18s ease, filter 0.18s ease, box-shadow 0.18s ease;
    }

    .stFormSubmitButton > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #f4fbff !important;
        transform: translateY(-1px);
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.18);
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: linear-gradient(180deg, #fbfdff, #dfe9f3);
        color: #08111a !important;
        letter-spacing: 0.02em;
        box-shadow:
            0 1px 0 rgba(255, 255, 255, 0.45) inset,
            0 14px 32px rgba(99, 132, 170, 0.18);
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #ffffff, #e7eef6) !important;
        color: #07111a !important;
        transform: translateY(-2px);
        box-shadow:
            0 1px 0 rgba(255, 255, 255, 0.55) inset,
            0 18px 36px rgba(99, 132, 170, 0.22);
    }

    div[data-testid="stMetric"] {
        background:
            radial-gradient(circle at top right, rgba(105, 227, 255, 0.08), transparent 28%),
            linear-gradient(180deg, rgba(14, 24, 38, 0.96), rgba(10, 18, 29, 0.98));
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 0.9rem;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18);
    }

    .hero-card {
        overflow: hidden;
        padding: 4.1rem 3.5rem 2.8rem;
        border-radius: 22px;
        border: 1px solid rgba(105, 227, 255, 0.10);
        background:
            radial-gradient(circle at 80% 18%, rgba(105, 227, 255, 0.16), transparent 18%),
            linear-gradient(135deg, rgba(9, 17, 28, 0.95), rgba(8, 15, 25, 0.92));
        backdrop-filter: blur(10px);
        box-shadow: 0 18px 46px rgba(0, 0, 0, 0.22);
        margin-bottom: 1.6rem;
        animation: fade-up 0.65s ease-out;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.8fr);
        gap: 1.2rem;
        align-items: end;
    }

    .hero-kicker {
        display: inline-block;
        padding: 0.32rem 0.65rem;
        border-radius: 999px;
        background: rgba(105, 227, 255, 0.10);
        color: #aef8ff;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .hero-title {
        margin: 0.9rem 0 0.5rem;
        font-size: 3.3rem;
        line-height: 0.98;
        color: #f5fcff;
        max-width: 720px;
        letter-spacing: -0.03em;
    }

    .hero-text {
        max-width: 720px;
        color: #9ab0c2;
        font-size: 1rem;
        line-height: 1.72;
        margin-bottom: 0;
    }

    .hero-stats {
        display: grid;
        gap: 0.8rem;
    }

    .trust-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin: 1.05rem 0 1.35rem;
    }

    .trust-pill {
        padding: 0.9rem 1rem;
        border-radius: 16px;
        border: 1px solid rgba(105, 227, 255, 0.10);
        background: rgba(255, 255, 255, 0.03);
    }

    .trust-pill strong {
        display: block;
        color: #ebfbff;
        font-size: 0.98rem;
        margin-bottom: 0.16rem;
    }

    .trust-pill span {
        color: #93a8ba;
        font-size: 0.9rem;
        line-height: 1.55;
    }

    .hero-stat {
        padding: 0.95rem 1rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.04);
        animation: fade-up 0.75s ease-out;
    }

    .hero-stat strong {
        display: block;
        color: #ffffff;
        font-size: 1.1rem;
        margin-bottom: 0.18rem;
    }

    .hero-stat span {
        color: #d0d0d0;
        font-size: 0.92rem;
    }

    .section-title {
        margin: 1.1rem 0 0.2rem;
        font-size: 1.62rem;
        font-weight: 700;
        color: #eef8ff;
        letter-spacing: -0.02em;
    }

    .section-subtitle {
        color: #90a8bc;
        margin-bottom: 1rem;
        max-width: 760px;
    }

    .section-wrap {
        position: relative;
        margin-top: 1rem;
        animation: fade-up 0.55s ease-out;
    }

    .section-wrap::after {
        content: "";
        display: block;
        width: 88px;
        height: 2px;
        margin-top: 0.55rem;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(105, 227, 255, 0.95), rgba(155, 255, 216, 0.35));
    }

    .game-card,
    .glass-card,
    .account-card,
    .order-item {
        border: 1px solid rgba(255, 255, 255, 0.08);
        background:
            linear-gradient(180deg, rgba(11, 18, 28, 0.96), rgba(13, 22, 34, 0.98));
        box-shadow: 0 14px 36px rgba(0, 0, 0, 0.18);
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        animation: fade-up 0.65s ease-out;
    }

    .game-card {
        padding: 1.2rem;
        min-height: 385px;
        border-radius: 26px;
    }

    .game-card:hover,
    .glass-card:hover,
    .account-card:hover,
    .order-item:hover {
        transform: translateY(-3px);
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.22);
        border-color: rgba(255, 255, 255, 0.12);
    }

    .glass-card {
        padding: 1.2rem;
        border-radius: 22px;
    }

    .auth-shell {
        padding: 1.4rem 1.35rem 1.2rem;
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background:
            linear-gradient(180deg, rgba(11, 18, 28, 0.96), rgba(13, 22, 34, 0.98));
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18);
        max-width: 520px;
        margin: 0 auto;
    }

    .auth-stage {
        margin-top: 0.4rem;
    }

    .auth-side {
        min-height: 100%;
        padding: 2rem 1.8rem;
        border-radius: 30px;
        border: 1px solid rgba(207, 219, 235, 0.1);
        background:
            radial-gradient(circle at top right, rgba(196, 206, 218, 0.12), transparent 28%),
            linear-gradient(180deg, rgba(10, 20, 35, 0.88), rgba(7, 16, 29, 0.98));
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.16);
    }

    .auth-side-kicker {
        display: inline-block;
        margin-bottom: 0.85rem;
        padding: 0.3rem 0.72rem;
        border-radius: 999px;
        background: rgba(149, 163, 184, 0.16);
        color: #d7deea;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .auth-side-title {
        margin: 0;
        font-size: 2.2rem;
        line-height: 1.08;
        color: var(--text);
    }

    .auth-side-text {
        margin: 1rem 0 1.35rem;
        color: var(--muted);
        font-size: 0.98rem;
        line-height: 1.72;
    }

    .auth-points {
        display: grid;
        gap: 0.75rem;
    }

    .auth-point {
        padding: 0.85rem 0.95rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(255, 255, 255, 0.03);
        color: var(--muted);
    }

    .auth-point strong {
        display: block;
        margin-bottom: 0.18rem;
        color: var(--text);
        font-size: 0.96rem;
    }

    .auth-eyebrow {
        display: inline-block;
        margin-bottom: 0.7rem;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.05);
        color: #dce8f3;
        font-size: 0.78rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .auth-note {
        color: #90a8bc;
        margin: -0.25rem 0 0.95rem;
        font-size: 0.94rem;
        line-height: 1.55;
    }

    .auth-shell .section-title {
        margin-top: 0.2rem;
        font-size: 1.55rem;
    }

    .auth-shell .section-subtitle {
        margin-bottom: 0.5rem;
    }

    .auth-shell [data-testid="stTextInput"] {
        margin-bottom: 0.25rem;
    }

    .auth-actions {
        margin-top: 0.55rem;
    }

    .auth-form {
        display: grid;
        gap: 0.35rem;
    }

    .auth-divider {
        margin: 1rem 0 0.2rem;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
    }

    .auth-footer {
        margin-top: 0.85rem;
        color: #90a8bc;
        font-size: 0.96rem;
        text-align: center;
    }

    .sidebar-account-actions {
        margin-top: 0.15rem;
    }

    .sidebar-section {
        margin: 0.95rem 0 0.45rem;
        padding: 0.85rem 0.9rem 0.95rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        background: rgba(255, 255, 255, 0.025);
    }

    .sidebar-section-title {
        margin-bottom: 0.7rem;
        color: #ffffff;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .sidebar-user-chip {
        margin: 0.65rem 0 0.2rem;
        padding: 0.75rem 0.85rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: rgba(255, 255, 255, 0.04);
        color: #ffffff;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .sidebar-brand {
        padding: 0.95rem 1rem;
        margin-bottom: 1rem;
        border-radius: 20px;
        border: 1px solid rgba(105, 227, 255, 0.10);
        background:
            radial-gradient(circle at top right, rgba(105, 227, 255, 0.12), transparent 28%),
            linear-gradient(180deg, rgba(14, 29, 47, 0.96), rgba(9, 20, 35, 0.98));
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
        animation: fade-up 0.5s ease-out, soft-float 5.5s ease-in-out infinite;
    }

    .sidebar-brand-title {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
    }

    .sidebar-brand-subtitle {
        margin-top: 0.28rem;
        color: #8ba2b7;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    .game-title {
        margin: 0.95rem 0 0.18rem;
        font-size: 1.28rem;
        font-weight: 700;
        color: #eff8ff;
    }

    .product-image-link {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 0.2rem;
        text-decoration: none;
    }

    .product-image-link img {
        width: 150px;
        max-width: 100%;
        height: auto;
        display: block;
        transition: transform 0.2s ease, filter 0.2s ease;
    }

    .product-image-link:hover img {
        transform: translateY(-3px) scale(1.02);
        filter: brightness(1.04);
    }

    .game-price {
        display: inline-flex;
        align-items: center;
        padding: 0.34rem 0.68rem;
        border-radius: 999px;
        background: rgba(105, 227, 255, 0.12);
        color: #b8fff6;
        font-size: 0.84rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }

    .product-card-description {
        color: #8ba1b5;
        font-size: 0.95rem;
        line-height: 1.65;
        margin-bottom: 0.95rem;
    }

    .tap-hint {
        margin-top: 0.55rem;
        color: #7ef0ff;
        font-size: 0.84rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .game-meta,
    .tiny-label {
        color: #8da6ba;
    }

    .pill-row {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        margin-bottom: 0.9rem;
    }

    .pill {
        padding: 0.3rem 0.72rem;
        border-radius: 999px;
        border: 1px solid rgba(105, 227, 255, 0.10);
        background: rgba(255, 255, 255, 0.03);
        color: #b9d1e4;
        font-size: 0.8rem;
    }

    .product-copy {
        padding: 0.4rem 0.25rem;
    }

    .purchase-panel {
        margin-top: 1.1rem;
        padding: 1.1rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.025);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.16);
    }

    .purchase-label {
        color: #8ab4c6;
        font-size: 0.84rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .purchase-price {
        margin: 0.4rem 0 0.8rem;
        color: #f1fbff;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1;
    }

    .purchase-help {
        margin-top: 0.7rem;
        color: #8ea8bb;
        font-size: 0.92rem;
        line-height: 1.6;
    }

    .product-kicker {
        display: inline-block;
        padding: 0.34rem 0.7rem;
        border-radius: 999px;
        background: rgba(105, 227, 255, 0.10);
        color: #aef8ff;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .product-title {
        margin: 0.9rem 0 0.55rem;
        font-size: 2.45rem;
        line-height: 1.02;
        color: #eff8ff;
    }

    .product-description {
        color: #90a8bc;
        font-size: 0.98rem;
        line-height: 1.74;
        margin-bottom: 1rem;
    }

    .product-highlights {
        display: grid;
        gap: 0.7rem;
        margin: 1rem 0 1.15rem;
    }

    .product-option-label {
        margin: 1rem 0 0.5rem;
        color: #aef8ff;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .product-highlight {
        padding: 0.85rem 0.95rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.025);
        color: #95adbf;
    }

    .product-highlight strong {
        display: block;
        color: #f1f8ff;
        margin-bottom: 0.2rem;
    }

    .account-card,
    .order-item {
        padding: 1rem 1.1rem;
        border-radius: 20px;
        margin-bottom: 0.8rem;
        background: #ffffff;
    }

    .wallet-value {
        font-size: 2rem;
        font-weight: 700;
        color: #111111;
        margin: 0.35rem 0 0;
    }

    .tiny-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        overflow: hidden;
        background: rgba(11, 18, 28, 0.96);
        animation: fade-up 0.6s ease-out;
    }

    div[data-testid="stAlert"] {
        border-radius: 16px;
        animation: fade-up 0.35s ease-out;
    }

    @media (prefers-reduced-motion: reduce) {
        .stApp,
        .hero-card,
        .hero-stat,
        .section-wrap,
        .game-card,
        .glass-card,
        .account-card,
        .order-item,
        .sidebar-brand,
        div[data-testid="stDataFrame"],
        div[data-testid="stAlert"] {
            animation: none !important;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            transition: none !important;
        }
    }

    @media (max-width: 900px) {
        .hero-grid {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 2.55rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


PRODUCTS = [
    {
        "key": "ml",
        "name": "Mobile Legends",
        "name_zh": "无尽对决",
        "image": "images/ml.png",
        "price": 10,
        "price_text": "Top-up from RM10",
        "price_text_zh": "RM10 起充值",
        "price_options": [10, 20, 50, 100],
        "category": "MOBA",
        "category_zh": "多人竞技",
        "description": "Fast Mobile Legends top-ups for daily players, ranked grinders, and event hunters who want a quick checkout flow.",
        "description_zh": "为日常玩家、排位玩家和活动玩家提供更快速的无尽对决充值流程，减少下单等待时间。",
        "card_copy": "Fast recharge, clear pricing, and a direct route into checkout for repeat players.",
        "card_copy_zh": "充值更快、价格更清晰，帮助回购玩家更直接进入下单流程。",
        "highlights": [
            ("Instant diamond flow", "Designed for fast purchases with a simple order path."),
            ("Popular starter option", "Begin with RM10 and keep the checkout lightweight."),
            ("Player support ready", "Orders can be tracked from your account and support inbox."),
        ],
        "highlights_zh": [
            ("钻石到账更快", "针对快速购买场景设计，尽量缩短下单路径。"),
            ("热门入门面额", "从 RM10 开始，首单决策更轻松。"),
            ("售后追踪更方便", "订单可在账户与客服收件箱中持续查看。"),
        ],
        "tags": ["Fast Delivery", "SEA Favorite", "Starter RM10"],
        "tags_zh": ["快速到账", "东南亚热门", "RM10 入门"],
    },
    {
        "key": "pubg",
        "name": "PUBG Mobile",
        "name_zh": "PUBG Mobile",
        "image": "images/pubg.png",
        "price": 10,
        "price_text": "Top-up from RM10",
        "price_text_zh": "RM10 起充值",
        "price_options": [10, 25, 60, 120],
        "category": "Shooter",
        "category_zh": "射击",
        "description": "A clean purchase page for PUBG Mobile players who want UC top-ups without extra friction or clutter.",
        "description_zh": "为 PUBG Mobile 玩家提供更干净直接的 UC 充值页面，减少多余步骤与干扰。",
        "card_copy": "Simple UC purchase flow with straightforward pricing and quick order creation.",
        "card_copy_zh": "UC 购买流程更简单，价格直观，订单创建更快。",
        "highlights": [
            ("Quick UC orders", "Made for repeat purchases and event restocks."),
            ("Battle-ready pricing", "Starter pricing keeps the first purchase simple."),
            ("Order visibility", "Each order is stored with a clear reference number."),
        ],
        "highlights_zh": [
            ("UC 下单更快", "适合日常补货与活动期间重复购买。"),
            ("价格清晰直接", "用入门面额让首次购买更简单。"),
            ("订单编号可追踪", "每一笔订单都会保存清晰的参考编号。"),
        ],
        "tags": ["Instant UC", "Battle Ready", "Starter RM10"],
        "tags_zh": ["UC 快速到账", "战备充值", "RM10 入门"],
    },
    {
        "key": "hok",
        "name": "Honor Of Kings",
        "name_zh": "王者荣耀国际版",
        "image": "images/hok.png",
        "price": 10,
        "price_text": "Top-up from RM10",
        "price_text_zh": "RM10 起充值",
        "price_options": [10, 20, 40, 80],
        "category": "Competitive MOBA",
        "category_zh": "竞技 MOBA",
        "description": "Honor Of Kings top-up access with a cleaner storefront layout and a more focused product presentation.",
        "description_zh": "以更清爽的商品布局与更专注的产品展示方式，为玩家提供王者荣耀国际版充值体验。",
        "card_copy": "A focused product page with cleaner pricing and less friction before checkout.",
        "card_copy_zh": "商品页更聚焦，价格更清楚，下单前阻力更少。",
        "highlights": [
            ("Focused product page", "A clearer layout for browsing, support, and checkout."),
            ("Fast starter amount", "RM10 entry point for quick top-up decisions."),
            ("Integrated account flow", "Orders and wallet view stay under one user account."),
        ],
        "highlights_zh": [
            ("商品信息更聚焦", "浏览、售后与下单都集中在更清楚的布局里。"),
            ("快速入门面额", "从 RM10 开始，适合快速充值决策。"),
            ("账户流程一体化", "订单与钱包统一在同一个账户中查看。"),
        ],
        "tags": ["Popular MOBA", "Mobile First", "Starter RM10"],
        "tags_zh": ["热门 MOBA", "移动优先", "RM10 入门"],
    },
]


TRANSLATIONS = {
    "en": {
        "nav_subtitle": "Gaming wallet layer for premium top-up execution",
        "nav_admin": "Admin",
        "nav_flow": "Premium top-up flow",
        "nav_login": "Login",
        "nav_register": "Register",
        "nav_logout": "Logout",
        "nav_language": "Language",
        "hero_kicker": "Gaming Wallet Layer",
        "hero_text": "A futuristic gaming and fintech layer for modern top-ups. Fast order execution, cleaner pricing, and a more trusted payment journey.",
        "hero_stat_1_title": "Fast Execution",
        "hero_stat_1_body": "Move from product view to confirmed order with less friction.",
        "hero_stat_2_title": "Wallet + Ops",
        "hero_stat_2_body": "Storefront, account view, payments, and follow-up in one flow.",
        "trust_1_title": "Clear Pricing",
        "trust_1_body": "See the amount before checkout with no confusing flow.",
        "trust_2_title": "Fast Purchase Path",
        "trust_2_body": "Pick a product, choose an amount, and place the order in a few clicks.",
        "trust_3_title": "Trackable Orders",
        "trust_3_body": "Every purchase gets a clear reference for support, trust, and follow-up.",
        "home_title": "Popular Games",
        "home_subtitle": "Open a product page, choose an amount, and complete checkout in a few steps.",
        "open_product": "Open {name}",
        "open_product_hint": "Open product to continue",
        "product_overview_title": "Product Overview",
        "product_overview_subtitle": "A focused page for browsing the selected game before checkout.",
        "main_product_title": "Main Product",
        "main_product_subtitle": "A clearer preview of the selected title before checkout.",
        "product_caption": "Clear pricing. Fast order creation. Easy follow-up with order number.",
        "choose_amount": "Choose amount",
        "back_products": "Back To Products",
        "buy_now": "Buy Now - RM {amount}",
        "login_required_checkout": "Login required before checkout.",
        "signed_in_checkout": "Signed in. Your order will be created instantly after confirmation.",
        "purchase_help": "Secure flow, clear pricing, and trackable order reference. {message}",
        "please_login_first": "Please login first",
        "order_created_full": "Order created! Full order number: {order_no}",
        "order_created": "Order created!",
        "order_failed": "Order failed: {error}",
        "register_eyebrow": "Create Account",
        "register_title": "Register",
        "register_subtitle": "Create an account to save orders, wallet access, and faster future top-ups.",
        "register_note": "A short username and password are enough to get started.",
        "username": "Username",
        "password": "Password",
        "register_success": "Account created. You can now login.",
        "register_failed": "Register failed: {error}",
        "register_footer": "Already have an account? Use the profile menu to open Login.",
        "login_eyebrow": "Sign In",
        "login_title": "Login",
        "login_subtitle": "Access your wallet, order history, and purchase flow in one place.",
        "login_note": "Sign in to continue with faster checkout and trackable orders.",
        "login_invalid": "Invalid login",
        "login_failed": "Login failed: {error}",
        "login_footer": "New here? Use the profile menu to open Register.",
        "wallet_title": "Wallet",
        "wallet_subtitle": "Your account snapshot updates in real time.",
        "current_balance": "Current Balance",
        "orders_title": "My Orders",
        "orders_subtitle": "Recent purchases and their current processing status.",
        "order_no_label": "Full Order No",
        "amount_status": "Amount: RM {amount} | Status: {status}",
        "no_orders": "You have no orders yet.",
        "admin_only": "Admin access only",
        "admin_title": "Admin Dashboard",
        "admin_subtitle": "Track players, monitor orders, and update order status.",
        "users_title": "Users",
        "users_subtitle": "Registered players and their current balances.",
        "orders_admin_title": "Orders",
        "orders_admin_subtitle": "All orders across the platform.",
        "inbox_title": "Customer Inbox",
        "inbox_subtitle": "Structured customer messages captured from WhatsApp.",
        "no_customer_messages": "No customer messages yet.",
        "choose_customer_message": "Choose a customer message to reply",
        "customer_message": "Customer message",
        "reply_to_customer": "Reply to customer",
        "send_whatsapp_reply": "Send WhatsApp Reply",
        "reply_sent": "Reply sent to customer on WhatsApp.",
        "reply_failed": "Failed to send WhatsApp reply: {error}",
        "inbox_not_ready": "Customer inbox not ready yet: {error}",
        "update_status_title": "Update Order Status",
        "update_status_subtitle": "Adjust the status of an existing order.",
        "choose_order": "Choose an order",
        "new_status": "New status",
        "update_order_status": "Update Order Status",
        "order_status_updated": "Order status updated",
        "no_orders_yet": "No orders yet",
        "orders_no_id": "The orders table has no 'id' column, so status updates are disabled.",
        "admin_failed": "Admin dashboard failed: {error}",
        "session_signed_out": "This account was logged in on another device. You have been signed out.",
        "insufficient_balance": "Insufficient balance. Current wallet balance: RM {balance}",
        "metric_users": "Users",
        "metric_orders": "Orders",
        "metric_pending": "Pending Orders",
    },
    "zh": {
        "nav_subtitle": "面向高品质充值体验的游戏钱包平台",
        "nav_admin": "后台",
        "nav_flow": "高效充值流程",
        "nav_login": "登录",
        "nav_register": "注册",
        "nav_logout": "退出登录",
        "nav_language": "语言",
        "hero_kicker": "游戏钱包层",
        "hero_text": "面向现代玩家打造的未来感游戏与金融科技平台。下单更快，价格更清晰，支付体验更值得信赖。",
        "hero_stat_1_title": "快速下单",
        "hero_stat_1_body": "从商品查看到订单确认，用更少步骤完成购买。",
        "hero_stat_2_title": "钱包与运营整合",
        "hero_stat_2_body": "商城、账户、支付与售后跟进统一在一个流程中。",
        "trust_1_title": "价格透明",
        "trust_1_body": "结账前直接看到金额，不再经历混乱流程。",
        "trust_2_title": "购买路径更短",
        "trust_2_body": "选择商品、选择面额、提交订单，几步内完成。",
        "trust_3_title": "订单可追踪",
        "trust_3_body": "每一笔购买都会生成清晰编号，方便售后与查单。",
        "home_title": "热门游戏",
        "home_subtitle": "进入商品页，选择金额，然后用更少步骤完成充值。",
        "open_product": "查看 {name}",
        "open_product_hint": "进入商品页继续",
        "product_overview_title": "商品详情",
        "product_overview_subtitle": "在结账前更专注地查看当前选中的游戏商品。",
        "main_product_title": "主要商品",
        "main_product_subtitle": "在结账前更清晰地查看当前游戏商品。",
        "product_caption": "价格透明，下单更快，订单编号便于后续追踪。",
        "choose_amount": "选择面额",
        "back_products": "返回商品列表",
        "buy_now": "立即购买 - RM {amount}",
        "login_required_checkout": "结账前需要先登录。",
        "signed_in_checkout": "已登录。确认后系统会立即创建订单。",
        "purchase_help": "安全流程、清晰价格、可追踪订单编号。{message}",
        "please_login_first": "请先登录",
        "order_created_full": "订单创建成功，完整订单号：{order_no}",
        "order_created": "订单创建成功",
        "order_failed": "订单失败：{error}",
        "register_eyebrow": "创建账户",
        "register_title": "注册",
        "register_subtitle": "创建账户后可保存订单、查看钱包余额，并更快完成后续充值。",
        "register_note": "只需设置一个简短用户名和密码即可开始使用。",
        "username": "用户名",
        "password": "密码",
        "register_success": "账户创建成功，现在可以登录了。",
        "register_failed": "注册失败：{error}",
        "register_footer": "已有账户？可从右上角菜单进入登录。",
        "login_eyebrow": "账户登录",
        "login_title": "登录",
        "login_subtitle": "在一个页面中查看钱包、订单记录与购买流程。",
        "login_note": "登录后可更快结账，并持续追踪订单状态。",
        "login_invalid": "账号或密码错误",
        "login_failed": "登录失败：{error}",
        "login_footer": "还没有账户？可从右上角菜单进入注册。",
        "wallet_title": "钱包",
        "wallet_subtitle": "你的账户余额与状态会实时更新。",
        "current_balance": "当前余额",
        "orders_title": "我的订单",
        "orders_subtitle": "查看最近订单与当前处理状态。",
        "order_no_label": "完整订单号",
        "amount_status": "金额：RM {amount} | 状态：{status}",
        "no_orders": "你目前还没有订单。",
        "admin_only": "仅管理员可访问",
        "admin_title": "后台仪表盘",
        "admin_subtitle": "查看玩家、监控订单并更新订单状态。",
        "users_title": "用户",
        "users_subtitle": "已注册玩家与当前余额。",
        "orders_admin_title": "订单",
        "orders_admin_subtitle": "平台内的全部订单。",
        "inbox_title": "客户收件箱",
        "inbox_subtitle": "来自 WhatsApp 的客户结构化消息。",
        "no_customer_messages": "目前还没有客户消息。",
        "choose_customer_message": "选择一条客户消息进行回复",
        "customer_message": "客户消息",
        "reply_to_customer": "回复客户",
        "send_whatsapp_reply": "发送 WhatsApp 回复",
        "reply_sent": "已成功通过 WhatsApp 回复客户。",
        "reply_failed": "发送 WhatsApp 回复失败：{error}",
        "inbox_not_ready": "客户收件箱尚未准备好：{error}",
        "update_status_title": "更新订单状态",
        "update_status_subtitle": "调整现有订单的处理状态。",
        "choose_order": "选择订单",
        "new_status": "新状态",
        "update_order_status": "更新订单状态",
        "order_status_updated": "订单状态已更新",
        "no_orders_yet": "目前还没有订单",
        "orders_no_id": "orders 数据表没有 id 字段，因此暂时无法更新状态。",
        "admin_failed": "后台加载失败：{error}",
        "session_signed_out": "该账号已在其他设备登录，当前设备已被退出。",
        "insufficient_balance": "余额不足。当前钱包余额：RM {balance}",
        "metric_users": "用户数",
        "metric_orders": "订单数",
        "metric_pending": "待处理订单",
    },
}


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

if "selected_product" not in st.session_state:
    st.session_state["selected_product"] = PRODUCTS[0]["key"]

if "language" not in st.session_state:
    st.session_state["language"] = "en"


def t(key, **kwargs):
    language = st.session_state.get("language", "en")
    text = TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(
        key,
        TRANSLATIONS["en"].get(key, key),
    )
    return text.format(**kwargs) if kwargs else text


def product_text(product, field):
    language = st.session_state.get("language", "en")
    localized_key = f"{field}_zh" if language == "zh" else field
    return product.get(localized_key, product.get(field, ""))


def product_list(product, field):
    language = st.session_state.get("language", "en")
    localized_key = f"{field}_zh" if language == "zh" else field
    return product.get(localized_key, product.get(field, []))


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
    st.warning(t("session_signed_out"))
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
        f"""
        <div class="hero-card">
            <div class="hero-grid">
                <div>
                    <div class="hero-kicker">{t("hero_kicker")}</div>
                    <div class="hero-title">BlazinGM</div>
                    <div class="hero-text">
                        {t("hero_text")}
                    </div>
                </div>
                <div class="hero-stats">
                    <div class="hero-stat">
                        <strong>{t("hero_stat_1_title")}</strong>
                        <span>{t("hero_stat_1_body")}</span>
                    </div>
                    <div class="hero-stat">
                        <strong>{t("hero_stat_2_title")}</strong>
                        <span>{t("hero_stat_2_body")}</span>
                    </div>
                </div>
            </div>
            <div class="trust-strip">
                <div class="trust-pill">
                    <strong>{t("trust_1_title")}</strong>
                    <span>{t("trust_1_body")}</span>
                </div>
                <div class="trust-pill">
                    <strong>{t("trust_2_title")}</strong>
                    <span>{t("trust_2_body")}</span>
                </div>
                <div class="trust-pill">
                    <strong>{t("trust_3_title")}</strong>
                    <span>{t("trust_3_body")}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title, subtitle):
    st.markdown(
        f"""
        <div class="section-wrap">
            <div class="section-title">{title}</div>
            <div class="section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_auth_side(kicker, title, description, points):
    points_html = "".join(
        [
            f'<div class="auth-point"><strong>{heading}</strong>{body}</div>'
            for heading, body in points
        ]
    )
    st.markdown(
        f"""
        <div class="auth-side">
            <div class="auth-side-kicker">{kicker}</div>
            <div class="auth-side-title">{title}</div>
            <div class="auth-side-text">{description}</div>
            <div class="auth-points">{points_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_game_card(product):
    tags_html = "".join([f'<span class="pill">{tag}</span>' for tag in product_list(product, "tags")])
    image_left, image_center, image_right = st.columns([0.16, 0.68, 0.16])
    with image_center:
        st.image(product["image"], width=150)
    product_name = product_text(product, "name")
    if st.button(t("open_product", name=product_name), key=f"open_product_{product['key']}", use_container_width=True):
        navigate_to("Product", product["key"])
        st.rerun()
    st.markdown(f'<div class="game-title">{product_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="game-price">{product_text(product, "price_text")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="product-card-description">{product_text(product, "card_copy")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pill-row">{tags_html}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tap-hint">{t("open_product_hint")}</div>', unsafe_allow_html=True)


def get_product_by_key(product_key):
    for product in PRODUCTS:
        if product["key"] == product_key:
            return product
    return None


@st.cache_data(show_spinner=False)
def image_to_data_uri(image_path):
    image_file = Path(image_path)
    suffix = image_file.suffix.lower()
    mime_type = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(image_file.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def navigate_to(page, product_key=None):
    st.session_state["active_page"] = page
    if product_key:
        st.session_state["selected_product"] = product_key
        st.query_params.clear()
        st.query_params["product"] = product_key
    else:
        st.query_params.clear()


def logout_current_user():
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
    navigate_to("Home")


def render_top_nav():
    st.markdown('<div class="top-nav-wrap">', unsafe_allow_html=True)
    left, center, right = st.columns([1.6, 0.8, 0.85])
    with left:
        st.markdown(
            f"""
            <div class="top-nav-brand">BlazinGM</div>
            <div class="top-nav-sub">{t("nav_subtitle")}</div>
            """,
            unsafe_allow_html=True,
        )
    with center:
        language = st.selectbox(
            t("nav_language"),
            ["en", "zh"],
            index=0 if st.session_state["language"] == "en" else 1,
            format_func=lambda value: "EN" if value == "en" else "中文",
            key="top_nav_language",
            label_visibility="collapsed",
        )
        if language != st.session_state["language"]:
            st.session_state["language"] = language
            st.rerun()

        if st.session_state["is_admin"]:
            if st.button(t("nav_admin"), key="top_nav_admin", use_container_width=True):
                navigate_to("Admin")
                st.rerun()
        else:
            st.markdown(f'<div class="top-nav-menu">{t("nav_flow")}</div>', unsafe_allow_html=True)
    with right:
        if not st.session_state["user"]:
            with st.popover("", icon=":material/person_outline:", key="top_nav_account_menu", width="content"):
                if st.button(t("nav_login"), key="nav_dropdown_login", use_container_width=True):
                    navigate_to("Login")
                    st.rerun()
                if st.button(t("nav_register"), key="nav_dropdown_register", use_container_width=True):
                    navigate_to("Register")
                    st.rerun()
        else:
            with st.popover("", icon=":material/person_outline:", key="top_nav_profile_menu", width="content"):
                if st.session_state["is_admin"]:
                    if st.button(t("nav_admin"), key="nav_dropdown_admin", use_container_width=True):
                        navigate_to("Admin")
                        st.rerun()
                if st.button(t("nav_logout"), key="nav_dropdown_logout", use_container_width=True, type="primary"):
                    logout_current_user()
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_product_page(product):
    product_name = product_text(product, "name")
    highlights_html = "".join(
        [
            f'<div class="product-highlight"><strong>{title}</strong>{body}</div>'
            for title, body in product_list(product, "highlights")
        ]
    )
    price_options = product.get("price_options", [product["price"]])
    left, right = st.columns([0.95, 1.05], gap="large")
    with left:
        render_section(t("main_product_title"), t("main_product_subtitle"))
        preview_left, preview_center, preview_right = st.columns([0.08, 0.84, 0.08])
        with preview_center:
            st.image(product["image"], width=250)
        st.caption(t("product_caption"))
    with right:
        st.markdown('<div class="product-copy">', unsafe_allow_html=True)
        tags_html = "".join([f"<span class=\"pill\">{tag}</span>" for tag in product_list(product, "tags")])
        st.markdown(f'<div class="product-kicker">{product_text(product, "category")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="product-title">{product_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="product-description">{product_text(product, "description")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pill-row">{tags_html}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="product-highlights">{highlights_html}</div>', unsafe_allow_html=True)
        st.markdown('<div class="purchase-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="purchase-label">{t("choose_amount")}</div>', unsafe_allow_html=True)
        selected_price = st.radio(
            t("choose_amount"),
            price_options,
            index=0,
            key=f"price_option_{product['key']}",
            horizontal=True,
            format_func=lambda amount: f"RM {amount}",
            label_visibility="collapsed",
        )
        st.markdown(f'<div class="purchase-price">RM {selected_price}</div>', unsafe_allow_html=True)
        action_left, action_right = st.columns([0.9, 1.1])
        with action_left:
            if st.button(t("back_products"), key=f"back_product_{product['key']}", use_container_width=True):
                navigate_to("Home")
                st.rerun()
        with action_right:
            buy_now = st.button(
                t("buy_now", amount=selected_price),
                key=f"buy_product_{product['key']}",
                use_container_width=True,
                type="primary",
            )
        login_message = (
            t("login_required_checkout")
            if not st.session_state["user"]
            else t("signed_in_checkout")
        )
        st.markdown(
            f'<div class="purchase-help">{t("purchase_help", message=login_message)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if buy_now:
        if not st.session_state["user"]:
            st.warning(t("please_login_first"))
        else:
            try:
                order_no = create_order(
                    st.session_state["user"],
                    product_name,
                    selected_price,
                )
                if order_no:
                    st.success(t("order_created_full", order_no=order_no))
                else:
                    st.success(t("order_created"))
            except Exception as e:
                st.error(t("order_failed", error=e))


def end_card():
    st.markdown("</div>", unsafe_allow_html=True)


def get_user_balance(username):
    balance_row = fetch_one(
        "SELECT balance FROM users WHERE username=%s",
        (username,),
    )
    return balance_row[0] if balance_row else 0


def create_order(username, game_name, amount):
    try:
        reset_failed_transaction()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE username=%s AND balance >= %s RETURNING balance",
                (amount, username, amount),
            )
            remaining_balance = cursor.fetchone()
            if not remaining_balance:
                conn.rollback()
                current_balance = get_user_balance(username)
                raise ValueError(
                    t("insufficient_balance", balance=current_balance)
                )

            if order_numbers_enabled():
                order_no = generate_order_number()
                try:
                    cursor.execute(
                        "INSERT INTO orders (order_no, user_id, game, amount, status) VALUES (%s, %s, %s, %s, %s) RETURNING id, order_no",
                        (order_no, username, game_name, amount, "pending"),
                    )
                    result = cursor.fetchone()
                    conn.commit()
                    return result[1] if result and result[1] else order_no
                except psycopg2.errors.UndefinedColumn:
                    conn.rollback()
                    st.session_state["order_no_ready"] = False
                    return create_order(username, game_name, amount)

            cursor.execute(
                "INSERT INTO orders (user_id, game, amount, status) VALUES (%s, %s, %s, %s) RETURNING id",
                (username, game_name, amount, "pending"),
            )
            result = cursor.fetchone()
            conn.commit()
            return build_fallback_order_ref(result[0]) if result and result[0] is not None else None
    except Exception:
        conn.rollback()
        raise


def render_account_shell(title, subtitle):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section(title, subtitle)


def show_user_panel():
    if not st.session_state["user"]:
        return

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
    render_section(t("wallet_title"), t("wallet_subtitle"))
    st.markdown(
        f"""
        <div class="account-card">
            <div class="tiny-label">{t("current_balance")}</div>
            <div class="wallet-value">RM {balance}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_section(t("orders_title"), t("orders_subtitle"))
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
        st.info(t("no_orders"))
    end_card()


if st.session_state["user"] and not session_still_valid():
    force_logout_due_to_other_login()

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Home"

if st.session_state["active_page"] not in {"Home", "Login", "Register", "Admin", "Product"}:
    st.session_state["active_page"] = "Home"

requested_product = st.query_params.get("product")
if requested_product:
    product = get_product_by_key(requested_product)
    if product:
        st.session_state["selected_product"] = requested_product
        st.session_state["active_page"] = "Product"

render_top_nav()

choice = st.session_state["active_page"]


if choice == "Home":
    render_hero()
    render_section(t("home_title"), t("home_subtitle"))

    columns = st.columns(3)
    for column, product in zip(columns, PRODUCTS):
        with column:
            render_game_card(product)

elif choice == "Product":
    product = get_product_by_key(st.session_state["selected_product"])
    if not product:
        navigate_to("Home")
        st.rerun()
    render_section(t("product_overview_title"), t("product_overview_subtitle"))
    render_product_page(product)

elif choice == "Register":
    left, center, right = st.columns([1.1, 0.9, 1.1])
    with center:
        st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
        st.markdown(f'<div class="auth-eyebrow">{t("register_eyebrow")}</div>', unsafe_allow_html=True)
        render_section(t("register_title"), t("register_subtitle"))
        st.markdown(
            f'<div class="auth-note">{t("register_note")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="auth-form">', unsafe_allow_html=True)
        with st.form("register_page_form"):
            new_user = st.text_input(t("username"), key="page_register_user")
            new_pass = st.text_input(t("password"), type="password", key="page_register_password")
            register_clicked = st.form_submit_button(t("nav_register"), use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="auth-footer">{t("register_footer")}</div>', unsafe_allow_html=True)

        if register_clicked:
            try:
                execute_write(
                    "INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)",
                    (new_user, new_pass, 0),
                )
                st.success(t("register_success"))
            except Exception as e:
                st.error(t("register_failed", error=e))
        end_card()

elif choice == "Login":
    left, center, right = st.columns([1.1, 0.9, 1.1])
    with center:
        st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
        st.markdown(f'<div class="auth-eyebrow">{t("login_eyebrow")}</div>', unsafe_allow_html=True)
        render_section(t("login_title"), t("login_subtitle"))
        st.markdown(
            f'<div class="auth-note">{t("login_note")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="auth-form">', unsafe_allow_html=True)
        with st.form("login_page_form"):
            user = st.text_input(t("username"), key="page_login_user")
            password = st.text_input(t("password"), type="password", key="page_login_password")
            login_clicked = st.form_submit_button(t("nav_login"), use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="auth-footer">{t("login_footer")}</div>', unsafe_allow_html=True)

        if login_clicked:
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
                    navigate_to("Home")
                    st.rerun()
                else:
                    st.error(t("login_invalid"))
            except Exception as e:
                st.error(t("login_failed", error=e))
        st.markdown("</div>", unsafe_allow_html=True)

elif choice == "Admin":
    if not st.session_state["user"] or not st.session_state["is_admin"]:
        st.error(t("admin_only"))
        st.stop()

    try:
        render_hero()
        render_section(t("admin_title"), t("admin_subtitle"))

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
        col_a.metric(t("metric_users"), len(users_df))
        col_b.metric(t("metric_orders"), len(orders_df))
        col_c.metric(
            t("metric_pending"),
            int((orders_df["Status"] == "pending").sum()) if not orders_df.empty else 0,
        )

        left, right = st.columns([1.2, 1])
        with left:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section(t("users_title"), t("users_subtitle"))
            st.dataframe(users_df, use_container_width=True)
            end_card()

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section(t("orders_admin_title"), t("orders_admin_subtitle"))
            st.dataframe(orders_df, use_container_width=True)
            end_card()

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section(t("inbox_title"), t("inbox_subtitle"))
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
                    st.info(t("no_customer_messages"))
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
                        t("choose_customer_message"),
                        list(message_options.keys()),
                        key="customer_inbox_reply_select",
                    )
                    selected_message = message_options[selected_message_label]

                    st.text_area(
                        t("customer_message"),
                        value=selected_message["raw_message"],
                        height=120,
                        disabled=True,
                        key="customer_inbox_raw_message",
                    )

                    admin_reply_text = st.text_area(
                        t("reply_to_customer"),
                        value=selected_message["admin_reply"],
                        height=120,
                        key=f"customer_reply_text_{selected_message['id']}",
                    )

                    if st.button(t("send_whatsapp_reply"), key="send_customer_inbox_reply"):
                        try:
                            send_whatsapp_text_message(
                                selected_message["sender"],
                                admin_reply_text,
                            )
                            save_admin_reply(selected_message["id"], admin_reply_text)
                            st.success(t("reply_sent"))
                            st.rerun()
                        except Exception as e:
                            st.error(t("reply_failed", error=e))
            except Exception as e:
                st.info(t("inbox_not_ready", error=e))
            end_card()

        with right:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_section(t("update_status_title"), t("update_status_subtitle"))
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
                    selected_label = st.selectbox(t("choose_order"), list(order_options.keys()))
                    new_status = st.selectbox(
                        t("new_status"),
                        ["pending", "paid", "processing", "completed", "cancelled"],
                    )

                    if st.button(t("update_order_status"), key="admin_update_order"):
                        execute_write(
                            "UPDATE orders SET status=%s WHERE id=%s",
                            (new_status, order_options[selected_label]),
                        )
                        st.success(t("order_status_updated"))
                        st.rerun()
                else:
                    st.info(t("no_orders_yet"))
            except psycopg2.errors.UndefinedColumn:
                st.warning(t("orders_no_id"))
            end_card()
    except Exception as e:
        st.error(t("admin_failed", error=e))


if choice != "Admin":
    show_user_panel()
