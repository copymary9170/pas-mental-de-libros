import unicodedata
from datetime import date

import pandas as pd
import streamlit as st

import src.database as db
from src.utils import PORTADAS_DIR, save_uploaded_file

ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
TIPOS = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic", "Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]


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


def _fmt_unknown(value):
    value = _safe_int(value, 0)
    return "?" if value <= 0 else str(value)


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
    .lib-title{font-weight:900;font-size:1.05rem;color:#0f172a}.lib-meta{font-size:.86rem;color:#1e3a8a;font-weight:750}.lib-small{font-size:.82rem;color:#334155;margin-top:4px}.lib-progress{height:10px;background:#bfdbfe;border-radius:999px;overflow:hidden;margin:8px 0}.lib-bar{height:10px;background:#1d4ed8;border-radius:999px}.lib-badges{margin-top:6px;font-size:.9rem}.lib-cover{width:70px;height:102px;object-fit:cover;border-radius:12px;box-shadow:0 6px 18px rgba(15,23,42,.2);float:left;margin-right:12px}.lib-empty{width:70px;height:102px;border-radius:12px;background:#1e3a8a;color:white;display:flex;align-items:center;justify-content:center;font-size:2rem;float:left;margin-right:12px}.kanban-col{background:#eff6ff;border-radius:16px;padding:10px;min-height:200px}.quality-box{background:#f8fafc;border-left:4px solid #2563eb;border-radius:12px;padding:10px;margin:8px 0;color:#0f172a}.edit-helper{background:#fff7ed;border-left:4px solid #f59e0b;border-radius:12px;padding:10px;margin:8px 0;color:#78350f;font-weight:800}
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
    if not str(row.get("portada_path") or "").strip(): badges.append("🖼️ falta portada")
    if not str(row.get("autor") or "").strip() or str(row.get("autor") or "").strip() == "?": badges.append("✍️ autor ?")
    if _safe_int(row.get("capitulo_total"), 0) <= 0: badges.append("🔢 total ?")
    return " ".join(badges)


def _card(row):
    portada = row.get("portada_path") or ""
    img = f'<img class="lib-cover" src="{portada}" />' if str(portada).startswith("http") else '<div class="lib-empty">📚</div>'
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados"), 0)
    total = _safe_int(row.get("capitulo_total"), 0)
    pct = _progress(row)
    link = row.get("link_original") or ""
    open_link = f' · <a href="{link}" target="_blank">Abrir link</a>' if str(link).startswith("http") else ""
    st.markdown(f"""
    <div class="lib-card">
      {img}
      <div class="lib-title">{row.get('titulo') or 'Sin título'}</div>
      <div class="lib-meta">{row.get('autor') or 'Autor no indicado'} · {row.get('tipo') or 'Tipo N/D'} · {row.get('estado_lectura') or 'Estado N/D'}{open_link}</div>
      <div class="lib-progress"><div class="lib-bar" style="width:{pct}%"></div></div>
      <div class="lib-small">T{row.get('temporada_actual') or 1}/{row.get('temporada_total') or 1} · vistos {vistos} · publicados {_fmt_unknown(publicados)} · total esperado {_fmt_unknown(total)} · {pct}% · ⏱️ {_fmt_time(row.get('tiempo_total_minutos'))}</div>
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
    cols = ["id", "titulo", "autor", "tipo", "estado_lectura", "estado_publicacion", "capitulos_vistos", "capitulos_publicados", "capitulo_total", "temporada_actual", "temporada_total", "favorito", "estrellas", "calidad_datos", "fandom", "ship", "etiquetas", "portada_path", "link_original"]
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


def _recalc_quality(row, data):
    merged = dict(row); merged.update(data)
    score = 0
    if merged.get("titulo"): score += 15
    if merged.get("autor") and str(merged.get("autor")).strip() != "?": score += 12
    if merged.get("tipo"): score += 8
    if merged.get("sinopsis"): score += 15
    if merged.get("portada_path"): score += 15
    if merged.get("link_original"): score += 10
    if _safe_int(merged.get("capitulos_publicados"), 0) > 0: score += 8
    if _safe_int(merged.get("capitulo_total"), 0) > 0: score += 7
    if merged.get("etiquetas"): score += 5
    if merged.get("estado_lectura"): score += 5
    return min(100, score)


def _detail(rows):
    if not rows: st.info("No hay obras para mostrar."); return
    opts = {f"#{r.get('id')} · {r.get('titulo')} · {r.get('autor') or 'N/D'}": r for r in rows}
    label = st.selectbox("Selecciona obra", list(opts.keys()), key="lib_detail_select")
    row = opts[label]
    _card(row)
    st.markdown("### Editar / completar obra sin borrar datos")
    st.markdown('<div class="edit-helper">Puedes guardar aunque falte portada, autor o total de capítulos. Si el autor dejó el total como ?, marca “total esperado desconocido” y se guardará como pendiente.</div>', unsafe_allow_html=True)

    with st.form(f"lib_edit_form_{row['id']}"):
        st.markdown("#### Datos principales")
        c0, c1, c2 = st.columns(3)
        titulo = c0.text_input("Título", value=row.get("titulo") or "")
        autor = c1.text_input("Autor / creador", value=row.get("autor") or "", placeholder="Puedes dejar ? si no se sabe")
        tipo = c2.selectbox("Tipo", TIPOS, index=TIPOS.index(row.get("tipo")) if row.get("tipo") in TIPOS else 0)

        c3, c4, c5 = st.columns(3)
        estado = c3.selectbox("Estado personal", ESTADOS, index=ESTADOS.index(row.get("estado_lectura")) if row.get("estado_lectura") in ESTADOS else 0)
        estado_pub = c4.selectbox("Estado publicación", ESTADOS_PUBLICACION, index=ESTADOS_PUBLICACION.index(row.get("estado_publicacion")) if row.get("estado_publicacion") in ESTADOS_PUBLICACION else 6)
        estrellas = c5.slider("Estrellas personales", 0, 5, _safe_int(row.get("estrellas"), 0))

        st.markdown("#### Progreso y capítulos")
        p1, p2, p3 = st.columns(3)
        vistos = p1.number_input("Capítulos vistos/leídos", min_value=0, value=_safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0))
        publicados_desconocidos = p2.checkbox("Publicados desconocidos (?)", value=_safe_int(row.get("capitulos_publicados"), 0) <= 0)
        publicados = p2.number_input("Capítulos publicados", min_value=0, value=_safe_int(row.get("capitulos_publicados"), 0), disabled=publicados_desconocidos)
        total_desconocido = p3.checkbox("Total esperado desconocido (?)", value=_safe_int(row.get("capitulo_total"), 0) <= 0)
        total_esperado = p3.number_input("Capítulos esperados", min_value=0, value=_safe_int(row.get("capitulo_total"), 0), disabled=total_desconocido)

        t1, t2 = st.columns(2)
        temporada_actual = t1.number_input("Temporada/arco actual", min_value=1, value=max(1, _safe_int(row.get("temporada_actual"), 1)))
        temporada_total = t2.number_input("Temporadas/arcos totales", min_value=1, value=max(1, _safe_int(row.get("temporada_total"), 1)))

        st.markdown("#### Portada y enlaces")
        portada_url = st.text_input("URL portada", value=row.get("portada_path") or "")
        portada_upload = st.file_uploader("Subir portada nueva", type=["jpg", "jpeg", "png", "webp"], key=f"lib_cover_upload_{row['id']}")
        link_original = st.text_input("Link original", value=row.get("link_original") or "")
        link_respaldo = st.text_input("Link respaldo", value=row.get("link_respaldo") or "")

        st.markdown("#### Descripción y organización")
        etiquetas = st.text_input("Etiquetas", value=row.get("etiquetas") or "")
        sinopsis = st.text_area("Sinopsis / descripción", value=row.get("sinopsis") or "", height=140)
        comentario = st.text_area("Comentario / motivo estado", value=row.get("motivo_estado") or "", height=90)
        resena = st.text_area("Reseña / opinión", value=row.get("resena") or "", height=90)
        fav = st.checkbox("Favorito", value=bool(_safe_int(row.get("favorito"), 0)))

        if st.form_submit_button("Guardar cambios / completar obra"):
            portada_path = portada_url.strip()
            if portada_upload is not None:
                portada_path = save_uploaded_file(portada_upload, PORTADAS_DIR)
            caps_publicados_final = 0 if publicados_desconocidos else int(publicados)
            cap_total_final = 0 if total_desconocido else int(total_esperado)
            vistos_final = int(vistos)
            if caps_publicados_final > 0 and vistos_final > caps_publicados_final:
                st.error("Los capítulos vistos/leídos no pueden superar los publicados. Si publicados es ?, marca publicados desconocidos.")
            else:
                data = {
                    "titulo": titulo.strip() or row.get("titulo"), "autor": autor.strip(), "tipo": tipo,
                    "estado_lectura": estado, "estado_publicacion": estado_pub, "estrellas": int(estrellas),
                    "capitulos_vistos": vistos_final, "capitulo_actual": vistos_final, "ultimo_capitulo_visto": vistos_final,
                    "fecha_ultimo_capitulo_visto": str(date.today()), "capitulos_publicados": caps_publicados_final,
                    "capitulo_total": cap_total_final, "ultimo_capitulo_publicado": caps_publicados_final,
                    "temporada_actual": int(temporada_actual), "temporada_total": int(max(temporada_total, temporada_actual)),
                    "portada_path": portada_path, "link_original": link_original.strip(), "link_respaldo": link_respaldo.strip(),
                    "etiquetas": etiquetas.strip(), "sinopsis": sinopsis.strip(), "motivo_estado": comentario.strip(),
                    "resena": resena.strip(), "favorito": 1 if fav else 0,
                }
                data["calidad_datos"] = _recalc_quality(row, data)
                db.update_obra(row["id"], data)
                st.success("Obra actualizada. Ya puedes completar lo que faltó sin recrearla.")
                st.rerun()

    st.markdown("### Datos completos")
    st.json(row)


def _quality(rows):
    st.markdown("### Calidad de biblioteca")
    no_cover = [r for r in rows if not str(r.get("portada_path") or "").strip()]
    no_syn = [r for r in rows if not str(r.get("sinopsis") or "").strip()]
    no_author = [r for r in rows if not str(r.get("autor") or "").strip() or str(r.get("autor") or "").strip() == "?"]
    no_total = [r for r in rows if _safe_int(r.get("capitulo_total"), 0) <= 0]
    low = [r for r in rows if _safe_int(r.get("calidad_datos"), 0) < 50]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sin portada", len(no_cover)); c2.metric("Sin sinopsis", len(no_syn)); c3.metric("Sin autor/autor ?", len(no_author)); c4.metric("Total ?", len(no_total)); c5.metric("Calidad < 50", len(low))
    for title, data in [("Sin portada", no_cover), ("Sin sinopsis", no_syn), ("Sin autor o autor ?", no_author), ("Total esperado desconocido", no_total), ("Baja calidad", low)]:
        with st.expander(title):
            st.dataframe(pd.DataFrame(data)[[c for c in ["id", "titulo", "autor", "tipo", "capitulo_total", "portada_path", "calidad_datos"] if data and c in data[0]]], use_container_width=True) if data else st.info("Nada pendiente aquí.")


def _export(rows):
    st.markdown("### Exportar selección")
    if not rows: st.info("No hay datos para exportar."); return
    df = pd.DataFrame(rows)
    st.download_button("CSV filtrado", df.to_csv(index=False).encode("utf-8"), "biblioteca_filtrada.csv", "text/csv", key="lib_csv")
    st.download_button("JSON filtrado", df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"), "biblioteca_filtrada.json", "application/json", key="lib_json")


def render_biblioteca(obras):
    st.subheader("📚 Biblioteca")
    st.caption("Centro de control: búsqueda, filtros, edición, cards, tabla, kanban, pendientes, detalle, calidad y exportes.")
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
