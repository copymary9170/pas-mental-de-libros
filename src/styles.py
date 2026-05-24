import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(192, 132, 252, 0.20), transparent 32%),
                radial-gradient(circle at top right, rgba(56, 189, 248, 0.14), transparent 30%),
                linear-gradient(135deg, #0f172a 0%, #111827 45%, #020617 100%);
            color: #f8fafc;
        }

        .main .block-container {
            padding-top: 1.6rem;
            padding-bottom: 4rem;
            max-width: 1280px;
        }

        h1 {
            font-size: 2.7rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.05em;
            background: linear-gradient(90deg, #f8fafc, #c084fc, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.1rem !important;
        }

        h2, h3 {
            color: #f8fafc !important;
            letter-spacing: -0.03em;
        }

        .stCaption, caption, small {
            color: #cbd5e1 !important;
        }

        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.92);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: rgba(15, 23, 42, 0.64);
            border: 1px solid rgba(148, 163, 184, 0.16);
            padding: 0.45rem;
            border-radius: 999px;
            backdrop-filter: blur(18px);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.65rem 1rem;
            color: #cbd5e1;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(192, 132, 252, 0.95), rgba(56, 189, 248, 0.85));
            color: #020617 !important;
        }

        .book-card {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 26px;
            padding: 1.15rem;
            margin-bottom: 1.1rem;
            background:
                linear-gradient(135deg, rgba(30, 41, 59, 0.88), rgba(15, 23, 42, 0.82)),
                radial-gradient(circle at top left, rgba(192, 132, 252, 0.20), transparent 36%);
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(20px);
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }

        .book-card:hover {
            transform: translateY(-3px);
            border-color: rgba(192, 132, 252, 0.55);
            box-shadow: 0 28px 90px rgba(15, 23, 42, 0.45);
        }

        .book-card:before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, rgba(192, 132, 252, 0.18), transparent 38%, rgba(56, 189, 248, 0.12));
            pointer-events: none;
        }

        .status-pill {
            display: inline-block;
            padding: 0.28rem 0.72rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            background: rgba(15, 23, 42, 0.62);
            color: #e0f2fe;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        }

        .hero-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 32px;
            padding: 1.4rem 1.55rem;
            margin: 0.8rem 0 1.2rem 0;
            background:
                radial-gradient(circle at top left, rgba(192, 132, 252, 0.25), transparent 40%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.72));
            box-shadow: 0 30px 90px rgba(0,0,0,0.28);
        }

        .hero-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            color: #cbd5e1;
            line-height: 1.55;
        }

        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.72));
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 22px;
            padding: 1rem;
            box-shadow: 0 18px 60px rgba(0,0,0,0.22);
        }

        [data-testid="stMetricLabel"] {
            color: #cbd5e1 !important;
            font-weight: 700;
        }

        [data-testid="stMetricValue"] {
            color: #f8fafc !important;
            font-weight: 800;
        }

        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            border-radius: 999px !important;
            border: 1px solid rgba(192, 132, 252, 0.35) !important;
            background: linear-gradient(135deg, rgba(192, 132, 252, 0.95), rgba(56, 189, 248, 0.82)) !important;
            color: #020617 !important;
            font-weight: 800 !important;
            box-shadow: 0 14px 38px rgba(56, 189, 248, 0.15);
        }

        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
            background: rgba(15, 23, 42, 0.72) !important;
            color: #f8fafc !important;
            border-radius: 16px !important;
            border-color: rgba(148, 163, 184, 0.22) !important;
        }

        .stDataFrame, [data-testid="stDataFrame"] {
            border-radius: 20px;
            overflow: hidden;
        }

        div[data-testid="stAlert"] {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            background: rgba(15, 23, 42, 0.70);
        }

        .small-muted {
            opacity: .78;
            font-size: .92rem;
            color: #cbd5e1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
