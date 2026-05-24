import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

        :root {
            --cream: #fff8ee;
            --paper: #ffffff;
            --ink: #2f241d;
            --muted: #8a7567;
            --caramel: #c9834a;
            --caramel-dark: #9f6132;
            --peach: #ffe5ce;
            --sage: #d9ead3;
            --line: rgba(112, 84, 62, 0.16);
        }

        html, body, [class*="css"] {
            font-family: 'Nunito', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 217, 179, 0.85), transparent 34%),
                radial-gradient(circle at bottom right, rgba(217, 234, 211, 0.80), transparent 28%),
                linear-gradient(180deg, #fff8ee 0%, #f7ecdf 100%);
            color: var(--ink);
        }

        .main .block-container {
            padding-top: 1.2rem;
            padding-bottom: 4rem;
            max-width: 1180px;
        }

        h1 {
            font-size: 2.35rem !important;
            font-weight: 900 !important;
            letter-spacing: -0.04em;
            color: var(--ink) !important;
            margin-bottom: 0.15rem !important;
        }

        h2, h3 {
            color: var(--ink) !important;
            font-weight: 900 !important;
            letter-spacing: -0.03em;
        }

        p, label, span, div {
            color: var(--ink);
        }

        .stCaption, caption, small {
            color: var(--muted) !important;
        }

        [data-testid="stSidebar"] {
            background: rgba(255, 248, 238, 0.92);
            border-right: 1px solid var(--line);
            box-shadow: 14px 0 40px rgba(112, 84, 62, 0.08);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--line);
            padding: 0.45rem;
            border-radius: 22px;
            box-shadow: 0 12px 35px rgba(112, 84, 62, 0.08);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 17px;
            padding: 0.62rem 0.9rem;
            color: var(--muted);
            font-weight: 900;
        }

        .stTabs [aria-selected="true"] {
            background: #3b2a20;
            color: #fff8ee !important;
        }

        .book-card {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.05rem;
            margin-bottom: 1rem;
            background: rgba(255, 255, 255, 0.86);
            box-shadow: 0 18px 45px rgba(112, 84, 62, 0.12);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }

        .book-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 26px 70px rgba(112, 84, 62, 0.18);
        }

        .book-card img {
            border-radius: 18px !important;
            box-shadow: 0 18px 35px rgba(65, 45, 32, 0.24);
            aspect-ratio: 2 / 3;
            object-fit: cover;
        }

        .book-card h3 {
            font-size: 1.22rem !important;
            line-height: 1.15 !important;
            margin-bottom: 0.25rem !important;
        }

        .status-pill {
            display: inline-block;
            padding: 0.28rem 0.68rem;
            border-radius: 999px;
            border: 1px solid rgba(201, 131, 74, 0.20);
            background: #fff1df;
            color: #7c4a26;
            font-size: 0.76rem;
            font-weight: 900;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .hero-card {
            border: 1px solid var(--line);
            border-radius: 32px;
            padding: 1.25rem 1.4rem;
            margin: 0.65rem 0 1.05rem 0;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255, 229, 206, 0.72));
            box-shadow: 0 20px 50px rgba(112, 84, 62, 0.12);
        }

        .hero-title {
            font-size: 1.12rem;
            font-weight: 900;
            color: var(--ink);
            margin-bottom: 0.25rem;
        }

        .hero-subtitle {
            color: var(--muted);
            line-height: 1.55;
            font-weight: 700;
        }

        .shelf-title {
            font-size: 1.05rem;
            font-weight: 900;
            color: var(--ink);
            margin: 1rem 0 0.55rem;
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1rem;
            box-shadow: 0 18px 45px rgba(112, 84, 62, 0.10);
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            font-weight: 900;
        }

        [data-testid="stMetricValue"] {
            color: var(--ink) !important;
            font-weight: 900;
        }

        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            border-radius: 18px !important;
            border: 0 !important;
            background: #3b2a20 !important;
            color: #fff8ee !important;
            font-weight: 900 !important;
            box-shadow: 0 12px 28px rgba(59, 42, 32, 0.18);
        }

        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.92) !important;
            color: var(--ink) !important;
            border-radius: 18px !important;
            border-color: var(--line) !important;
            font-weight: 700;
        }

        .stSlider [data-baseweb="slider"] > div {
            color: var(--caramel) !important;
        }

        .stDataFrame, [data-testid="stDataFrame"] {
            border-radius: 22px;
            overflow: hidden;
            border: 1px solid var(--line);
        }

        div[data-testid="stAlert"] {
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.82);
        }

        .small-muted {
            opacity: .85;
            font-size: .92rem;
            color: var(--muted);
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
