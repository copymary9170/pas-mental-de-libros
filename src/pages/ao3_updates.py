from datetime import date

import pandas as pd
import streamlit as st

import src.database as db
from src.ao3_utils import es_link_ao3, extraer_ao3_info


def _safe_int(value, default=0):
    try:
        if value is None or value == "" or value == "?":
            return default
        return int(value)
    except Exception:
        return default


def _ao3_link(obra):
    return obra.get("link_original") or obra.get("url_fuente") or ""


def _status(leidos, publicados, completo, revisado):
    if not revisado:
        return "🔴 Sin revisar", "sin_revisar"
    if completo and publicados <= leidos:
        return "🔵 Completo", "completo"
    pendientes = max(0, publicados - leidos)
    if pendientes <= 0:
        return "🟢 Al día", "al_dia"
    return f"🟡 {pendientes} pendientes", "pendientes"


def _progress(leidos, publicados):
    if publicados <= 0:
        return 0
    return min(100, int((leidos / publicados) * 100))


def _style():
    st.markdown(
        """
        <style>
        .ao3-card{border:1px solid rgba(147,197,253,.45);border-radius:18px;background:linear-gradient(180deg,#eff6ff,#dbeafe);padding:14px 16px;margin:12px 0;color:#0f172a;box-shadow:0 6px 20px rgba(15,23,42,.10)}
        .ao3-title{font-size:1.12rem;font-weight:900;color:#0f172a;margin-bottom:3px}.ao3-meta{font-size:.86rem;color:#1e3a8a;font-weight:700}.ao3-badges{margin-top:8px;font-size:.95rem}.ao3-small{font-size:.82rem;color:#334155;margin-top:5px}.ao3-progress{height:10px;background:#bfdbfe;border-radius:999px;overflow:hidden;margin:8px 0}.ao3-bar{height:10px;background:#1d4ed8;border-radius:999px}.ao3-link a{color:#1d4ed8;font-weight:800;text-decoration:none}.ao3-warn{background:#fef9c3;border-left:4px solid #eab308;border-radius:12px;padding:8px 10px;margin-top:8px;color:#422006}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_row(obra, revisar=False, cached=None):
    link = _ao3_link(obra)
    data = cached or {}
    if revisar:
        data = extraer_ao3_info(link)
    leidos = _safe_int(obra.get("capitulos_vistos") or obra.get("capitulo_actual"), 0)
    if data.get("ok"):
        publicados = _safe_int(data.get("capitulos_publicados"), 0)
        completo = bool(data.get("completo"))
        estado_txt, estado_key = _status(leidos, publicados, completo, True)
        pendientes = max(0, publicados - leidos)
        return {
            "obra": obra,
            "id": obra.get("id"),
            "titulo": data.get("titulo") or obra.get("titulo") or "Sin título",
            "autor": data.get("autor") or obra.get("autor") or "",
            "link": link,
            "leidos": leidos,
            "publicados": publicados,
            "totales": _safe_int(data.get("capitulos_totales"), 0),
            "pendientes": pendientes,
            "estado": estado_txt,
            "estado_key": estado_key,
            "actualizacion": data.get("fecha_actualizacion") or "",
            "publicacion": data.get("fecha_publicacion") or obra.get("fecha_publicacion") or "",
            "revisado": data.get("revisado_en") or "",
            "ok": True,
            "error": "",
            "completo": completo,
        }
    publicados_local = _safe_int(obra.get("capitulos_publicados") or obra.get("capitulo_total"), 0)
    pendientes = max(0, publicados_local - leidos)
    estado_txt, estado_key = _status(leidos, publicados_local, False, False)
    return {
        "obra": obra,
        "id": obra.get("id"),
        "titulo": obra.get("titulo") or "Sin título",
        "autor": obra.get("autor") or "",
        "link": link,
        "leidos": leidos,
        "publicados": publicados_local,
        "totales": _safe_int(obra.get("capitulo_total"), 0),
        "pendientes": pendientes,
        "estado": estado_txt,
        "estado_key": estado_key,
        "actualizacion": data.get("error") or obra.get("fecha_ultimo_capitulo_publicado") or "",
        "publicacion": obra.get("fecha_publicacion") or "",
        "revisado": "",
        "ok": False,
        "error": data.get("error") or "Pulsa revisar para consultar AO3.",
        "completo": False,
    }


def _apply_remote_metadata(row):
    obra_id = row.get("id")
    if not obra_id:
        return
    update = {
        "capitulos_publicados": row["publicados"],
        "ultimo_capitulo_publicado": row["publicados"],
        "fecha_ultimo_capitulo_publicado": row.get("actualizacion") or str(date.today()),
        "estado_publicacion": "Terminada" if row.get("completo") else "En emision",
        "ao3_tracking": 1,
        "motivo_estado": f"AO3 revisado {row.get('revisado') or date.today().isoformat()} · publicados {row['publicados']} · pendientes {row['pendientes']}",
    }
    obra = row.get("obra") or {}
    if not obra.get("autor") and row.get("autor"):
        update["autor"] = row.get("autor")
    if not obra.get("titulo") and row.get("titulo"):
        update["titulo"] = row.get("titulo")
    db.update_obra(obra_id, update)


def _mark_read(row, new_value, registrar=True):
    obra_id = row.get("id")
    if not obra_id:
        return
    new_value = max(0, int(new_value))
    update = {
        "capitulos_vistos": new_value,
        "capitulo_actual": new_value,
        "ultimo_capitulo_visto": new_value,
        "fecha_ultimo_capitulo_visto": str(date.today()),
    }
    if row.get("publicados"):
        update["capitulos_publicados"] = max(_safe_int(row.get("publicados")), new_value)
        update["ultimo_capitulo_publicado"] = max(_safe_int(row.get("publicados")), new_value)
    db.update_obra(obra_id, update)
    if registrar:
        db.add_actividad({
            "obra_id": obra_id,
            "fecha": str(date.today()),
            "tipo_actividad": "ao3_leido",
            "cantidad": max(1, new_value - _safe_int(row.get("leidos"), 0)),
            "minutos": 0,
            "mood": "",
            "comentario": f"AO3 marcado leído hasta capítulo {new_value}",
            "premio": "🔔 AO3",
        })


def _record_check_summary(total_pendientes, obras_pendientes):
    db.add_actividad({
        "obra_id": None,
        "fecha": str(date.today()),
        "tipo_actividad": "ao3_revision",
        "cantidad": int(total_pendientes),
        "minutos": 0,
        "mood": "",
        "comentario": f"Revisión AO3: {obras_pendientes} obras con pendientes, {total_pendientes} capítulos pendientes",
        "premio": "🔔 AO3",
    })


def _render_card(row):
    pct = _progress(row["leidos"], row["publicados"])
    fav = "❤️" if _safe_int(row["obra"].get("favorito"), 0) else ""
    fandom = row["obra"].get("fandom") or ""
    ship = row["obra"].get("ship") or ""
    extra = " · ".join([x for x in [row["autor"], fandom, ship] if x])
    st.markdown(
        f"""
        <div class="ao3-card">
          <div class="ao3-title">{row['estado']} {fav} · {row['titulo']}</div>
          <div class="ao3-meta">{extra}</div>
          <div class="ao3-progress"><div class="ao3-bar" style="width:{pct}%"></div></div>
          <div class="ao3-badges">📖 Leídos {row['leidos']} / Publicados {row['publicados']} · Pendientes {row['pendientes']} · {pct}%</div>
          <div class="ao3-small">Actualización AO3: {row.get('actualizacion') or 'N/D'} · Revisado: {row.get('revisado') or 'N/D'}</div>
          <div class="ao3-link"><a href="{row['link']}" target="_blank">Abrir en AO3</a></div>
          {f'<div class="ao3-warn">⚠️ {row["error"]}</div>' if row.get('error') else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ao3_updates(obras):
    st.subheader("🔔 Actualizaciones AO3")
    st.caption("Inbox manual de fanfics AO3: metadata pública, pendientes, progreso y acciones seguras. No descarga capítulos completos.")
    _style()

    obras_ao3 = []
    for obra in obras or []:
        if es_link_ao3(_ao3_link(obra)):
            obras_ao3.append(obra)

    if not obras_ao3:
        st.info("No hay obras con links de AO3 todavía.")
        st.caption("Guarda un link de AO3 en la obra para habilitar seguimiento.")
        return

    if "ao3_cache" not in st.session_state:
        st.session_state["ao3_cache"] = {}

    c1, c2, c3, c4 = st.columns(4)
    revisar_todo = c1.button("🔄 Revisar AO3 ahora", key="ao3_refresh_all")
    revisar_pendientes = c2.button("🟡 Revisar pendientes", key="ao3_refresh_pending")
    revisar_favoritos = c3.button("❤️ Revisar favoritos", key="ao3_refresh_favs")
    limpiar_cache = c4.button("🧹 Limpiar revisión", key="ao3_clear_cache")
    if limpiar_cache:
        st.session_state["ao3_cache"] = {}
        st.success("Cache AO3 limpiado.")

    rows = []
    for obra in obras_ao3:
        link = _ao3_link(obra)
        local_leidos = _safe_int(obra.get("capitulos_vistos") or obra.get("capitulo_actual"), 0)
        local_publicados = _safe_int(obra.get("capitulos_publicados") or obra.get("capitulo_total"), 0)
        local_pendiente = local_publicados > local_leidos
        should_check = revisar_todo or (revisar_pendientes and local_pendiente) or (revisar_favoritos and _safe_int(obra.get("favorito"), 0))
        cached = st.session_state["ao3_cache"].get(link)
        row = _build_row(obra, revisar=should_check, cached=cached)
        if should_check and row.get("ok"):
            st.session_state["ao3_cache"][link] = {
                "ok": True,
                "titulo": row["titulo"],
                "autor": row["autor"],
                "capitulos_publicados": row["publicados"],
                "capitulos_totales": row["totales"],
                "completo": row["completo"],
                "fecha_actualizacion": row["actualizacion"],
                "fecha_publicacion": row["publicacion"],
                "revisado_en": row["revisado"],
            }
            _apply_remote_metadata(row)
        elif should_check and not row.get("ok"):
            st.session_state["ao3_cache"][link] = {"ok": False, "error": row.get("error")}
        rows.append(row)

    total_pend = sum(_safe_int(r["pendientes"]) for r in rows if r["estado_key"] == "pendientes")
    obras_pend = sum(1 for r in rows if r["estado_key"] == "pendientes")
    al_dia = sum(1 for r in rows if r["estado_key"] == "al_dia")
    completas = sum(1 for r in rows if r["estado_key"] == "completo")
    sin_revisar = sum(1 for r in rows if r["estado_key"] == "sin_revisar")

    if revisar_todo or revisar_pendientes or revisar_favoritos:
        _record_check_summary(total_pend, obras_pend)
        st.success("Revisión AO3 completada y registrada en actividad/calendario.")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Obras AO3", len(rows))
    m2.metric("Pendientes", obras_pend)
    m3.metric("Capítulos pendientes", total_pend)
    m4.metric("Al día", al_dia)
    m5.metric("Sin revisar", sin_revisar)
    st.caption(f"🔵 completas: {completas}")

    with st.expander("Filtros y orden", expanded=False):
        f1, f2, f3 = st.columns(3)
        estado_filter = f1.multiselect("Estado", ["pendientes", "al_dia", "completo", "sin_revisar"], default=["pendientes", "al_dia", "completo", "sin_revisar"], key="ao3_estado_filter")
        solo_fav = f2.checkbox("Solo favoritos", key="ao3_only_favs")
        orden = f3.selectbox("Ordenar", ["Más pendientes", "Favoritos primero", "Título", "Última actualización", "Leídos"], key="ao3_sort")
        q = st.text_input("Buscar por título, autor, fandom o ship", key="ao3_query")

    filtered = [r for r in rows if r["estado_key"] in estado_filter]
    if solo_fav:
        filtered = [r for r in filtered if _safe_int(r["obra"].get("favorito"), 0)]
    if q.strip():
        qq = q.lower().strip()
        filtered = [r for r in filtered if qq in " ".join([str(r.get("titulo", "")), str(r.get("autor", "")), str(r["obra"].get("fandom", "")), str(r["obra"].get("ship", ""))]).lower()]
    if orden == "Más pendientes":
        filtered.sort(key=lambda r: r["pendientes"], reverse=True)
    elif orden == "Favoritos primero":
        filtered.sort(key=lambda r: (_safe_int(r["obra"].get("favorito"), 0), r["pendientes"]), reverse=True)
    elif orden == "Título":
        filtered.sort(key=lambda r: r["titulo"].lower())
    elif orden == "Última actualización":
        filtered.sort(key=lambda r: str(r.get("actualizacion") or ""), reverse=True)
    elif orden == "Leídos":
        filtered.sort(key=lambda r: r["leidos"], reverse=True)

    st.markdown("### 📥 Inbox AO3")
    if not filtered:
        st.info("No hay obras AO3 con esos filtros.")
        return

    for row in filtered:
        _render_card(row)
        a1, a2, a3, a4 = st.columns([1, 1, 1, 2])
        if a1.button("+1 leído", key=f"ao3_plus_{row['id']}"):
            _mark_read(row, row["leidos"] + 1)
            st.success(f"Actualizado: {row['titulo']} +1 capítulo leído.")
            st.rerun()
        if a2.button("Marcar al día", key=f"ao3_done_{row['id']}"):
            _mark_read(row, row["publicados"])
            st.success(f"Marcado al día: {row['titulo']}.")
            st.rerun()
        if a3.button("Guardar metadata", key=f"ao3_meta_{row['id']}"):
            _apply_remote_metadata(row)
            st.success(f"Metadata AO3 guardada: {row['titulo']}.")
            st.rerun()
        nuevo = a4.number_input("Leer hasta capítulo", min_value=0, max_value=max(row["publicados"], row["leidos"], 1), value=row["leidos"], step=1, key=f"ao3_until_{row['id']}")
        if st.button("Guardar lectura manual", key=f"ao3_save_until_{row['id']}"):
            _mark_read(row, nuevo)
            st.success(f"Lectura actualizada hasta capítulo {nuevo}.")
            st.rerun()

    st.markdown("### Tabla rápida")
    table = pd.DataFrame([{k: r[k] for k in ["titulo", "autor", "leidos", "publicados", "pendientes", "estado", "actualizacion", "revisado"]} for r in rows])
    st.dataframe(table, use_container_width=True)
