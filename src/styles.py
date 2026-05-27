import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

        :root {
            --cream: #eef6ff;
            --paper: #ffffff;
            --ink: #0f172a;
            --muted: #475569;
            --blue: #2563eb;
            --blue-dark: #1e3a8a;
            --blue-soft: #dbeafe;
            --cyan-soft: #e0f2fe;
            --line: rgba(37, 99, 235, 0.18);
        }

        html, body, [class*="css"] {
            font-family: 'Nunito', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(191, 219, 254, 0.90), transparent 34%),
                radial-gradient(circle at bottom right, rgba(186, 230, 253, 0.84), transparent 28%),
                linear-gradient(180deg, #eff6ff 0%, #e0f2fe 100%);
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
            background: rgba(239, 246, 255, 0.94);
            border-right: 1px solid var(--line);
            box-shadow: 14px 0 40px rgba(30, 58, 138, 0.08);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--line);
            padding: 0.45rem;
            border-radius: 22px;
            box-shadow: 0 12px 35px rgba(30, 58, 138, 0.10);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 17px;
            padding: 0.62rem 0.9rem;
            color: var(--blue-dark) !important;
            font-weight: 900;
        }

        .stTabs [aria-selected="true"] {
            background: var(--blue-dark) !important;
            color: #ffffff !important;
        }

        .stTabs [aria-selected="true"] * {
            color: #ffffff !important;
        }

        .book-card {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.05rem;
            margin-bottom: 1rem;
            background: rgba(255, 255, 255, 0.90);
            box-shadow: 0 18px 45px rgba(30, 58, 138, 0.12);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }

        .book-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 26px 70px rgba(30, 58, 138, 0.18);
        }

        .book-card img {
            border-radius: 18px !important;
            box-shadow: 0 18px 35px rgba(30, 58, 138, 0.24);
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
            border: 1px solid rgba(37, 99, 235, 0.24);
            background: var(--blue-soft);
            color: var(--blue-dark);
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
                linear-gradient(135deg, rgba(255,255,255,0.94), rgba(219, 234, 254, 0.76));
            box-shadow: 0 20px 50px rgba(30, 58, 138, 0.12);
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
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1rem;
            box-shadow: 0 18px 45px rgba(30, 58, 138, 0.10);
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
            background: var(--blue-dark) !important;
            color: #ffffff !important;
            font-weight: 900 !important;
            box-shadow: 0 12px 28px rgba(30, 58, 138, 0.22);
        }

        .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
            background: var(--blue) !important;
            color: #ffffff !important;
        }

        .stButton > button *, .stDownloadButton > button *, .stLinkButton > a * {
            color: #ffffff !important;
        }

        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.96) !important;
            color: var(--ink) !important;
            border-radius: 18px !important;
            border-color: var(--line) !important;
            font-weight: 700;
        }

        .stSelectbox div[data-baseweb="select"] *, .stMultiSelect div[data-baseweb="select"] * {
            color: var(--ink) !important;
        }

        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background: #ffffff !important;
            color: var(--ink) !important;
        }

        div[role="option"] {
            color: var(--ink) !important;
            background: #ffffff !important;
            font-weight: 800 !important;
        }

        div[role="option"][aria-selected="true"], div[role="option"]:hover {
            background: var(--blue-dark) !important;
            color: #ffffff !important;
        }

        div[role="option"][aria-selected="true"] *, div[role="option"]:hover * {
            color: #ffffff !important;
        }

        .stRadio label, .stCheckbox label {
            color: var(--ink) !important;
            font-weight: 800;
        }

        .stSlider [data-baseweb="slider"] > div {
            color: var(--blue) !important;
        }

        .stDataFrame, [data-testid="stDataFrame"] {
            border-radius: 22px;
            overflow: hidden;
            border: 1px solid var(--line);
        }

        div[data-testid="stAlert"] {
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.88);
        }

        .small-muted {
            opacity: .88;
            font-size: .92rem;
            color: var(--muted);
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )