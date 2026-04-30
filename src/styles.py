import streamlit as st

def apply_styles():
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.5rem;
            max-width: 1200px;
        }
        .book-card {
            border: 1px solid rgba(128,128,128,.25);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,.05);
        }
        .status-pill {
            display: inline-block;
            padding: .18rem .55rem;
            border-radius: 999px;
            border: 1px solid rgba(128,128,128,.35);
            font-size: .82rem;
            margin-right: .25rem;
        }
        .small-muted {
            opacity: .75;
            font-size: .9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
