import calendar
from datetime import date

import pandas as pd
import streamlit as st


def _cover_html(path, titulo):
    if path and str(path).startswith("http"):
        return f'<img src="{path}" title="{titulo}" />'
    return '<span class="cal-emoji">📚</span>'


def render_calendario(list_actividad):
    st.subheader("📅 Calendario visual")
    hoy = date.today()
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Año", min_value=2000, max_value=2100, value=hoy.year, step=1)
    with col2:
        month = st.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1)

    inicio = date(int(year), int(month), 1)
    ultimo_dia = calendar.monthrange(int(year), int(month))[1]
    fin = date(int(year), int(month), ultimo_dia)

    actividad = pd.DataFrame(list_actividad(str(inicio), str(fin)))
    st.markdown("""
    <style>
    .cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:12px}
    .cal-head{font-weight:800;text-align:center;color:#6b5b7a;padding:8px}
    .cal-day{min-height:135px;border:1px solid rgba(120,90,140,.18);border-radius:18px;background:rgba(255,255,255,.74);padding:10px;box-shadow:0 6px 20px rgba(40,20,60,.06)}
    .cal-empty{opacity:.35;background:rgba(245,240,250,.35)}
    .cal-num{font-weight:800;font-size:.92rem;margin-bottom:8px;color:#3c2d45}
    .cal-covers{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
    .cal-covers img{width:42px;height:58px;object-fit:cover;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.18)}
    .cal-emoji{display:inline-flex;width:42px;height:58px;align-items:center;justify-content:center;border-radius:8px;background:#f1e9f7}
    .cal-more{font-size:.78rem;margin-top:6px;color:#7b6a86;font-weight:700}
    </style>
    """, unsafe_allow_html=True)

    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    html = ['<div class="cal-grid">']
    for d in dias:
        html.append(f'<div class="cal-head">{d}</div>')

    cal = calendar.Calendar(firstweekday=0)
    if actividad.empty:
        por_fecha = {}
    else:
        actividad["fecha_dt"] = pd.to_datetime(actividad["fecha"], errors="coerce").dt.date
        por_fecha = {k: v.to_dict("records") for k, v in actividad.groupby("fecha_dt")}

    for day in cal.itermonthdates(int(year), int(month)):
        if day.month != int(month):
            html.append('<div class="cal-day cal-empty"></div>')
            continue
        items = por_fecha.get(day, [])
        covers = []
        for item in items[:4]:
            covers.append(_cover_html(item.get("portada_path"), item.get("titulo", "")))
        more = f'<div class="cal-more">+{len(items)-4} más</div>' if len(items) > 4 else ""
        html.append(f'<div class="cal-day"><div class="cal-num">{day.day}</div><div class="cal-covers">{"".join(covers)}</div>{more}</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)

    if not actividad.empty:
        st.markdown("### Detalle del mes")
        cols = [c for c in ["fecha", "titulo", "tipo", "tipo_actividad", "cantidad", "minutos", "mood", "comentario"] if c in actividad.columns]
        st.dataframe(actividad[cols], use_container_width=True)
    else:
        st.info("No hay actividad registrada en este mes.")
