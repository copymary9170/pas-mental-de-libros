import base64
import json
import mimetypes
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import src.database as db
from src.utils import PORTADAS_DIR, save_uploaded_file

ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
TIPOS = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic", "Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
DIVISIONES_OBRA = ["Temporada", "Arco", "Volumen", "Parte", "Libro", "Saga"]
EXPECTATIVAS = ["No aplica", "ninguna", "baja", "media", "alta", "demasiado hype"]
RESULTADOS_EXPECTATIVA = ["No aplica", "supero", "cumplio", "decepciono", "fue diferente"]
RECOMENDARIA = ["No aplica", "Si", "No", "A ciertas personas", "Con advertencias"]
AMBIENTACIONES = ["No aplica", "contemporanea", "medieval", "victoriana", "antigua", "futurista", "distopica", "historica real", "fantasia historica", "otra"]
TIPOS_ISEKAI = ["No aplica", "reencarnacion", "transmigracion", "invocacion", "sistema", "regreso en el tiempo", "villana", "juego", "portal", "otro"]


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _norm(text):
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def _idx(options, value, default=0):
    return options.index(value) if value in options else default


def _select_value(value):
    return "" if value == "No aplica" else value


def _fmt_unknown(value):
    value = _safe_int(value, 0)
    return "?" if value <= 0 else str(value)


def _image_src(path_or_url):
    raw = str(path_or_url or "").strip()
    if not raw:
        return ""
    if raw.startswith(("http://", "https://", "data:")):
        return raw
    path = Path(raw)
    if not path.exists():
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def _cover_html(row):
    src = _image_src(row.get("portada_path"))
    if src:
        return f'<img class="lib-cover" src="{src}" />'
    return '<div class="lib-empty">📚</div>'


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
    .lib-card{border:1px solid rgba(147,197,253,.45);border-radius:18px 18px 10px 10px;background:linear-gradient(180deg,#eff6ff,#dbeafe);padding:14px;margin:10px 0 0 0;color:#0f172a;box-shadow:0 6px 20px rgba(15,23,42,.10)}
    .lib-title{font-weight:900;font-size:1.05rem;color:#0f172a}.lib-meta{font-size:.86rem;color:#1e3a8a;font-weight:750}.lib-small{font-size:.82rem;color:#334155;margin-top:4px}.lib-progress{height:10px;background:#bfdbfe;border-radius:999px;overflow:hidden;margin:8px 0}.lib-bar{height:10px;background:#1d4ed8;border-radius:999px}.lib-badges{margin-top:6px;font-size:.9rem}.lib-cover{width:70px;height:102px;object-fit:cover;border-radius:12px;box-shadow:0 6px 18px rgba(15,23,42,.2);float:left;margin-right:12px}.lib-empty{width:70px;height:102px;border-radius:12px;background:#1e3a8a;color:white;display:flex;align-items:center;justify-content:center;font-size:2rem;float:left;margin-right:12px}.edit-helper{background:#fff7ed;border-left:4px solid #f59e0b;border-radius:12px;padding:10px;margin:8px 0;color:#78350f;font-weight:800}
    .lib-action-mini-title{font-size:.74rem;font-weight:900;line-height:1.05;color:#fff}.lib-action-mini-sub{font-size:.62rem;opacity:.9;margin-top:2px;line-height:1.12;color:#dbeafe}.lib-action-current{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:1px 7px;margin-left:4px;font-size:.62rem;color:#fff}
    div[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(135deg,#0f2f73 0%,#1d4ed8 100%)!important;border:1px solid rgba(219,234,254,.70)!important;border-radius:0 0 12px 12px!important;padding:6px 8px 7px 8px!important;margin:0 0 12px 0!important;box-shadow:0 3px 10px rgba(15,23,42,.14)!important;color:#fff!important}
    div[data-testid="stVerticalBlockBorderWrapper"] p, div[data-testid="stVerticalBlockBorderWrapper"] span, div[data-testid="stVerticalBlockBorderWrapper"] label{color:#fff!important}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] button{background:#f8fafc!important;color:#0f2f73!important;border:1px solid rgba(255,255,255,.95)!important;border-radius:9px!important;padding:.18rem .28rem!important;min-height:26px!important;font-size:.69rem!important;font-weight:900!important;box-shadow:none!important}
    div[data-testid="stVerticalBlockBorderWrapper"] input{background:#eff6ff!important;color:#0f172a!important;border:1px solid #bfdbfe!important;border-radius:8px!important;min-height:26px!important;font-size:.72rem!important;font-weight:800!important}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"]>div{background:#eff6ff!important;color:#0f172a!important;border:1px solid #bfdbfe!important;border-radius:8px!important;min-height:26px!important;font-size:.72rem!important}
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] span{color:#0f172a!important;font-size:.72rem!important;font-weight:800!important}
    </style>
    """, unsafe_allow_html=True)


def _badges(row):
    badges = []
    if _safe_int(row.get("favorito"), 0): badges.append("❤️")
    if row.get("ao3_work_id") or _safe_int(row.get("ao3_tracking"), 0): badges.append("🔔 AO3")
    if _pending(row) > 0: badges.append(f"🟡 {_pending(row)} pend")
    if row.get("estado_lectura") == "Terminado": badges.append("✅")
    if row.get("estado_lectura") == "Pausado": badges.append("💤")
    if _safe_int(row.get("es_crossover"), 0): badges.append("🧩")
    if row.get("fandom"): badges.append("🌌")
    stars = _safe_int(row.get("estrellas"), 0)
    if stars: badges.append("⭐" * min(stars, 5))
    if not str(row.get("portada_path") or "").strip(): badges.append("🖼️ falta portada")
    if not str(row.get("autor") or "").strip() or str(row.get("autor") or "").strip() == "?": badges.append("✍️ autor ?")
    if _safe_int(row.get("capitulo_total"), 0) <= 0: badges.append("🔢 total ?")
    return " ".join(badges)


def _card(row):
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados"), 0)
    total = _safe_int(row.get("capitulo_total"), 0)
    pct = _progress(row)
    link = row.get("link_original") or ""
    open_link = f' · <a href="{link}" target="_blank">Abrir link</a>' if str(link).startswith("http") else ""
    st.markdown(f"""
    <div class="lib-card">
      {_cover_html(row)}
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
    for col in ["titulo", "autor", "tipo", "estado_lectura", "estado_publicacion", "etiquetas", "sinopsis", "fandom", "ship", "obra_original_nombre", "universo_au", "link_original", "ao3_work_id", "portada_path"]:
        if col not in df.columns:
            df[col] = ""
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
    keymap = {"Título": lambda r: str(r.get("titulo") or "").lower(), "Autor": lambda r: str(r.get("autor") or "").lower(), "Favoritos": lambda r: _safe_int(r.get("favorito"), 0), "Progreso": _progress, "Pendientes": _pending, "Tiempo total": lambda r: _safe_int(r.get("tiempo_total_minutos"), 0), "Estrellas": lambda r: _safe_int(r.get("estrellas"), 0), "Calidad": lambda r: _safe_int(r.get("calidad_datos"), 0), "Actualizado reciente": lambda r: str(r.get("updated_at") or "")}
    rows.sort(key=keymap.get(orden, keymap["Actualizado reciente"]), reverse=reverse)
    return rows


def _dashboard(rows):
    total = len(rows)
    active = sum(1 for r in rows if r.get("estado_lectura") in ["Leyendo", "Viendo", "Releyendo", "Rewatch"])
    done = sum(1 for r in rows if r.get("estado_lectura") == "Terminado")
    fav = sum(_safe_int(r.get("favorito"), 0) for r in rows)
    pending = sum(1 for r in rows if _pending(r) > 0)
    minutes = sum(_safe_int(r.get("tiempo_total_minutos"), 0) for r in rows)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Obras", total); c2.metric("Activas", active); c3.metric("Terminadas", done); c4.metric("Favoritas", fav); c5.metric("Pendientes", pending); c6.metric("Tiempo", _fmt_time(minutes))


def _sumar_avance(row, cantidad):
    actual = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    nuevo = actual + max(0, int(cantidad or 0))
    if publicados > 0:
        nuevo = min(nuevo, publicados)
    db.update_obra(row["id"], {"capitulos_vistos": nuevo, "capitulo_actual": nuevo, "ultimo_capitulo_visto": nuevo, "fecha_ultimo_capitulo_visto": str(date.today())})


def _quick_actions(row):
    actual = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    total_txt = publicados if publicados > 0 else "?"
    titulo = row.get("titulo") or "esta obra"
    with st.container(border=True):
        st.markdown(f"""
        <div class="lib-action-mini-title">Acciones <span class="lib-action-current">{actual}/{total_txt}</span></div>
        <div class="lib-action-mini-sub">{titulo[:48]} · solo esta obra</div>
        """, unsafe_allow_html=True)
        q1, q2, q3, q4, q5, q6 = st.columns([0.45, 0.7, 0.5, 0.72, 1.15, 0.72])
        if q1.button("❤️", key=f"lib_fav_{row['id']}", help="Favorito", use_container_width=True):
            db.update_obra(row["id"], {"favorito": 0 if _safe_int(row.get("favorito"), 0) else 1})
            st.rerun()
        cantidad = q2.number_input("Caps", min_value=0, value=1, step=1, key=f"lib_sum_qty_{row['id']}", label_visibility="collapsed")
        if q3.button("+", key=f"lib_sum_btn_{row['id']}", help="Sumar capítulos vistos", use_container_width=True):
            if int(cantidad or 0) <= 0:
                st.warning("Coloca un número mayor a 0 para sumar avance.")
            else:
                _sumar_avance(row, cantidad)
                st.rerun()
        if q4.button("Día", key=f"lib_done_{row['id']}", help="Poner avance al último capítulo publicado", use_container_width=True):
            db.update_obra(row["id"], {"capitulos_vistos": publicados, "capitulo_actual": publicados, "ultimo_capitulo_visto": publicados, "fecha_ultimo_capitulo_visto": str(date.today())})
            st.rerun()
        estado = q5.selectbox("Estado", ESTADOS, index=ESTADOS.index(row.get("estado_lectura")) if row.get("estado_lectura") in ESTADOS else 0, key=f"lib_estado_{row['id']}", label_visibility="collapsed")
        if q5.button("Guardar", key=f"lib_save_estado_{row['id']}", help="Guardar estado", use_container_width=True):
            db.update_obra(row["id"], {"estado_lectura": estado})
            st.rerun()
        if q6.button("Gráfica", key=f"lib_graph_{row['id']}", help="Ver evolución por capítulos", use_container_width=True):
            if str(st.session_state.get("biblioteca_graph_id")) == str(row.get("id")):
                st.session_state.pop("biblioteca_graph_id", None)
            else:
                st.session_state["biblioteca_graph_id"] = row.get("id")
            st.rerun()


def _cards(rows):
    for row in rows:
        _card(row)
        _quick_actions(row)


def _table(rows):
    if not rows:
        st.info("No hay resultados.")
        return
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
    if merged.get("titulo"): score += 10
    if merged.get("autor") and str(merged.get("autor")).strip() != "?": score += 8
    if merged.get("tipo"): score += 7
    if merged.get("estado_lectura"): score += 7
    if merged.get("sinopsis"): score += 10
    if merged.get("portada_path"): score += 10
    if merged.get("link_original"): score += 10
    if _safe_int(merged.get("capitulos_publicados"), 0) > 0: score += 7
    if _safe_int(merged.get("capitulo_total"), 0) > 0: score += 6
    if merged.get("etiquetas"): score += 5
    if merged.get("resena") or merged.get("mood") or merged.get("comentario"): score += 7
    return min(100, score)


def _detail(rows):
    if not rows:
        st.info("No hay obras para mostrar.")
        return
    opts = {f"#{r.get('id')} · {r.get('titulo')} · {r.get('autor') or 'N/D'}": r for r in rows}
    label = st.selectbox("Selecciona obra", list(opts.keys()), key="lib_detail_select")
    row = opts[label]
    _card(row)
    src = _image_src(row.get("portada_path"))
    if src:
        st.image(src, caption="Portada actual", width=150)
    st.markdown("### Editar / completar obra")
    st.markdown('<div class="edit-helper">Puedes completar lo básico sin borrar datos. Para opiniones por capítulo usa 📝 Capítulos.</div>', unsafe_allow_html=True)
    with st.form(f"lib_edit_form_{row['id']}"):
        c0, c1, c2 = st.columns(3)
        titulo = c0.text_input("Título", value=row.get("titulo") or "")
        autor = c1.text_input("Autor / creador / estudio", value=row.get("autor") or "")
        tipo = c2.selectbox("Tipo", TIPOS, index=_idx(TIPOS, row.get("tipo"), 0))
        c3, c4, c5 = st.columns(3)
        estado = c3.selectbox("Estado personal", ESTADOS, index=_idx(ESTADOS, row.get("estado_lectura"), 0))
        estado_pub = c4.selectbox("Estado publicación", ESTADOS_PUBLICACION, index=_idx(ESTADOS_PUBLICACION, row.get("estado_publicacion"), 6))
        estrellas = c5.slider("Estrellas personales", 0, 5, _safe_int(row.get("estrellas"), 0))
        p1, p2, p3 = st.columns(3)
        vistos = p1.number_input("Capítulos vistos/leídos", min_value=0, value=_safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0))
        publicados = p2.number_input("Capítulos publicados", min_value=0, value=_safe_int(row.get("capitulos_publicados"), 0))
        total_esperado = p3.number_input("Capítulos esperados", min_value=0, value=_safe_int(row.get("capitulo_total"), 0))
        portada_url = st.text_input("URL portada o ruta guardada", value=row.get("portada_path") or "")
        portada_upload = st.file_uploader("Subir portada nueva", type=["jpg", "jpeg", "png", "webp"], key=f"lib_cover_upload_{row['id']}")
        link_original = st.text_input("Link original / fuente", value=row.get("link_original") or "")
        link_respaldo = st.text_input("Link respaldo / copia", value=row.get("link_respaldo") or "")
        etiquetas = st.text_input("Etiquetas / géneros", value=row.get("etiquetas") or "")
        sinopsis = st.text_area("Sinopsis / descripción", value=row.get("sinopsis") or "", height=140)
        comentario = st.text_area("Comentario general", value=row.get("comentario") or "", height=90)
        resena = st.text_area("Reseña / opinión general", value=row.get("resena") or "", height=110)
        mood = st.text_input("Mood", value=row.get("mood") or "")
        fav = st.checkbox("Favorito", value=bool(_safe_int(row.get("favorito"), 0)))
        if st.form_submit_button("Guardar detalles"):
            portada_path = portada_url.strip()
            if portada_upload is not None:
                portada_path = save_uploaded_file(portada_upload, PORTADAS_DIR)
            data = {"titulo": titulo.strip() or row.get("titulo"), "autor": autor.strip(), "tipo": tipo, "estado_lectura": estado, "estado_publicacion": estado_pub, "estrellas": int(estrellas), "capitulos_vistos": int(vistos), "capitulo_actual": int(vistos), "ultimo_capitulo_visto": int(vistos), "fecha_ultimo_capitulo_visto": str(date.today()), "capitulos_publicados": int(publicados), "capitulo_total": int(total_esperado), "ultimo_capitulo_publicado": int(publicados), "portada_path": portada_path, "link_original": link_original.strip(), "link_respaldo": link_respaldo.strip(), "etiquetas": etiquetas.strip(), "sinopsis": sinopsis.strip(), "comentario": comentario.strip(), "resena": resena.strip(), "mood": mood.strip(), "favorito": 1 if fav else 0}
            data["calidad_datos"] = _recalc_quality(row, data)
            db.update_obra(row["id"], data)
            st.success("Detalles actualizados.")
            st.rerun()
    with st.expander("Datos completos", expanded=False):
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
    if not rows:
        st.info("No hay datos para exportar.")
        return
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
