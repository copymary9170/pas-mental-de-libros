import calendar
from datetime import date, timedelta

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
    if path and str(path).startswith("http"):
        return f'<img src="{path}" title="{title}" />'
    return f'<span class="cal-emoji" title="{title}">{_emoji_tipo(tipo)}</span>'


def _day_summary(items):
    minutos = sum(_safe_int(i.get("minutos")) for i in items)
    caps = sum(_safe_int(i.get("cantidad")) for i in items)
    obras = len({i.get("titulo") for i in items if i.get("titulo")})
    moods = [i.get("mood") for i in items if i.get("mood")]
    premios = [i.get("premio") for i in items if i.get("premio")]
    return minutos, caps, obras, moods, premios


def _daily_table(df, inicio, fin):
    days = pd.date_range(inicio, fin, freq="D")
    base = pd.DataFrame({"fecha_dt": [d.date() for d in days]})
    if df.empty:
        return base.assign(minutos=0, cantidad=0, obras=0, sesiones=0)
    daily = df.groupby("fecha_dt").agg(
        minutos=("minutos", "sum"), cantidad=("cantidad", "sum"), obras=("titulo", "nunique"), sesiones=("titulo", "count")
    ).reset_index()
    return base.merge(daily, on="fecha_dt", how="left").fillna(0)


def _calc_streaks(df):
    if df.empty:
        return 0, 0
    days = sorted(set(df["fecha_dt"].dropna()))
    if not days:
        return 0, 0
    best = current = 1
    for prev, cur in zip(days, days[1:]):
        current = current + 1 if cur == prev + timedelta(days=1) else 1
        best = max(best, current)
    run = 0
    cursor = date.today()
    day_set = set(days)
    while cursor in day_set:
        run += 1
        cursor -= timedelta(days=1)
    return run, best


def _distribute(total, days):
    total = int(total or 0)
    days = max(1, int(days or 1))
    base = total // days
    extra = total % days
    return [base + (1 if i < extra else 0) for i in range(days)]


def _render_retroactive_activity(obras):
    st.markdown("### 🕰️ Registrar actividad pasada")
    st.caption("Úsalo cuando agregaste una obra y colocaste capítulos ya leídos de días anteriores. Esto alimenta Calendario y Wrapped sin fingir que todo pasó hoy.")
    if not obras:
        st.info("Agrega una obra primero para registrar actividad pasada.")
        return
    opciones = {f"#{o.get('id')} · {o.get('titulo') or 'Sin título'} · {o.get('tipo') or 'Tipo N/D'}": o for o in obras}
    with st.form("cal_retro_form"):
        obra_label = st.selectbox("Obra", list(opciones.keys()), key="cal_retro_obra")
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha_inicio = st.date_input("Desde", value=date.today() - timedelta(days=13), key="cal_retro_inicio")
        with c2:
            fecha_fin = st.date_input("Hasta", value=date.today(), key="cal_retro_fin")
        with c3:
            cantidad_total = st.number_input("Capítulos / episodios totales", min_value=1, value=1, step=1, key="cal_retro_cantidad")
        c4, c5, c6 = st.columns(3)
        with c4:
            minutos_total = st.number_input("Minutos totales opcional", min_value=0, value=0, step=10, key="cal_retro_minutos")
        with c5:
            mood = st.text_input("Mood opcional", placeholder="comfort, hype, triste...", key="cal_retro_mood")
        with c6:
            modo = st.selectbox("Modo", ["Repartir por días", "Todo en fecha final"], key="cal_retro_modo")
        comentario = st.text_area("Comentario", value="Registro retroactivo de lectura/visionado acumulado.", key="cal_retro_comentario")
        confirmar = st.checkbox("Confirmo que quiero crear actividad pasada en el calendario", key="cal_retro_confirm")
        submitted = st.form_submit_button("Guardar actividad pasada")
    if not submitted:
        return
    if not confirmar:
        st.warning("Marca la confirmación antes de guardar.")
        return
    if fecha_fin < fecha_inicio:
        st.error("La fecha final no puede ser anterior a la fecha inicial.")
        return
    obra = opciones[obra_label]
    if modo == "Todo en fecha final":
        fechas = [fecha_fin]
        cantidades = [int(cantidad_total)]
        minutos = [int(minutos_total or 0)]
    else:
        fechas = [fecha_inicio + timedelta(days=i) for i in range((fecha_fin - fecha_inicio).days + 1)]
        cantidades = _distribute(int(cantidad_total), len(fechas))
        minutos = _distribute(int(minutos_total or 0), len(fechas))
    creados = 0
    for f, cant, mins in zip(fechas, cantidades, minutos):
        if int(cant or 0) <= 0 and int(mins or 0) <= 0:
            continue
        db.add_actividad({
            "obra_id": obra.get("id"),
            "capitulo_id": None,
            "fecha": str(f),
            "tipo_actividad": "registro retroactivo",
            "cantidad": int(cant or 0),
            "minutos": int(mins or 0),
            "mood": mood.strip(),
            "comentario": comentario.strip(),
            "premio": "actividad pasada",
        })
        creados += 1
    st.success(f"Actividad pasada registrada: {creados} días para {obra.get('titulo') or 'la obra'}.")
    st.rerun()


def _style():
    st.markdown("""
    <style>
    .cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:12px}
    .cal-head{font-weight:900;text-align:center;color:#dbeafe;padding:8px;background:#1e3a8a;border-radius:12px}
    .cal-day{min-height:166px;border:1px solid rgba(147,197,253,.45);border-radius:18px;background:linear-gradient(180deg,#eff6ff,#dbeafe);padding:10px;box-shadow:0 6px 20px rgba(15,23,42,.12);color:#0f172a}
    .cal-day-0{background:linear-gradient(180deg,#f8fafc,#e2e8f0)} .cal-day-1{background:linear-gradient(180deg,#eff6ff,#dbeafe)} .cal-day-2{background:linear-gradient(180deg,#dbeafe,#bfdbfe)} .cal-day-3{background:linear-gradient(180deg,#bfdbfe,#93c5fd)} .cal-day-4{background:linear-gradient(180deg,#93c5fd,#60a5fa)}
    .cal-day-today{outline:3px solid #38bdf8}.cal-day-selected{outline:3px solid #facc15}.cal-empty{opacity:.35;background:rgba(219,234,254,.35)}
    .cal-num{font-weight:900;font-size:.95rem;margin-bottom:6px;color:#0f172a;display:flex;justify-content:space-between;gap:6px}.cal-metrics{font-size:.75rem;line-height:1.35;color:#1e3a8a;font-weight:750;margin-bottom:7px}
    .cal-covers{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.cal-covers img{width:38px;height:54px;object-fit:cover;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.22)}
    .cal-emoji{display:inline-flex;width:38px;height:54px;align-items:center;justify-content:center;border-radius:8px;background:#1e40af;color:white;font-size:1.25rem}.cal-more{font-size:.76rem;margin-top:6px;color:#1d4ed8;font-weight:800}
    .cal-chip{display:inline-block;border-radius:999px;background:#1e3a8a;color:white;padding:2px 7px;font-size:.7rem;font-weight:800}.cal-badges{font-size:.9rem;margin:4px 0}.timeline-card{border-left:4px solid #2563eb;background:#eff6ff;border-radius:12px;padding:10px 12px;margin:8px 0;color:#0f172a}
    @media(max-width:700px){.cal-grid{grid-template-columns:repeat(2,1fr);gap:8px}.cal-head{display:none}.cal-day{min-height:130px;padding:8px}.cal-covers img,.cal-emoji{width:30px;height:42px}.cal-metrics{font-size:.68rem}}
    </style>
    """, unsafe_allow_html=True)


def _badges(minutos, caps, obras, moods, premios, meta_min, meta_caps):
    b = []
    if minutos >= meta_min and meta_min > 0: b.append("✅")
    elif minutos > 0: b.append("🟡")
    else: b.append("⚪")
    if caps >= meta_caps and meta_caps > 0: b.append("🏆")
    if minutos >= 120: b.append("📚")
    if caps >= 5: b.append("🔥")
    if obras >= 3: b.append("🌈")
    if any("comfort" in str(m).lower() for m in moods): b.append("💧")
    if premios: b.append("🏅")
    return " ".join(b[:6])


def _render_month(df, year, month, selected_day, meta_min, meta_caps):
    html = ['<div class="cal-grid">']
    for d in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]:
        html.append(f'<div class="cal-head">{d}</div>')
    por_fecha = {k: v.to_dict("records") for k, v in df.groupby("fecha_dt")} if not df.empty else {}
    today = date.today()
    for day in calendar.Calendar(firstweekday=0).itermonthdates(int(year), int(month)):
        if day.month != int(month):
            html.append('<div class="cal-day cal-empty"></div>'); continue
        items = por_fecha.get(day, [])
        minutos, caps, obras, moods, premios = _day_summary(items)
        intensity = 0 if minutos == 0 and caps == 0 else 1 if minutos < 30 and caps < 2 else 2 if minutos < 90 and caps < 5 else 3 if minutos < 180 else 4
        classes = ["cal-day", f"cal-day-{intensity}"]
        if day == today: classes.append("cal-day-today")
        if selected_day and day == selected_day: classes.append("cal-day-selected")
        covers = [_cover_html(i.get("portada_path"), i.get("titulo", ""), i.get("tipo", "")) for i in items[:5]]
        more = f'<div class="cal-more">+{len(items)-5} más</div>' if len(items) > 5 else ""
        metrics = f'<div class="cal-metrics">📖 {caps} caps · ⏱️ {minutos} min · 📚 {obras} obras</div>' if items else ""
        badges = f'<div class="cal-badges">{_badges(minutos, caps, obras, moods, premios, meta_min, meta_caps)}</div>'
        html.append(f'<div class="{" ".join(classes)}"><div class="cal-num"><span>{day.day}</span><span class="cal-chip">{len(items)}</span></div>{metrics}{badges}<div class="cal-covers">{"".join(covers)}</div>{more}</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_daily_detail(df, selected_day):
    st.markdown("### Detalle diario")
    daily = df[df["fecha_dt"] == selected_day] if not df.empty else pd.DataFrame()
    st.caption(f"📅 {selected_day.isoformat()}")
    if daily.empty:
        st.info("No hay actividad registrada ese día."); return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Obras", daily["titulo"].nunique()); c2.metric("Capítulos/eventos", int(daily["cantidad"].sum())); c3.metric("Minutos", int(daily["minutos"].sum())); c4.metric("Premios", daily["premio"].replace("", pd.NA).dropna().nunique())
    cols = [c for c in ["fecha", "titulo", "tipo", "tipo_actividad", "cantidad", "minutos", "mood", "premio", "comentario"] if c in daily.columns]
    st.dataframe(daily[cols].sort_values(["fecha", "titulo"]), use_container_width=True)


def _render_heatmap(df, inicio, fin):
    st.markdown("### Heatmap de actividad")
    rango = st.radio("Rango", ["Mes actual", "Últimos 30 días", "Últimos 90 días", "Año completo"], horizontal=True, key="cal_heat_range")
    end = fin
    start = inicio if rango == "Mes actual" else end - timedelta(days=29) if rango == "Últimos 30 días" else end - timedelta(days=89) if rango == "Últimos 90 días" else date(end.year, 1, 1)
    daily = _daily_table(df[(df["fecha_dt"] >= start) & (df["fecha_dt"] <= end)] if not df.empty else df, start, end)
    daily["semana"] = pd.to_datetime(daily["fecha_dt"]).dt.isocalendar().week.astype(int); daily["dia"] = pd.to_datetime(daily["fecha_dt"]).dt.day_name(); daily["fecha"] = daily["fecha_dt"].astype(str)
    metric = st.selectbox("Métrica", ["minutos", "cantidad", "obras", "sesiones"], key="cal_heat_metric")
    fig = px.density_heatmap(daily, x="semana", y="dia", z=metric, hover_data=["fecha", "minutos", "cantidad", "obras", "sesiones"], nbinsx=20)
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _render_by_work(df):
    st.markdown("### Calendario por obra")
    if df.empty: st.info("No hay actividad para agrupar por obra."); return
    obras = sorted([x for x in df["titulo"].dropna().unique().tolist() if str(x).strip()])
    if not obras:
        st.info("No hay obras con título para agrupar."); return
    obra = st.selectbox("Selecciona una obra", obras, key="cal_work_select")
    sub = df[df["titulo"] == obra]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Días activos", sub["fecha_dt"].nunique()); c2.metric("Minutos", int(sub["minutos"].sum())); c3.metric("Capítulos", int(sub["cantidad"].sum())); c4.metric("Último día", str(max(sub["fecha_dt"])) if not sub.empty else "-")
    daily = sub.groupby("fecha_dt").agg(minutos=("minutos", "sum"), capitulos=("cantidad", "sum")).reset_index().sort_values("fecha_dt")
    daily["caps_acumulados"] = daily["capitulos"].cumsum(); daily["min_acumulados"] = daily["minutos"].cumsum()
    fig = px.line(daily, x="fecha_dt", y=["capitulos", "minutos", "caps_acumulados"], markers=True)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sub.sort_values("fecha_dt", ascending=False), use_container_width=True)


def _render_timeline(df):
    st.markdown("### Timeline cronológico")
    if df.empty: st.info("No hay actividad para mostrar en timeline."); return
    for _, row in df.sort_values(["fecha_dt", "titulo"], ascending=[False, True]).head(180).iterrows():
        comentario = _safe_text(row.get("comentario"), "")
        premio = _safe_text(row.get("premio"), "")
        st.markdown(f'<div class="timeline-card"><strong>{row.get("fecha_dt")} · {_emoji_tipo(row.get("tipo"))} {row.get("titulo") or "Sin título"}</strong><br/><span>{row.get("tipo")} · {row.get("tipo_actividad")} · ⏱️ {_safe_int(row.get("minutos"))} min · 📖 {_safe_int(row.get("cantidad"))}</span><br/><small>{row.get("mood") or ""} {" · 🏆 " + premio if premio else ""} {comentario}</small></div>', unsafe_allow_html=True)


def _render_week(df, selected_day):
    st.markdown("### Vista semanal")
    start = selected_day - timedelta(days=selected_day.weekday()); end = start + timedelta(days=6)
    week = _daily_table(df[(df["fecha_dt"] >= start) & (df["fecha_dt"] <= end)] if not df.empty else df, start, end)
    fig = px.bar(week, x="fecha_dt", y=["minutos", "cantidad", "obras"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(week, use_container_width=True)


def _render_year(df, year):
    st.markdown("### Vista anual")
    if df.empty: st.info("No hay actividad en este año. Usa Capítulos o Cronómetro para registrar actividad."); return
    tmp = df.copy(); tmp["mes"] = pd.to_datetime(tmp["fecha_dt"]).dt.month
    grouped = tmp.groupby("mes").agg(minutos=("minutos", "sum"), capitulos=("cantidad", "sum"), obras=("titulo", "nunique"), dias=("fecha_dt", "nunique")).reset_index()
    fig = px.bar(grouped, x="mes", y=["minutos", "capitulos", "obras", "dias"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(grouped, use_container_width=True)


def _render_progress(df):
    st.markdown("### Progreso acumulado")
    if df.empty: st.info("No hay datos para progreso acumulado."); return
    daily = df.groupby("fecha_dt").agg(capitulos=("cantidad", "sum"), minutos=("minutos", "sum"), obras=("titulo", "nunique")).reset_index().sort_values("fecha_dt")
    daily["capitulos acumulados"] = daily["capitulos"].cumsum(); daily["minutos acumulados"] = daily["minutos"].cumsum()
    fig = px.line(daily, x="fecha_dt", y=["capitulos acumulados", "minutos acumulados"], markers=True)
    st.plotly_chart(fig, use_container_width=True)


def _render_exports(df):
    st.markdown("### Exportar calendario")
    if df.empty: st.info("No hay datos para exportar."); return
    csv = df.drop(columns=["fecha_dt"], errors="ignore").to_csv(index=False).encode("utf-8")
    json_data = df.drop(columns=["fecha_dt"], errors="ignore").to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
    resumen = f"Resumen mensual\nSesiones: {len(df)}\nDías activos: {df['fecha_dt'].nunique()}\nMinutos: {int(df['minutos'].sum())}\nCapítulos/eventos: {int(df['cantidad'].sum())}\nObras: {df['titulo'].nunique()}"
    c1, c2, c3 = st.columns(3)
    c1.download_button("Descargar CSV", csv, "calendario_paz_mental.csv", "text/csv", key="cal_csv")
    c2.download_button("Descargar JSON", json_data, "calendario_paz_mental.json", "application/json", key="cal_json")
    c3.download_button("Resumen mensual TXT", resumen.encode("utf-8"), "resumen_calendario.txt", "text/plain", key="cal_txt")
    st.code(resumen)


def render_calendario(list_actividad, obras=None):
    st.subheader("📅 Calendario visual avanzado")
    st.caption("Bookmory + TV Time + diario de fandom: mes, semana, año, heatmap, timeline, metas, badges y exportes.")
    _style()
    obras = obras if obras is not None else db.list_obras()
    with st.expander("🕰️ Registrar actividad pasada", expanded=False):
        _render_retroactive_activity(obras)
    hoy = date.today()
    c1, c2, c3 = st.columns(3)
    with c1: year = st.number_input("Año", min_value=2000, max_value=2100, value=hoy.year, step=1, key="cal_year")
    with c2: month = st.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1, key="cal_month")
    with c3: modo = st.selectbox("Modo calendario", ["Mes", "Semana", "Año", "Heatmap", "Por obra", "Timeline", "Progreso", "Exportar"], key="cal_mode")
    inicio = date(int(year), int(month), 1); fin = date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])
    try:
        actividad = _prepare_df(list_actividad(str(date(int(year), 1, 1)), str(date(int(year), 12, 31))))
    except Exception as exc:
        st.error("No pude leer la actividad del calendario. Revisa Diagnóstico para ver la base de datos.")
        st.exception(exc)
        actividad = _empty_activity_df()
    tipos = sorted([x for x in actividad.get("tipo", pd.Series(dtype=str)).dropna().unique().tolist() if str(x).strip()]) if not actividad.empty else []
    titulos = sorted([x for x in actividad.get("titulo", pd.Series(dtype=str)).dropna().unique().tolist() if str(x).strip()]) if not actividad.empty else []
    with st.expander("Metas y filtros", expanded=False):
        g1, g2, g3, g4 = st.columns(4)
        with g1: meta_min = st.number_input("Meta diaria de minutos", min_value=0, value=30, step=5, key="cal_goal_min")
        with g2: meta_caps = st.number_input("Meta diaria de capítulos/eventos", min_value=0, value=1, step=1, key="cal_goal_caps")
        with g3: tipos_sel = st.multiselect("Tipo de obra", tipos, default=tipos, key="cal_filter_tipo")
        with g4: solo_notas = st.checkbox("Solo con notas/comentarios", key="cal_solo_notas")
        obras_sel = st.multiselect("Obra específica", titulos, default=titulos, key="cal_filter_obra")
        only_fanfic = st.checkbox("Solo fanfiction/AO3", key="cal_only_fanfic")
        only_portadas = st.checkbox("Solo días con portadas", key="cal_only_portadas")
    filtrada = actividad.copy()
    if not filtrada.empty:
        if tipos_sel: filtrada = filtrada[filtrada["tipo"].isin(tipos_sel)]
        if obras_sel: filtrada = filtrada[filtrada["titulo"].isin(obras_sel)]
        if solo_notas: filtrada = filtrada[filtrada["comentario"].fillna("").astype(str).str.strip() != ""]
        if only_fanfic: filtrada = filtrada[filtrada["tipo"].astype(str).str.contains("Fanfiction", case=False, na=False) | filtrada["etiquetas"].astype(str).str.contains("AO3|fanfic", case=False, na=False)]
        if only_portadas: filtrada = filtrada[filtrada["portada_path"].fillna("").astype(str).str.strip() != ""]
    mensual = filtrada[(filtrada["fecha_dt"] >= inicio) & (filtrada["fecha_dt"] <= fin)] if not filtrada.empty else filtrada
    racha_actual, mejor_racha = _calc_streaks(filtrada)
    daily_month = _daily_table(mensual, inicio, fin)
    dias_activos = int((daily_month["sesiones"] > 0).sum()) if not daily_month.empty else 0
    cumplidos = int((daily_month["minutos"] >= int(meta_min)).sum()) if int(meta_min) > 0 else 0
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Días activos", dias_activos); m2.metric("Días sin actividad", len(daily_month) - dias_activos); m3.metric("Minutos mes", 0 if mensual.empty else int(mensual["minutos"].sum())); m4.metric("Capítulos mes", 0 if mensual.empty else int(mensual["cantidad"].sum())); m5.metric("Meta diaria", f"{cumplidos}/{len(daily_month)}")
    s1, s2, s3 = st.columns(3)
    s1.metric("Racha actual", f"{racha_actual} días"); s2.metric("Mejor racha", f"{mejor_racha} días"); s3.metric("Promedio diario", round(float(daily_month["minutos"].mean()), 1) if not daily_month.empty else 0)
    selected_num = st.number_input("Día seleccionado", min_value=1, max_value=calendar.monthrange(int(year), int(month))[1], value=min(hoy.day, calendar.monthrange(int(year), int(month))[1]) if hoy.year == int(year) and hoy.month == int(month) else 1, step=1, key="cal_selected_day")
    selected_day = date(int(year), int(month), int(selected_num))
    if modo == "Mes": _render_month(mensual, int(year), int(month), selected_day, int(meta_min), int(meta_caps)); _render_daily_detail(mensual, selected_day)
    elif modo == "Semana": _render_week(mensual, selected_day); _render_daily_detail(mensual, selected_day)
    elif modo == "Año": _render_year(filtrada, int(year))
    elif modo == "Heatmap": _render_heatmap(filtrada, inicio, fin)
    elif modo == "Por obra": _render_by_work(filtrada)
    elif modo == "Timeline": _render_timeline(mensual)
    elif modo == "Progreso": _render_progress(mensual)
    elif modo == "Exportar": _render_exports(mensual)
    st.markdown("### Detalle del mes filtrado")
    if not mensual.empty:
        cols = [c for c in ["fecha", "titulo", "tipo", "tipo_actividad", "cantidad", "minutos", "mood", "premio", "comentario"] if c in mensual.columns]
        st.dataframe(mensual[cols].sort_values(["fecha", "titulo"], ascending=[False, True]), use_container_width=True)
    else:
        st.info("No hay actividad registrada con los filtros actuales.")
