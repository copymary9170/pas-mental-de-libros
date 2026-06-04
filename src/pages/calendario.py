import base64
import calendar
import mimetypes
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import src.database as db

TIPO_EMOJI = {
    "Libro": "📖", "Fanfiction": "✍️", "Novela": "📖", "Novela ligera": "📗",
    "Manga": "🌸", "Manhwa": "💠", "Manhua": "🏮", "Webnovel": "💜",
    "Comic": "💥", "Anime": "🌸", "Serie": "📺", "Kdrama": "💙",
    "Pelicula": "🎬", "Documental": "🎥", "Podcast": "🎧", "Otro": "📚",
}

CAL_COLUMNS = [
    "fecha", "fecha_dt", "minutos", "cantidad", "titulo", "tipo", "tipo_actividad",
    "comentario", "mood", "portada_path", "premio", "etiquetas",
]


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _safe_text(value, default=""):
    return default if value is None else str(value)


def _emoji_tipo(tipo):
    return TIPO_EMOJI.get(_safe_text(tipo), "📚")


def _image_src(path_or_url):
    raw = str(path_or_url or "").strip()
    if not raw:
        return ""
    if raw.startswith(("http://", "https://", "data:")):
        return raw
    path = Path(raw)
    if not path.exists():
        return ""
    try:
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{data}"
    except Exception:
        return ""


def _empty_activity_df():
    return pd.DataFrame({
        "fecha": pd.Series(dtype="str"),
        "fecha_dt": pd.Series(dtype="object"),
        "minutos": pd.Series(dtype="int"),
        "cantidad": pd.Series(dtype="int"),
        "titulo": pd.Series(dtype="str"),
        "tipo": pd.Series(dtype="str"),
        "tipo_actividad": pd.Series(dtype="str"),
        "comentario": pd.Series(dtype="str"),
        "mood": pd.Series(dtype="str"),
        "portada_path": pd.Series(dtype="str"),
        "premio": pd.Series(dtype="str"),
        "etiquetas": pd.Series(dtype="str"),
    })


def _prepare_df(rows):
    df = pd.DataFrame(rows or [])
    if df.empty:
        return _empty_activity_df()
    if "fecha" not in df.columns:
        df["fecha"] = ""
    df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    df = df.dropna(subset=["fecha_dt"]).copy()
    if df.empty:
        return _empty_activity_df()
    for col in ["minutos", "cantidad"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["titulo", "tipo", "tipo_actividad", "comentario", "mood", "portada_path", "premio", "etiquetas"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    return df


def _cover_html(path, titulo, tipo):
    title = _safe_text(titulo).replace('"', "'")
    src = _image_src(path)
    if src:
        return f'<img src="{src}" title="{title}" />'
    return f'<span class="cal-emoji" title="{title}">{_emoji_tipo(tipo)}</span>'
