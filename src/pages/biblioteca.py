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
TIPOS_ISEKAI = ["No aplica", "reencarnacion", "transmigracion", "invocacion", "sistema", "regreso en el tiempo", "villana", "juego", "portal", "otro"]
AMBIENTACIONES = ["No aplica", "contemporanea", "medieval", "victoriana", "antigua", "futurista", "distopica", "historica real", "fantasia historica", "otra"]
TIPOS_CRINGE = ["No aplica", "divertido", "incomodo", "vergüenza ajena", "malo", "delicioso"]
TIPOS_TEMA_OSCURO = ["No aplica", "violencia", "abuso", "manipulacion", "trauma", "moral cuestionable", "taboo narrativo", "otro"]
COMO_EMPECE = ["No aplica", "impulso", "recomendacion", "curiosidad", "hype", "pendiente antiguo", "relectura", "rewatch"]
DISFRUTE_MAS = ["No aplica", "sola", "acompañada", "ambas"]
NIVELES_OBSESION = ["No aplica", "bajo", "medio", "alto", "extremo"]
MOMENTOS_PERSONALES = ["No aplica", "mal momento", "buen momento", "momento perfecto", "etapa importante"]
RECOMENDARIA = ["No aplica", "Si", "No", "A ciertas personas", "Con advertencias"]


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


def _bool_int(value):
    return 1 if value else 0


def _json(data):
    return json.dumps(data, ensure_ascii=False)


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
    .lib-card{border:1px solid rgba(147,197,253,.45);border-radius:18px;background:linear-gradient(180deg,#eff6ff,#dbeafe);padding:14px;margin:10px 0;color:#0f172a;box-shadow:0 6px 20px rgba(15,23,42,.10)}
    .lib-title{font-weight:900;font-size:1.05rem;color:#0f172a}.lib-meta{font-size:.86rem;color:#1e3a8a;font-weight:750}.lib-small{font-size:.82rem;color:#334155;margin-top:4px}.lib-progress{height:10px;background:#bfdbfe;border-radius:999px;overflow:hidden;margin:8px 0}.lib-bar{height:10px;background:#1d4ed8;border-radius:999px}.lib-badges{margin-top:6px;font-size:.9rem}.lib-cover{width:70px;height:102px;object-fit:cover;border-radius:12px;box-shadow:0 6px 18px rgba(15,23,42,.2);float:left;margin-right:12px}.lib-empty{width:70px;height:102px;border-radius:12px;background:#1e3a8a;color:white;display:flex;align-items:center;justify-content:center;font-size:2rem;float:left;margin-right:12px}.edit-helper{background:#fff7ed;border-left:4px solid #f59e0b;border-radius:12px;padding:10px;margin:8px 0;color:#78350f;font-weight:800}
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
    keymap = {
        "Título": lambda r: str(r.get("titulo") or "").lower(), "Autor": lambda r: str(r.get("autor") or "").lower(),
        "Favoritos": lambda r: _safe_int(r.get("favorito"), 0), "Progreso": _progress, "Pendientes": _pending,
        "Tiempo total": lambda r: _safe_int(r.get("tiempo_total_minutos"), 0), "Estrellas": lambda r: _safe_int(r.get("estrellas"), 0),
        "Calidad": lambda r: _safe_int(r.get("calidad_datos"), 0), "Actualizado reciente": lambda r: str(r.get("updated_at") or ""),
    }
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
    if not rows:
        st.info("No hay resultados."); return
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
    if any(_safe_int(merged.get(k), 0) > 0 or bool(merged.get(k)) for k in ["nivel_esperanza_inicial", "nivel_satisfaccion_general", "sensor_llanto", "sensor_cringe", "sensor_red_flag", "es_isekai", "senales_wrapped_json", "sensores_wrapped_json"]): score += 13
    return min(100, score)


def _detail(rows):
    if not rows:
        st.info("No hay obras para mostrar."); return
    opts = {f"#{r.get('id')} · {r.get('titulo')} · {r.get('autor') or 'N/D'}": r for r in rows}
    label = st.selectbox("Selecciona obra", list(opts.keys()), key="lib_detail_select")
    row = opts[label]
    _card(row)
    src = _image_src(row.get("portada_path"))
    if src:
        st.image(src, caption="Portada actual", width=150)

    st.markdown("### 🖼️ Agregar portada faltante")
    st.caption("Usa esto si creaste la obra sin portada. Puedes subir una imagen o pegar una URL y guardarla sin tocar nada más.")
    with st.form(f"lib_cover_only_form_{row['id']}"):
        cover_url_only = st.text_input("URL de portada", value=row.get("portada_path") or "", key=f"lib_cover_url_only_{row['id']}")
        cover_file_only = st.file_uploader("Subir portada", type=["jpg", "jpeg", "png", "webp"], key=f"lib_cover_only_{row['id']}")
        if st.form_submit_button("Guardar solo portada"):
            new_cover = cover_url_only.strip()
            if cover_file_only is not None:
                new_cover = save_uploaded_file(cover_file_only, PORTADAS_DIR)
            if not new_cover:
                st.error("Sube una imagen o pega una URL de portada.")
            else:
                data = {"portada_path": new_cover}
                data["calidad_datos"] = _recalc_quality(row, data)
                db.update_obra(row["id"], data)
                st.success("Portada guardada. Si era archivo subido, ya quedó asociada a esta obra.")
                st.rerun()

    st.markdown("### Editar / completar obra sin borrar datos")
    st.markdown('<div class="edit-helper">Este detalle ahora permite completar casi todo lo de ➕ Agregar y 🔗 Links: datos básicos, progreso, portada, opinión, Wrapped, expectativas, sensores, ambientación y links.</div>', unsafe_allow_html=True)

    with st.form(f"lib_edit_form_{row['id']}"):
        st.markdown("#### Datos principales")
        c0, c1, c2 = st.columns(3)
        titulo = c0.text_input("Título", value=row.get("titulo") or "")
        autor = c1.text_input("Autor / creador / estudio", value=row.get("autor") or "", placeholder="Puedes dejar ? si no se sabe")
        tipo = c2.selectbox("Tipo", TIPOS, index=_idx(TIPOS, row.get("tipo"), 0))
        c3, c4, c5 = st.columns(3)
        estado = c3.selectbox("Estado personal", ESTADOS, index=_idx(ESTADOS, row.get("estado_lectura"), 0))
        estado_pub = c4.selectbox("Estado publicación", ESTADOS_PUBLICACION, index=_idx(ESTADOS_PUBLICACION, row.get("estado_publicacion"), 6))
        division_obra = c5.selectbox("Tipo de división", DIVISIONES_OBRA, index=_idx(DIVISIONES_OBRA, row.get("division_obra"), 0))
        c6, c7, c8 = st.columns(3)
        estrellas = c6.slider("Estrellas personales", 0, 5, _safe_int(row.get("estrellas"), 0))
        clasificacion = c7.slider("Nota / clasificación", 0.0, 10.0, _safe_float(row.get("clasificacion"), 0.0), 0.5)
        prioridad = c8.slider("Prioridad", 0, 5, _safe_int(row.get("prioridad"), 0))

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

        st.markdown("#### Fechas")
        f1, f2, f3, f4 = st.columns(4)
        fecha_publicacion = f1.text_input("Fecha de publicación / estreno", value=row.get("fecha_publicacion") or "")
        fecha_agregada_pendientes = f2.text_input("Fecha agregada a pendientes", value=row.get("fecha_agregada_pendientes") or "")
        fecha_inicio = f3.text_input("Fecha de inicio", value=row.get("fecha_inicio") or "")
        fecha_fin = f4.text_input("Fecha de finalización", value=row.get("fecha_fin") or "")

        st.markdown("#### Portada y enlaces")
        portada_url = st.text_input("URL portada o ruta guardada", value=row.get("portada_path") or "")
        portada_upload = st.file_uploader("Subir portada nueva", type=["jpg", "jpeg", "png", "webp"], key=f"lib_cover_upload_{row['id']}")
        link_original = st.text_input("Link original / fuente", value=row.get("link_original") or "")
        link_respaldo = st.text_input("Link respaldo / copia", value=row.get("link_respaldo") or "")

        st.markdown("#### Descripción, opinión y organización")
        etiquetas = st.text_input("Etiquetas / géneros", value=row.get("etiquetas") or "")
        sinopsis = st.text_area("Sinopsis / descripción", value=row.get("sinopsis") or "", height=140)
        comentario = st.text_area("Comentario corto / primera impresión", value=row.get("comentario") or row.get("motivo_estado") or "", height=90)
        motivo_estado = st.text_area("Motivo del estado", value=row.get("motivo_estado") or "", height=80)
        resena = st.text_area("Reseña / opinión personal", value=row.get("resena") or "", height=110)
        mood = st.text_input("Mood", value=row.get("mood") or "", placeholder="cozy, intenso, lloré, fangirl, cringe delicioso...")
        frases_favoritas = st.text_area("Frases favoritas", value=row.get("frases_favoritas") or "", height=70)
        escenas_favoritas = st.text_area("Escenas favoritas", value=row.get("escenas_favoritas") or "", height=70)
        momentos_marcantes = st.text_area("Momentos que me marcaron", value=row.get("momentos_marcantes") or "", height=70)
        spoilers = st.text_area("Spoilers / notas con spoiler", value=row.get("spoilers") or "", height=70)
        lo_recomendaria = st.selectbox("¿Lo recomendaría?", RECOMENDARIA, index=_idx(RECOMENDARIA, row.get("lo_recomendaria") or "No aplica", 0))

        st.markdown("#### Ambientación y subgénero")
        a1, a2, a3 = st.columns(3)
        es_isekai = a1.checkbox("Es isekai", value=bool(_safe_int(row.get("es_isekai"), 0)))
        tipo_isekai = a1.selectbox("Tipo de isekai", TIPOS_ISEKAI, index=_idx(TIPOS_ISEKAI, row.get("tipo_isekai") or "No aplica", 0))
        epoca_ambientacion = a1.selectbox("Época / ambientación", AMBIENTACIONES, index=_idx(AMBIENTACIONES, row.get("epoca_ambientacion") or "No aplica", 0))
        mundo_principal = a1.text_input("País / cultura / reino / mundo principal", value=row.get("mundo_principal") or "")
        nivel_construccion_mundo = a2.slider("Construcción de mundo", 0, 5, _safe_int(row.get("nivel_construccion_mundo"), 0))
        nivel_politica_intriga = a2.slider("Política / intriga", 0, 5, _safe_int(row.get("nivel_politica_intriga"), 0))
        nivel_magia_sistema = a2.slider("Magia / sistema de poder", 0, 5, _safe_int(row.get("nivel_magia_sistema"), 0))
        nivel_romance = a3.slider("Romance", 0, 5, _safe_int(row.get("nivel_romance"), 0))
        nivel_accion = a3.slider("Acción", 0, 5, _safe_int(row.get("nivel_accion"), 0))
        nivel_drama = a3.slider("Drama", 0, 5, _safe_int(row.get("nivel_drama"), 0))

        st.markdown("#### Señales para Wrapped automático")
        w1, w2, w3 = st.columns(3)
        como_empece = w1.selectbox("Cómo la empecé", COMO_EMPECE, key=f"lib_como_{row['id']}")
        retome_despues_pausa = w1.checkbox("La retomé después de pausarla", key=f"lib_retome_{row['id']}")
        la_vi_con_alguien = w1.checkbox("La vi/leí con alguien", key=f"lib_con_alguien_{row['id']}")
        disfrute_mas = w1.selectbox("La disfruté más", DISFRUTE_MAS, key=f"lib_disfrute_{row['id']}")
        nivel_obsesion = w2.selectbox("Nivel de obsesión", NIVELES_OBSESION, key=f"lib_obsesion_{row['id']}")
        busquedas_extra = w2.multiselect("Me hizo buscar", ["teorías", "fanarts", "edits", "fanfiction", "entrevistas", "nada"], key=f"lib_busquedas_{row['id']}")
        la_recomende = w2.checkbox("La recomendé", key=f"lib_recomende_{row['id']}")
        la_mencione_mucho = w2.checkbox("La mencioné mucho", key=f"lib_mencione_{row['id']}")
        saco_bloqueo = w3.checkbox("Me sacó de un bloqueo", key=f"lib_saco_{row['id']}")
        metio_bloqueo = w3.checkbox("Me metió en un bloqueo", key=f"lib_metio_{row['id']}")
        estado_emocional = w3.text_input("Estado emocional al verla/leerla", key=f"lib_estado_emocional_{row['id']}")
        momento_personal = w3.selectbox("Momento personal", MOMENTOS_PERSONALES, key=f"lib_momento_personal_{row['id']}")

        st.markdown("#### Expectativas, esperanza y final")
        e1, e2, e3 = st.columns(3)
        expectativa_inicial = e1.selectbox("Expectativa inicial", EXPECTATIVAS, index=_idx(EXPECTATIVAS, row.get("expectativa_inicial") or "No aplica", 0))
        nivel_esperanza_inicial = e1.slider("Nivel de esperanza inicial", 0, 5, _safe_int(row.get("nivel_esperanza_inicial"), 0))
        le_tenia_esperanza = e1.checkbox("Le tenía esperanza", value=bool(_safe_int(row.get("le_tenia_esperanza"), 0)))
        le_tenia_pocas_esperanzas = e1.checkbox("Le tenía pocas esperanzas", value=bool(_safe_int(row.get("le_tenia_pocas_esperanzas"), 0)))
        resultado_expectativa = e2.selectbox("Resultado contra expectativa", RESULTADOS_EXPECTATIVA, index=_idx(RESULTADOS_EXPECTATIVA, row.get("resultado_expectativa") or "No aplica", 0))
        nivel_decepcion = e2.slider("Nivel de decepción", 0, 5, _safe_int(row.get("nivel_decepcion"), 0))
        nivel_satisfaccion_general = e2.slider("Satisfacción general", 0, 5, _safe_int(row.get("nivel_satisfaccion_general"), 0))
        satisfaccion_final = e2.slider("Satisfacción del final", 0, 5, _safe_int(row.get("satisfaccion_final"), 0))
        final_salvo_obra = e3.checkbox("El final salvó la obra", value=bool(_safe_int(row.get("final_salvo_obra"), 0)))
        final_arruino_obra = e3.checkbox("El final arruinó la obra", value=bool(_safe_int(row.get("final_arruino_obra"), 0)))
        autor_arruino_final = e3.checkbox("El autor arruinó la obra al final", value=bool(_safe_int(row.get("autor_arruino_final"), 0)))
        motivo_esperanza = st.text_area("Por qué tenía esperanza o pocas esperanzas", value=row.get("motivo_esperanza") or "", height=70)
        como_arruino_final = st.text_area("Cómo la arruinó el autor al final", value=row.get("como_arruino_final") or "", height=70)
        comentario_final = st.text_area("Comentario del final", value=row.get("comentario_final") or "", height=70)

        st.markdown("#### Sensores para Wrapped")
        s1, s2, s3 = st.columns(3)
        sensor_lujuria = s1.checkbox("Sensor lujuria / caliente", value=bool(_safe_int(row.get("sensor_lujuria"), 0)))
        nivel_lujuria = s1.slider("Nivel de lujuria", 0, 5, _safe_int(row.get("nivel_lujuria"), 0))
        sensor_llanto = s1.checkbox("Sensor llanto", value=bool(_safe_int(row.get("sensor_llanto"), 0)))
        nivel_llanto = s1.slider("Nivel de llanto", 0, 5, _safe_int(row.get("nivel_llanto"), 0))
        veces_llore = s1.number_input("Veces que lloré", min_value=0, value=_safe_int(row.get("veces_llore"), 0), step=1)
        sensor_risa = s1.checkbox("Sensor risa", value=bool(_safe_int(row.get("sensor_risa"), 0)))
        nivel_risa = s1.slider("Nivel de risa", 0, 5, _safe_int(row.get("nivel_risa"), 0))
        sensor_aburrimiento = s2.checkbox("Sensor aburrimiento", value=bool(_safe_int(row.get("sensor_aburrimiento"), 0)))
        nivel_aburrimiento = s2.slider("Nivel de aburrimiento", 0, 5, _safe_int(row.get("nivel_aburrimiento"), 0))
        sensor_cringe = s2.checkbox("Sensor cringe", value=bool(_safe_int(row.get("sensor_cringe"), 0)))
        nivel_cringe = s2.slider("Nivel de cringe", 0, 5, _safe_int(row.get("nivel_cringe"), 0))
        tipo_cringe = s2.selectbox("Tipo de cringe", TIPOS_CRINGE, index=_idx(TIPOS_CRINGE, row.get("tipo_cringe") or "No aplica", 0))
        sensor_red_flag = s3.checkbox("Sensor red flag", value=bool(_safe_int(row.get("sensor_red_flag"), 0)))
        nivel_red_flag = s3.slider("Nivel de red flag", 0, 5, _safe_int(row.get("nivel_red_flag"), 0))
        sensor_resaca_emocional = s3.checkbox("Sensor resaca emocional", value=bool(_safe_int(row.get("sensor_resaca_emocional"), 0)))
        nivel_resaca_emocional = s3.slider("Nivel de resaca emocional", 0, 5, _safe_int(row.get("nivel_resaca_emocional"), 0))
        sensor_tema_oscuro = s3.checkbox("Sensor tema oscuro", value=bool(_safe_int(row.get("sensor_tema_oscuro"), 0)))
        nivel_oscuridad = s3.slider("Nivel de oscuridad", 0, 5, _safe_int(row.get("nivel_oscuridad"), 0))
        tipo_tema_oscuro = s3.selectbox("Tipo de tema oscuro", TIPOS_TEMA_OSCURO, index=_idx(TIPOS_TEMA_OSCURO, row.get("tipo_tema_oscuro") or "No aplica", 0))
        sensor_obra_larga = st.checkbox("Sensor obra larga / me cansó la longitud", value=bool(_safe_int(row.get("sensor_obra_larga"), 0)))
        nivel_cansancio_longitud = st.slider("Nivel cansancio por longitud", 0, 5, _safe_int(row.get("nivel_cansancio_longitud"), 0))

        fav = st.checkbox("Favorito", value=bool(_safe_int(row.get("favorito"), 0)))
        if st.form_submit_button("Guardar todos los detalles"):
            portada_path = portada_url.strip()
            if portada_upload is not None:
                portada_path = save_uploaded_file(portada_upload, PORTADAS_DIR)
            caps_publicados_final = 0 if publicados_desconocidos else int(publicados)
            cap_total_final = 0 if total_desconocido else int(total_esperado)
            vistos_final = int(vistos)
            if caps_publicados_final > 0 and vistos_final > caps_publicados_final:
                st.error("Los capítulos vistos/leídos no pueden superar los publicados. Si publicados es ?, marca publicados desconocidos.")
            else:
                senales_wrapped = {
                    "como_empece": _select_value(como_empece),
                    "retome_despues_pausa": retome_despues_pausa,
                    "la_vi_con_alguien": la_vi_con_alguien,
                    "disfrute_mas": _select_value(disfrute_mas),
                    "nivel_obsesion": _select_value(nivel_obsesion),
                    "busquedas_extra": busquedas_extra,
                    "la_recomende": la_recomende,
                    "la_mencione_mucho": la_mencione_mucho,
                    "saco_bloqueo": saco_bloqueo,
                    "metio_bloqueo": metio_bloqueo,
                    "estado_emocional": estado_emocional,
                    "momento_personal": _select_value(momento_personal),
                }
                sensores_wrapped = {
                    "lujuria": {"activo": sensor_lujuria, "nivel": int(nivel_lujuria)},
                    "llanto": {"activo": sensor_llanto, "nivel": int(nivel_llanto), "veces": int(veces_llore)},
                    "risa": {"activo": sensor_risa, "nivel": int(nivel_risa)},
                    "aburrimiento": {"activo": sensor_aburrimiento, "nivel": int(nivel_aburrimiento)},
                    "cringe": {"activo": sensor_cringe, "nivel": int(nivel_cringe), "tipo": _select_value(tipo_cringe)},
                    "red_flag": {"activo": sensor_red_flag, "nivel": int(nivel_red_flag)},
                    "resaca_emocional": {"activo": sensor_resaca_emocional, "nivel": int(nivel_resaca_emocional)},
                    "tema_oscuro": {"activo": sensor_tema_oscuro, "nivel": int(nivel_oscuridad), "tipo": _select_value(tipo_tema_oscuro)},
                    "obra_larga": {"activo": sensor_obra_larga, "nivel": int(nivel_cansancio_longitud)},
                }
                data = {
                    "titulo": titulo.strip() or row.get("titulo"),
                    "autor": autor.strip(),
                    "tipo": tipo,
                    "estado_lectura": estado,
                    "estado_publicacion": estado_pub,
                    "division_obra": division_obra,
                    "estrellas": int(estrellas),
                    "clasificacion": float(clasificacion),
                    "prioridad": int(prioridad),
                    "fecha_publicacion": fecha_publicacion.strip(),
                    "fecha_agregada_pendientes": fecha_agregada_pendientes.strip(),
                    "fecha_inicio": fecha_inicio.strip(),
                    "fecha_fin": fecha_fin.strip(),
                    "capitulos_vistos": vistos_final,
                    "capitulo_actual": vistos_final,
                    "ultimo_capitulo_visto": vistos_final,
                    "fecha_ultimo_capitulo_visto": str(date.today()),
                    "capitulos_publicados": caps_publicados_final,
                    "capitulo_total": cap_total_final,
                    "ultimo_capitulo_publicado": caps_publicados_final,
                    "temporada_actual": int(temporada_actual),
                    "temporada_total": int(max(temporada_total, temporada_actual)),
                    "portada_path": portada_path,
                    "link_original": link_original.strip(),
                    "link_respaldo": link_respaldo.strip(),
                    "etiquetas": etiquetas.strip(),
                    "sinopsis": sinopsis.strip(),
                    "comentario": comentario.strip(),
                    "motivo_estado": motivo_estado.strip(),
                    "resena": resena.strip(),
                    "mood": mood.strip(),
                    "frases_favoritas": frases_favoritas.strip(),
                    "escenas_favoritas": escenas_favoritas.strip(),
                    "momentos_marcantes": momentos_marcantes.strip(),
                    "spoilers": spoilers.strip(),
                    "lo_recomendaria": _select_value(lo_recomendaria),
                    "favorito": 1 if fav else 0,
                    "es_isekai": _bool_int(es_isekai),
                    "tipo_isekai": _select_value(tipo_isekai),
                    "epoca_ambientacion": _select_value(epoca_ambientacion),
                    "mundo_principal": mundo_principal.strip(),
                    "nivel_construccion_mundo": int(nivel_construccion_mundo),
                    "nivel_politica_intriga": int(nivel_politica_intriga),
                    "nivel_magia_sistema": int(nivel_magia_sistema),
                    "nivel_romance": int(nivel_romance),
                    "nivel_accion": int(nivel_accion),
                    "nivel_drama": int(nivel_drama),
                    "expectativa_inicial": _select_value(expectativa_inicial),
                    "nivel_esperanza_inicial": int(nivel_esperanza_inicial),
                    "le_tenia_esperanza": _bool_int(le_tenia_esperanza),
                    "le_tenia_pocas_esperanzas": _bool_int(le_tenia_pocas_esperanzas),
                    "motivo_esperanza": motivo_esperanza.strip(),
                    "resultado_expectativa": _select_value(resultado_expectativa),
                    "nivel_decepcion": int(nivel_decepcion),
                    "nivel_satisfaccion_general": int(nivel_satisfaccion_general),
                    "satisfaccion_final": int(satisfaccion_final),
                    "final_salvo_obra": _bool_int(final_salvo_obra),
                    "final_arruino_obra": _bool_int(final_arruino_obra),
                    "autor_arruino_final": _bool_int(autor_arruino_final),
                    "como_arruino_final": como_arruino_final.strip(),
                    "comentario_final": comentario_final.strip(),
                    "sensor_lujuria": _bool_int(sensor_lujuria),
                    "nivel_lujuria": int(nivel_lujuria),
                    "sensor_llanto": _bool_int(sensor_llanto),
                    "nivel_llanto": int(nivel_llanto),
                    "veces_llore": int(veces_llore),
                    "sensor_risa": _bool_int(sensor_risa),
                    "nivel_risa": int(nivel_risa),
                    "sensor_aburrimiento": _bool_int(sensor_aburrimiento),
                    "nivel_aburrimiento": int(nivel_aburrimiento),
                    "sensor_cringe": _bool_int(sensor_cringe),
                    "nivel_cringe": int(nivel_cringe),
                    "tipo_cringe": _select_value(tipo_cringe),
                    "sensor_red_flag": _bool_int(sensor_red_flag),
                    "nivel_red_flag": int(nivel_red_flag),
                    "sensor_resaca_emocional": _bool_int(sensor_resaca_emocional),
                    "nivel_resaca_emocional": int(nivel_resaca_emocional),
                    "sensor_tema_oscuro": _bool_int(sensor_tema_oscuro),
                    "nivel_oscuridad": int(nivel_oscuridad),
                    "tipo_tema_oscuro": _select_value(tipo_tema_oscuro),
                    "sensor_obra_larga": _bool_int(sensor_obra_larga),
                    "nivel_cansancio_longitud": int(nivel_cansancio_longitud),
                    "senales_wrapped_json": _json(senales_wrapped),
                    "sensores_wrapped_json": _json(sensores_wrapped),
                }
                data["calidad_datos"] = _recalc_quality(row, data)
                db.update_obra(row["id"], data)
                st.success("Detalles completos actualizados. Biblioteca ya puede completar lo que falte después de crear/importar una obra.")
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
    if not rows:
        st.info("No hay datos para exportar."); return
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
