import calendar
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

TIPO_EMOJI = {
    "Libro": "📘",
    "Fanfiction": "🖋️",
    "Novela": "📖",
    "Novela ligera": "📗",
    "Manga": "🌸",
    "Manhwa": "💠",
    "Manhua": "🏮",
    "Webnovel": "🌐",
    "Comic": "💥",
    "Anime": "🎬",
    "Serie": "📺",
    "Kdrama": "💙",
    "Pelicula": "🎞️",
    "Documental": "🎥",
    "Podcast": "🎧",
    "Otro": "📚",
}


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _safe_text(value, default=""):
    if value is None:
        return default
    return str(value)


def _emoji_tipo(tipo):
    return TIPO_EMOJI.get(_safe_text(tipo), "📚")


def _prepare_df(rows):
    df = pd.DataFrame(rows or [])
    if df.empty:
        return df
    if "fecha" not in df.columns:
        df["fecha"] = ""
    df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    df = df.dropna(subset=["fecha_dt"]).copy()
    for col in ["minutos", "cantidad"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["titulo", "tipo", "tipo_actividad", "comentario", "mood", "portada_path"]:
        if col not in df.columns:
            df[col] = ""
    return df


def _cover_html(path, titulo, tipo):
    title = _safe_text(titulo).replace('"', "'")
    if path and str(path).startswith("http"):
        return f'<img src="{path}" title="{title}" />'
    return f'<span class="cal-emoji" title="{title}">{_emoji_tipo(tipo)}</span>'


def _day_summary(items):
    minutos = sum(_safe_int(i.get("minutos")) for i in items)
    caps = sum(_safe_int(i.get("cantidad")) for i in items)
    obras = len({i.get("titulo") for i in items if i.get("titulo")})
    return minutos, caps, obras


def _calc_streaks(df):
    if df.empty:
        return 0, 0
    days = sorted(set(df["fecha_dt"].dropna()))
    if not days:
        return 0, 0
    best = 1
    current = 1
    for prev, cur in zip(days, days[1:]):
        if cur == prev + timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1
    today = date.today()
    run = 0
    cursor = today
    day_set = set(days)
    while cursor in day_set:
        run += 1
        cursor -= timedelta(days=1)
    return run, best


def _style():
    st.markdown(
        """
        <style>
        .cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:12px}
        .cal-head{font-weight:900;text-align:center;color:#dbeafe;padding:8px;background:#1e3a8a;border-radius:12px}
        .cal-day{min-height:155px;border:1px solid rgba(147,197,253,.45);border-radius:18px;background:linear-gradient(180deg,#eff6ff,#dbeafe);padding:10px;box-shadow:0 6px 20px rgba(15,23,42,.12);color:#0f172a}
        .cal-day-today{outline:3px solid #38bdf8;background:linear-gradient(180deg,#dbeafe,#bfdbfe)}
        .cal-day-selected{outline:3px solid #facc15;background:linear-gradient(180deg,#fef9c3,#dbeafe)}
        .cal-empty{opacity:.35;background:rgba(219,234,254,.35)}
        .cal-num{font-weight:900;font-size:.95rem;margin-bottom:6px;color:#0f172a;display:flex;justify-content:space-between;gap:6px}
        .cal-metrics{font-size:.75rem;line-height:1.35;color:#1e3a8a;font-weight:750;margin-bottom:7px}
        .cal-covers{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
        .cal-covers img{width:38px;height:54px;object-fit:cover;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.22)}
        .cal-emoji{display:inline-flex;width:38px;height:54px;align-items:center;justify-content:center;border-radius:8px;background:#1e40af;color:white;font-size:1.25rem}
        .cal-more{font-size:.76rem;margin-top:6px;color:#1d4ed8;font-weight:800}
        .cal-chip{display:inline-block;border-radius:999px;background:#1e3a8a;color:white;padding:2px 7px;font-size:.7rem;font-weight:800}
        .timeline-card{border-left:4px solid #2563eb;background:#eff6ff;border-radius:12px;padding:10px 12px;margin:8px 0;color:#0f172a}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_month(df, year, month, selected_day):
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    html = ['<div class="cal-grid">']
    for d in dias:
        html.append(f'<div class="cal-head">{d}</div>')

    por_fecha = {}
    if not df.empty:
        por_fecha = {k: v.to_dict("records") for k, v in df.groupby("fecha_dt")}

    cal = calendar.Calendar(firstweekday=0)
    today = date.today()
    for day in cal.itermonthdates(int(year), int(month)):
        if day.month != int(month):
            html.append('<div class="cal-day cal-empty"></div>')
            continue
        items = por_fecha.get(day, [])
        minutos, caps, obras = _day_summary(items)
        classes = ["cal-day"]
        if day == today:
            classes.append("cal-day-today")
        if selected_day and day == selected_day:
            classes.append("cal-day-selected")
        covers = [_cover_html(i.get("portada_path"), i.get("titulo", ""), i.get("tipo", "")) for i in items[:5]]
        more = f'<div class="cal-more">+{len(items)-5} más</div>' if len(items) > 5 else ""
        metrics = ""
        if items:
            metrics = f'<div class="cal-metrics">⏱️ {minutos} min · 📍 {caps} caps · 📚 {obras} obras</div>'
        html.append(
            f'<div class="{" ".join(classes)}">'
            f'<div class="cal-num"><span>{day.day}</span><span class="cal-chip">{len(items)}</span></div>'
            f'{metrics}<div class="cal-covers">{"".join(covers)}</div>{more}</div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_daily_detail(df, selected_day):
    st.markdown("### Detalle diario")
    if not selected_day:
        st.info("Selecciona un día para ver su detalle.")
        return
    daily = df[df["fecha_dt"] == selected_day] if not df.empty else pd.DataFrame()
    st.caption(f"Día seleccionado: {selected_day.isoformat()}")
    if daily.empty:
        st.info("No hay actividad registrada ese día.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Minutos", int(daily["minutos"].sum()))
    c2.metric("Capítulos / eventos", int(daily["cantidad"].sum()))
    c3.metric("Obras", daily["titulo"].nunique())
    cols = [c for c in ["fecha", "titulo", "tipo", "tipo_actividad", "cantidad", "minutos", "mood", "comentario"] if c in daily.columns]
    st.dataframe(daily[cols].sort_values(["fecha", "titulo"]), use_container_width=True)


def _render_heatmap(df, inicio, fin):
    st.markdown("### Heatmap de actividad")
    days = pd.date_range(inicio, fin, freq="D")
    base = pd.DataFrame({"fecha_dt": [d.date() for d in days]})
    if df.empty:
        daily = base.assign(minutos=0, cantidad=0, obras=0)
    else:
        daily = df.groupby("fecha_dt").agg(minutos=("minutos", "sum"), cantidad=("cantidad", "sum"), obras=("titulo", "nunique")).reset_index()
        daily = base.merge(daily, on="fecha_dt", how="left").fillna(0)
    daily["semana"] = pd.to_datetime(daily["fecha_dt"]).dt.isocalendar().week.astype(int)
    daily["dia"] = pd.to_datetime(daily["fecha_dt"]).dt.day_name()
    daily["fecha"] = daily["fecha_dt"].astype(str)
    metric = st.selectbox("Métrica del heatmap", ["minutos", "cantidad", "obras"], key="cal_heat_metric")
    fig = px.density_heatmap(daily, x="semana", y="dia", z=metric, hover_data=["fecha", "minutos", "cantidad", "obras"], nbinsx=8)
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _render_by_work(df):
    st.markdown("### Vista por obra")
    if df.empty:
        st.info("No hay actividad para agrupar por obra.")
        return
    grouped = df.groupby(["titulo", "tipo"], dropna=False).agg(
        sesiones=("fecha_dt", "count"),
        dias=("fecha_dt", "nunique"),
        minutos=("minutos", "sum"),
        capitulos=("cantidad", "sum"),
    ).reset_index().sort_values(["minutos", "capitulos", "sesiones"], ascending=False)
    st.dataframe(grouped, use_container_width=True)
    fig = px.bar(grouped.head(20), x="titulo", y="minutos", hover_data=["tipo", "sesiones", "dias", "capitulos"])
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="Obra", yaxis_title="Minutos")
    st.plotly_chart(fig, use_container_width=True)


def _render_timeline(df):
    st.markdown("### Timeline cronológico")
    if df.empty:
        st.info("No hay actividad para mostrar en timeline.")
        return
    ordered = df.sort_values(["fecha_dt", "titulo"], ascending=[False, True])
    for _, row in ordered.head(150).iterrows():
        titulo = _safe_text(row.get("titulo"), "Sin título") or "Sin título"
        tipo = _safe_text(row.get("tipo"), "Otro") or "Otro"
        actividad = _safe_text(row.get("tipo_actividad"), "actividad") or "actividad"
        comentario = _safe_text(row.get("comentario"), "")
        st.markdown(
            f"""
            <div class="timeline-card">
                <strong>{row.get('fecha_dt')} · {_emoji_tipo(tipo)} {titulo}</strong><br/>
                <span>{tipo} · {actividad} · ⏱️ {_safe_int(row.get('minutos'))} min · 📍 {_safe_int(row.get('cantidad'))}</span><br/>
                <small>{comentario}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_calendario(list_actividad):
    st.subheader("📅 Calendario visual avanzado")
    st.caption("Mes real en cuadrícula, heatmap, vista por obra, timeline, filtros, detalle diario y rachas.")
    _style()

    hoy = date.today()
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Año", min_value=2000, max_value=2100, value=hoy.year, step=1, key="cal_year")
    with col2:
        month = st.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1, key="cal_month")
    with col3:
        modo = st.selectbox("Modo", ["Mes", "Heatmap", "Por obra", "Timeline"], key="cal_mode")

    inicio = date(int(year), int(month), 1)
    ultimo_dia = calendar.monthrange(int(year), int(month))[1]
    fin = date(int(year), int(month), ultimo_dia)

    actividad = _prepare_df(list_actividad(str(inicio), str(fin)))

    if actividad.empty:
        tipos = []
        titulos = []
    else:
        tipos = sorted([x for x in actividad["tipo"].dropna().unique().tolist() if str(x).strip()])
        titulos = sorted([x for x in actividad["titulo"].dropna().unique().tolist() if str(x).strip()])

    with st.expander("Filtros", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            tipos_sel = st.multiselect("Filtrar por tipo", tipos, default=tipos, key="cal_filter_tipo")
        with f2:
            obras_sel = st.multiselect("Filtrar por obra", titulos, default=titulos, key="cal_filter_obra")
        with f3:
            solo_notas = st.checkbox("Solo actividad con notas/comentarios", key="cal_solo_notas")

    filtrada = actividad.copy()
    if not filtrada.empty:
        if tipos_sel:
            filtrada = filtrada[filtrada["tipo"].isin(tipos_sel)]
        if obras_sel:
            filtrada = filtrada[filtrada["titulo"].isin(obras_sel)]
        if solo_notas:
            filtrada = filtrada[filtrada["comentario"].fillna("").astype(str).str.strip() != ""]

    racha_actual, mejor_racha = _calc_streaks(filtrada)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sesiones", 0 if filtrada.empty else len(filtrada))
    m2.metric("Minutos", 0 if filtrada.empty else int(filtrada["minutos"].sum()))
    m3.metric("Racha actual", f"{racha_actual} días")
    m4.metric("Mejor racha", f"{mejor_racha} días")

    selected_num = st.number_input("Día seleccionado", min_value=1, max_value=ultimo_dia, value=min(hoy.day, ultimo_dia) if hoy.year == int(year) and hoy.month == int(month) else 1, step=1, key="cal_selected_day")
    selected_day = date(int(year), int(month), int(selected_num))

    if modo == "Mes":
        _render_month(filtrada, int(year), int(month), selected_day)
        _render_daily_detail(filtrada, selected_day)
    elif modo == "Heatmap":
        _render_heatmap(filtrada, inicio, fin)
        _render_daily_detail(filtrada, selected_day)
    elif modo == "Por obra":
        _render_by_work(filtrada)
    elif modo == "Timeline":
        _render_timeline(filtrada)

    st.markdown("### Detalle del mes filtrado")
    if not filtrada.empty:
        cols = [c for c in ["fecha", "titulo", "tipo", "tipo_actividad", "cantidad", "minutos", "mood", "comentario"] if c in filtrada.columns]
        st.dataframe(filtrada[cols].sort_values(["fecha", "titulo"], ascending=[False, True]), use_container_width=True)
    else:
        st.info("No hay actividad registrada con los filtros actuales.")
