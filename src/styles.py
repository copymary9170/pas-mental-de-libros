import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

        :root {
            --blue: #3F7EA6;
            --blue-dark: #2F6689;
            --cream: #F4EFE4;
            --paper: #FFFDF8;
            --ink: #666A6D;
            --muted: #9A9A96;
            --green: #A8BFA3;
            --turquoise: #78C7C4;
            --yellow: #F0CF4E;
            --line: rgba(63, 126, 166, .16);
            --shadow: 0 14px 34px rgba(111, 106, 94, .14);
        }

        html, body, [class*="css"] {
            font-family: 'Nunito', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 88% 18%, rgba(255,255,255,.18), transparent 18%),
                linear-gradient(180deg, var(--blue) 0 17.5rem, var(--cream) 17.5rem 100%);
            color: var(--ink);
        }

        header[data-testid="stHeader"] { background: transparent; }

        .main .block-container {
            max-width: 440px;
            padding-top: .55rem;
            padding-left: .9rem;
            padding-right: .9rem;
            padding-bottom: 7rem;
        }

        h1, h2, h3 { color: var(--ink) !important; font-weight: 900 !important; letter-spacing: -.035em; }
        p, label, span, div { color: var(--ink); }
        .stCaption, caption, small { color: rgba(255,255,255,.75) !important; font-weight: 800; }

        .app-hero {
            padding: .2rem 0 1.15rem;
            margin: 0 0 .2rem;
        }
        .app-hero h1 {
            color: rgba(255,255,255,.94) !important;
            font-size: 2.12rem !important;
            line-height: .95;
            margin: .25rem 0 .1rem !important;
        }
        .app-hero p {
            color: rgba(255,255,255,.66) !important;
            font-size: .98rem;
            font-weight: 800;
            margin: 0;
        }
        .hero-label {
            display: inline-flex;
            align-items: center;
            gap: .38rem;
            padding: .3rem .72rem;
            border-radius: 999px;
            background: rgba(255,255,255,.14);
            color: rgba(255,255,255,.9);
            font-size: .6rem;
            font-weight: 900;
            letter-spacing: .13em;
            text-transform: uppercase;
        }
        .hero-label::before {
            content: '👑';
            display: inline-grid;
            place-items: center;
            width: 1rem;
            height: 1rem;
            border-radius: 999px;
            background: var(--yellow);
            font-size: .58rem;
        }

        .pm-phone-shell { margin-top: -.15rem; }
        .pm-top-space { height: .2rem; }
        .pm-current-progress {
            display: flex;
            justify-content: space-between;
            color: var(--yellow);
            font-weight: 900;
            font-size: .86rem;
            margin: 0 .35rem .45rem;
        }
        .pm-current-progress span { color: var(--yellow); }
        .pm-reading-card {
            position: relative;
            background: var(--paper);
            border-radius: 7px;
            box-shadow: var(--shadow);
            padding: 1.55rem 1rem 1.15rem;
            min-height: 8rem;
            overflow: visible;
        }
        .pm-bookmark {
            position: absolute;
            top: 0;
            left: 2.25rem;
            width: 1rem;
            height: 1.75rem;
            background: var(--yellow);
            clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 78%, 0 100%);
        }
        .pm-reading-title {
            font-size: .98rem;
            font-weight: 900;
            color: #505357;
            max-width: 17rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-bottom: .65rem;
        }
        .pm-reading-body { display: flex; align-items: center; gap: .85rem; }
        .pm-cover-placeholder {
            width: 4.3rem;
            height: 5.6rem;
            border-radius: 4px;
            background: rgba(240,240,235,.86);
            box-shadow: 0 7px 20px rgba(116,108,92,.12);
            display: grid;
            place-items: center;
            color: #aaa;
            font-weight: 900;
        }
        .pm-reading-date, .pm-reading-status, .pm-reading-notes {
            color: #9A9A96;
            font-weight: 800;
            font-size: .82rem;
        }
        .pm-floating-actions {
            position: absolute;
            right: .7rem;
            bottom: -.9rem;
            border-radius: 999px;
            background: var(--blue);
            color: #fff;
            padding: .55rem .85rem;
            box-shadow: 0 8px 18px rgba(63,126,166,.28);
        }
        .pm-status-card, .pm-wide-card, .pm-mini-card, .pm-streak-card, .pm-chart-card {
            background: rgba(255,253,248,.95);
            border-radius: 8px;
            box-shadow: var(--shadow);
            border: 1px solid rgba(255,255,255,.75);
        }
        .pm-status-card {
            margin: 2.6rem 0 1.2rem;
            padding: .92rem 1rem;
            font-weight: 900;
            color: #757779;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pm-section-row { display:flex; justify-content:space-between; align-items:end; margin-top: 1.05rem; }
        .shelf-title {
            display: inline-block;
            font-size: 1.38rem;
            font-weight: 900;
            color: rgba(94,97,98,.78);
            border-bottom: .42rem solid rgba(63,126,166,.26);
            line-height: .78;
            margin: 0 0 .55rem;
        }
        .pm-section-more { color: var(--blue-dark); font-weight:900; font-size:.8rem; margin-bottom:.35rem; }
        .pm-plus-row {
            background: rgba(255,253,248,.55);
            border-radius: 999px;
            display: flex;
            justify-content: space-around;
            padding: .35rem;
            margin-bottom: .9rem;
        }
        .pm-plus {
            width: 3.1rem;
            height: 3.1rem;
            background: rgba(255,253,248,.95);
            border-radius: 999px;
            display: grid;
            place-items: center;
            color: #888;
            font-size: 1.65rem;
            font-weight: 500;
            box-shadow: 0 5px 14px rgba(112,105,92,.13);
        }
        .pm-mini-card {
            min-height: 4.7rem;
            padding: .82rem .85rem;
            margin-bottom: .72rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pm-wide-card {
            padding: .92rem 1rem;
            margin-bottom: .78rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pm-mini-title { font-weight: 900; font-size: .98rem; color: #6B6E70; line-height: 1.05; }
        .pm-mini-subtitle { font-weight: 800; font-size: .78rem; color: #A0A09A; margin-top: .14rem; }
        .pm-mini-icon { color: rgba(125,125,120,.22); font-size: 1.5rem; font-weight: 900; }
        .pm-streak-card { padding: .95rem 1rem; margin: .55rem 0 .82rem; }
        .pm-streak-title { font-weight:900; color:#65686B; font-size:1rem; }
        .pm-streak-subtitle { color:#A0A09A; font-weight:800; font-size:.78rem; }
        .pm-week-row { display:flex; justify-content:space-between; margin-top:.65rem; font-size:.68rem; font-weight:900; color:#999; }
        .pm-week-row span { color:#999; position:relative; padding-top:1.2rem; }
        .pm-week-row span::before { content:''; position:absolute; top:0; left:50%; transform:translateX(-50%); width:.82rem; height:.82rem; border-radius:50%; border:2px solid #ddd; background:#f7f4ec; }
        .pm-week-row span.active::before { background:var(--blue); border-color:var(--blue); }
        .pm-chart-card { padding: 1rem; min-height: 9.8rem; margin-bottom: .9rem; }
        .pm-bar-wrap { height: 6rem; display:flex; align-items:end; justify-content:center; border-bottom: .42rem solid rgba(140,140,135,.22); border-radius:999px; margin-top:.8rem; }
        .pm-bar { width: .72rem; background: var(--blue); border-radius: 999px 999px 0 0; }
        .pm-year-chip { width:3rem; height:3rem; border-radius:50%; border:2px dotted rgba(160,160,154,.45); display:grid; place-items:center; color:#C0BDB2; font-weight:900; font-size:.72rem; margin:.35rem 0 1rem; }
        .pm-tool-strip { display:flex; gap:.5rem; overflow-x:auto; padding:.7rem 0 1.2rem; }
        .pm-tool-strip div { flex:0 0 auto; background:rgba(255,253,248,.92); border-radius:999px; padding:.55rem .85rem; box-shadow:var(--shadow); font-weight:900; font-size:.78rem; color:#6B6E70; }

        .pm-home-card, .hero-card, .book-card, [data-testid="stMetric"], div[data-testid="stAlert"], div[data-testid="stForm"] {
            background: rgba(255,253,248,.95) !important;
            border: 1px solid rgba(255,255,255,.75) !important;
            border-radius: 10px !important;
            box-shadow: var(--shadow);
        }
        [data-testid="stMetric"] { padding:.72rem !important; }
        [data-testid="stMetricLabel"] { color:#969893 !important; font-weight:900; font-size:.72rem; }
        [data-testid="stMetricValue"] { color:#696C6F !important; font-weight:900; font-size:1.08rem !important; }

        .stTabs [data-baseweb="tab-list"] {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            z-index: 999;
            max-width: 440px;
            margin: 0 auto;
            gap: .12rem;
            background: rgba(255,253,248,.96);
            border-radius: 24px 24px 0 0;
            padding: .5rem .55rem .45rem;
            box-shadow: 0 -8px 25px rgba(111,106,94,.16);
            overflow-x: auto;
            border: 1px solid rgba(255,255,255,.8);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: .55rem .7rem;
            color: #8A8D8E !important;
            font-weight: 900;
            font-size: .78rem;
            min-width: fit-content;
        }
        .stTabs [aria-selected="true"] { background: var(--blue) !important; color:#fff !important; }
        .stTabs [aria-selected="true"] * { color:#fff !important; }

        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            border-radius: 999px !important;
            border: 0 !important;
            background: var(--blue) !important;
            color: #ffffff !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 22px rgba(63,126,166,.24);
        }
        .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover { background: var(--blue-dark) !important; color:#fff !important; }
        .stButton > button *, .stDownloadButton > button *, .stLinkButton > a * { color:#fff !important; }

        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
            background: rgba(255,253,248,.96) !important;
            color: var(--ink) !important;
            border-radius: 14px !important;
            border-color: rgba(63,126,166,.18) !important;
            font-weight: 800;
        }
        .stSelectbox div[data-baseweb="select"] *, .stMultiSelect div[data-baseweb="select"] * { color: var(--ink) !important; }
        div[data-baseweb="popover"], div[data-baseweb="menu"] { background: var(--paper) !important; color: var(--ink) !important; }
        div[role="option"] { color: var(--ink) !important; background: var(--paper) !important; font-weight: 800 !important; }
        div[role="option"][aria-selected="true"], div[role="option"]:hover { background: var(--blue) !important; color:#fff !important; }
        div[role="option"][aria-selected="true"] *, div[role="option"]:hover * { color:#fff !important; }
        .stRadio label, .stCheckbox label { color: var(--ink) !important; font-weight: 800; }
        .stDataFrame, [data-testid="stDataFrame"] { border-radius: 14px; overflow:hidden; border: 1px solid var(--line); }
        div[data-testid="stAlert"] { border-radius: 12px; }

        @media (min-width: 700px) {
            .main .block-container { max-width: 520px; }
            .stTabs [data-baseweb="tab-list"] { max-width: 520px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
