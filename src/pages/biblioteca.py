import unicodedata
from datetime import date

import pandas as pd
import streamlit as st

import src.database as db

ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _norm(text):
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def _progress(row):
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    if publicados <= 0:
        return 0
    return min(100, int((vistos / publicados) * 100))


def _pending(row):
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    return max(0, publicados - vistos)


def _fmt_time(mins):
    mins = _safe_int(mins, 0)
    h, m = divmod(mins, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def _style():
    st.markdown("""
    <style>
    .lib-card{border:1px solid rgba(147,197,253,.45);border-radius:18px;background:linear-gradient(180deg,#eff6ff,#dbeafe);padding:14px;margin:10px 0;color:#0f172a;box-shadow:0 6px 20px rgba(15,23,42,.10)}
    .lib-title{font-weight:900;font-size:1.05rem;color:#0f172a}.lib-meta{font-size:.86rem;color:#1e3a8a;font-weight:750}.lib-small{font-size:.82rem;color:#334155;margin-top:4px}.lib-progress{height:10px;background:#bfdbfe;border-radius:999px;overflow:hidden;margin:8px 0}.lib-bar{height:10px;background:#1d4ed8;border-radius:999px}.lib-badges{margin-top:6px;font-size:.9rem}.lib-cover{width:70px;height:102px;object-fit:cover;border-radius:12px;box-shadow:0 6px 18px rgba(15,23,42,.2);float:left;margin-right:12px}.lib-empty{width:70px;height:102px;border-radius:12px;background:#1e3a8a;color:white;display:flex;align-items:center;justify-content:center;font-size:2rem;float:left;margin-right:12px}.kanban-col{background:#eff6ff;border-radius:16px;padding:10px;min-height:200px}.quality-box{background:#f8fafc;border-left:4px solid #2563eb;border-radius:12px;padding:10px;margin:8px 0;color:#0f172a}
    </style>
    """, unsafe_allow_html=True)


def _badges(row):
    badges = []
    if _safe_int(row.get("favorito"), 0): badges.append("❤️")
    if row.get("ao3_work_id") or _safe_int(row.get("ao3_tracking"), 0): badges.append("🔔 AO3")
    if _pending(row) > 0: badges.append(f"🟡 {_pending(row)} pend")
    if row.get("estado_lectura") in ["Terminado"]: badges.append("✅")
    if row.get("estado_lectura") in ["Pausado"]: badges.append("💤")
    if _safe_int(row.get("es_crossover"), 0): badges.append("🧩")
    if row.get("fandom"): badges.append("🌌")
    stars = _safe_int(row.get("estrellas"), 0)
    if stars: badges.append("⭐" * min(stars, 5))
    return " ".join(badges)


def _card(row):
    portada = row.get("portada_path") or ""
    img = f'<img class="lib-cover" src="{portada}" />' if str(portada).startswith("http") else '<div class="lib-empty">📚</div>'
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    pct = _progress(row)
    link = row.get("link_original") or ""
    open_link = f' · <a href="{link}" target="_blank">Abrir link</a>' if str(link).startswith("http") else ""
    st.markdown(f"""
    <div class="lib-card">
      {img}
      <div class="lib-title">{row.get('titulo') or 'Sin título'}</div>
      <div class="lib-meta">{row.get('autor') or 'Autor no indicado'} · {row.get('tipo') or 'Tipo N/D'} · {row.get('estado_lectura') or 'Estado N/D'}{open_link}</div>
      <div class="lib-progress"><div class="lib-bar" style="width:{pct}%"></div></div>
      <div class="lib-small">T{row.get('temporada_actual') or 1}/{row.get('temporada_total') or 1} · {vistos}/{publicados} caps · {pct}% · ⏱️ {_fmt_time(row.get('tiempo_total_minutos'))}</div>
      <div class="lib-small">Calidad {row.get('calidad_datos') or 0}/100 · Fuente {row.get('ultima_importacion_fuente') or 'manual'} · Publicación: {row.get('estado_publicacion') or 'N/D'}</div>
      <div class="lib-badges">{_badges(row)}</div>
      <div class="lib-small">{(row.get('sinopsis') or 'Sin sinopsis todavía.')[:220]}</div>
      <div style="clear:both"></div>
    </div>
    """, unsafe_allow_html=True)


def _filter_rows(obras):
    df = pd.DataFrame(obras or [])
    if df.empty:
        return []
    for col in ["titulo", "autor", "tipo", "estado_lectura", "estado_publicacion", "etiquetas", "sinopsis", "fandom", "ship", "obra_original_nombre", "universo_au", "link_original", "ao3_work_id"]:
        if col not in df.columns: df[col] = ""
    with st.expander("Buscar y filtrar", expanded=True):
        q = st.text_input("Buscar en título, autor, etiquetas, sinopsis, fandom, ship, AO3 work ID o link", key="lib_query")
        c1, c2, c3, c4 = st.columns(4)
        tipos = sorted([x for x in df["tipo"].dropna().unique().tolist() if str(x).strip()])
        estados = sorted([x for x in df["estado_lectura"].dropna().unique().tolist() if str(x).strip()])
        pubs = sorted([x for x in df["estado_publicacion"].dropna().unique().tolist() if str(x).strip()])
        tipo_sel = c1.multiselect("Tipo", tipos, default=tipos, key="lib_tipo")
        estado_sel = c2.multiselect("Estado", estados, default=estados, key="lib_estado")
        pub_sel = c3.multiselect("Publicación", pubs, default=pubs, key="lib_pub")
        orden = c4.selectbox("Orden", ["Actualizado reciente", "Título", "Autor", "Favoritos", "Progreso", "Pendientes", "Tiempo total", "Estrellas", "Calidad"], key="lib_orden")
        f1, f2, f3, f4, f5 = st.columns(5)
        only_fav = f1.checkbox("Favoritos", key="lib_only_fav")
        only_pending = f2.checkbox("Con pendientes", key="lib_only_pending")
        only_ao3 = f3.checkbox("AO3", key="lib_only_ao3")
        no_cover = f4.checkbox("Sin portada", key="lib_no_cover")
        low_quality = f5.checkbox("Calidad < 50", key="lib_low_quality")
    rows = df.to_dict("records")
    if q.strip():
        qq = _norm(q)
        rows = [r for r in rows if qq in _norm(" ".join(str(r.get(c, "")) for c in ["titulo", "autor", "etiquetas", "sinopsis", "fandom", "ship", "obra_original_nombre", "universo_au", "link_original", "ao3_work_id"]))]
    if tipo_sel: rows = [r for r in rows if r.get("tipo") in tipo_sel]
    if estado_sel: rows = [r for r in rows if r.get("estado_lectura") in estado_sel]
    if pub_sel: rows = [r for r in rows if r.get("estado_publicacion") in pub_sel]
    if only_fav: rows = [r for r in rows if _safe_int(r.get("favorito"), 0)]
    if only_pending: rows = [r for r in rows if _pending(r) > 0]
    if only_ao3: rows = [r for r in rows if r.get("ao3_work_id") or _safe_int(r.get("ao3_tracking"), 0) or "archiveofourown.org" in str(r.get("link_original"))]
    if no_cover: rows = [r for r in rows if not str(r.get("portada_path") or "").strip()]
    if low_quality: rows = [r for r in rows if _safe_int(r.get("calidad_datos"), 0) < 50]
    reverse = orden not in ["Título", "Autor"]
    keymap = {
        "Título": lambda r: str(r.get("titulo") or "").lower(), "Autor": lambda r: str(r.get("autor") or "").lower(),
        "Favoritos": lambda r: _safe_int(r.get("favorito"), 0), "Progreso": _progress, "Pendientes": _pending,
        "Tiempo total": lambda r: _safe_int(r.get("tiempo_total_minutos"), 0), "Estrellas": lambda r: _safe_int(r.get("estrellas"), 0),
        "Calidad": lambda r: _safe_int(r.get("calidad_datos"), 0), "Actualizado reciente": lambda r: str(r.get("updated_at") or ""),
    }
    rows.sort(key=keymap.get(orden, keymap["Actualizado reciente"]), reverse=reverse)
    return rows


def _dashboard(rows):
    total = len(rows); active = sum(1 for r in rows if r.get("estado_lectura") in ["Leyendo", "Viendo", "Releyendo", "Rewatch"])
    done = sum(1 for r in rows if r.get("estado_lectura") == "Terminado"); fav = sum(_safe_int(r.get("favorito"), 0) for r in rows)
    pending = sum(1 for r in rows if _pending(r) > 0); minutes = sum(_safe_int(r.get("tiempo_total_minutos"), 0) for r in rows)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Obras", total); c2.metric("Activas", active); c3.metric("Terminadas", done); c4.metric("Favoritas", fav); c5.metric("Pendientes", pending); c6.metric("Tiempo", _fmt_time(minutes))


def _quick_actions(row):
    a1, a2, a3, a4 = st.columns([1, 1, 1, 2])
    if a1.button("❤️ Favorito", key=f"lib_fav_{row['id']}"):
        db.update_obra(row["id"], {"favorito": 0 if _safe_int(row.get("favorito"), 0) else 1}); st.rerun()
    if a2.button("+1 cap", key=f"lib_plus_{row['id']}"):
        new = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0) + 1
        db.update_obra(row["id"], {"capitulos_vistos": new, "capitulo_actual": new, "ultimo_capitulo_visto": new, "fecha_ultimo_capitulo_visto": str(date.today())}); st.rerun()
    if a3.button("Al día", key=f"lib_done_{row['id']}"):
        pub = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
        db.update_obra(row["id"], {"capitulos_vistos": pub, "capitulo_actual": pub, "ultimo_capitulo_visto": pub, "fecha_ultimo_capitulo_visto": str(date.today())}); st.rerun()
    estado = a4.selectbox("Estado rápido", ESTADOS, index=ESTADOS.index(row.get("estado_lectura")) if row.get("estado_lectura") in ESTADOS else 0, key=f"lib_estado_{row['id']}")
    if st.button("Guardar estado", key=f"lib_save_estado_{row['id']}"):
        db.update_obra(row["id"], {"estado_lectura": estado}); st.rerun()


def _cards(rows):
    for row in rows:
        _card(row); _quick_actions(row)


def _table(rows):
    if not rows: st.info("No hay resultados."); return
    cols = ["id", "titulo", "autor", "tipo", "estado_lectura", "estado_publicacion", "capitulos_vistos", "capitulos_publicados", "temporada_actual", "temporada_total", "favorito", "estrellas", "calidad_datos", "fandom", "ship", "etiquetas", "link_original"]
    df = pd.DataFrame(rows)
    st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True)


def _kanban(rows):
    states = ["Pendiente", "Leyendo", "Viendo", "Pausado", "Terminado", "Abandonado"]
    cols = st.columns(len(states))
    for col, state in zip(cols, states):
        with col:
            st.markdown(f"### {state}")
            for r in [x for x in rows if x.get("estado_lectura") == state][:25]:
                st.markdown(f"**{r.get('titulo')}**  \n{r.get('tipo')} · {_pending(r)} pend · {_progress(r)}%")


def _detail(rows):
    if not rows: st.info("No hay obras para mostrar."); return
    opts = {f"{r.get('titulo')} · {r.get('autor') or 'N/D'}": r for r in rows}
    label = st.selectbox("Selecciona obra", list(opts.keys()), key="lib_detail_select")
    row = opts[label]
    _card(row)
    st.markdown("### Editar sin borrar datos")
    c1, c2, c3 = st.columns(3)
    estado = c1.selectbox("Estado personal", ESTADOS, index=ESTADOS.index(row.get("estado_lectura")) if row.get("estado_lectura") in ESTADOS else 0, key="lib_det_estado")
    estado_pub = c2.selectbox("Estado publicación", ESTADOS_PUBLICACION, index=ESTADOS_PUBLICACION.index(row.get("estado_publicacion")) if row.get("estado_publicacion") in ESTADOS_PUBLICACION else 6, key="lib_det_pub")
    estrellas = c3.slider("Estrellas personales", 0, 5, _safe_int(row.get("estrellas"), 0), key="lib_det_stars")
    c4, c5, c6 = st.columns(3)
    vistos = c4.number_input("Capítulos vistos/leídos", min_value=0, value=_safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0), key="lib_det_vistos")
    publicados = c5.number_input("Capítulos publicados", min_value=0, value=_safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0), key="lib_det_pubcaps")
    fav = c6.checkbox("Favorito", value=bool(_safe_int(row.get("favorito"), 0)), key="lib_det_fav")
    etiquetas = st.text_input("Etiquetas", value=row.get("etiquetas") or "", key="lib_det_tags")
    comentario = st.text_area("Comentario / motivo estado", value=row.get("motivo_estado") or "", key="lib_det_comment")
    if st.button("Guardar cambios de obra", key="lib_det_save"):
        db.update_obra(row["id"], {"estado_lectura": estado, "estado_publicacion": estado_pub, "estrellas": int(estrellas), "capitulos_vistos": int(vistos), "capitulo_actual": int(vistos), "capitulos_publicados": int(publicados), "favorito": 1 if fav else 0, "etiquetas": etiquetas, "motivo_estado": comentario})
        st.success("Obra actualizada."); st.rerun()
    st.markdown("### Datos completos")
    st.json(row)


def _quality(rows):
    st.markdown("### Calidad de biblioteca")
    no_cover = [r for r in rows if not str(r.get("portada_path") or "").strip()]
    no_syn = [r for r in rows if not str(r.get("sinopsis") or "").strip()]
    no_author = [r for r in rows if not str(r.get("autor") or "").strip()]
    low = [r for r in rows if _safe_int(r.get("calidad_datos"), 0) < 50]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sin portada", len(no_cover)); c2.metric("Sin sinopsis", len(no_syn)); c3.metric("Sin autor", len(no_author)); c4.metric("Calidad < 50", len(low))
    for title, data in [("Sin portada", no_cover), ("Sin sinopsis", no_syn), ("Sin autor", no_author), ("Baja calidad", low)]:
        with st.expander(title):
            st.dataframe(pd.DataFrame(data)[[c for c in ["id", "titulo", "autor", "tipo", "calidad_datos"] if data and c in data[0]]], use_container_width=True) if data else st.info("Nada pendiente aquí.")


def _export(rows):
    st.markdown("### Exportar selección")
    if not rows: st.info("No hay datos para exportar."); return
    df = pd.DataFrame(rows)
    st.download_button("CSV filtrado", df.to_csv(index=False).encode("utf-8"), "biblioteca_filtrada.csv", "text/csv", key="lib_csv")
    st.download_button("JSON filtrado", df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"), "biblioteca_filtrada.json", "application/json", key="lib_json")


def render_biblioteca(obras):
    st.subheader("📚 Biblioteca")
    st.caption("Centro de control: búsqueda, filtros, cards, tabla, kanban, pendientes, detalle, calidad y exportes.")
    _style()
    if not obras:
        st.info("Aún no tienes obras registradas.")
        return
    rows = _filter_rows(obras)
    _dashboard(rows)
    modo = st.radio("Vista", ["Cards", "Tabla", "Kanban", "Pendientes", "Detalle", "Calidad", "Exportar"], horizontal=True, key="lib_view")
    st.caption(f"Mostrando {len(rows)} obras filtradas.")
    if modo == "Cards": _cards(rows)
    elif modo == "Tabla": _table(rows)
    elif modo == "Kanban": _kanban(rows)
    elif modo == "Pendientes": _cards([r for r in rows if _pending(r) > 0])
    elif modo == "Detalle": _detail(rows)
    elif modo == "Calidad": _quality(rows)
    elif modo == "Exportar": _export(rows)
