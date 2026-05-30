from datetime import date
import difflib
import re

import streamlit as st

from src.pages.fanfiction import render_fanfiction_fields

BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
TIPOS = BOOK_TYPES + TV_TYPES
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
DIVISIONES_OBRA = ["Temporada", "Arco", "Volumen", "Parte", "Libro", "Saga"]
EXPECTATIVAS = ["No aplica", "ninguna", "baja", "media", "alta", "demasiado hype"]
RESULTADOS_EXPECTATIVA = ["No aplica", "supero", "cumplio", "decepciono", "fue diferente"]
TIPOS_ISEKAI = ["No aplica", "reencarnacion", "transmigracion", "invocacion", "sistema", "regreso en el tiempo", "villana", "juego", "portal", "otro"]
AMBIENTACIONES = ["No aplica", "contemporanea", "medieval", "victoriana", "antigua", "futurista", "distopica", "historica real", "fantasia historica", "otra"]
TIPOS_CRINGE = ["No aplica", "divertido", "incomodo", "vergüenza ajena", "malo", "delicioso"]
TIPOS_TEMA_OSCURO = ["No aplica", "violencia", "abuso", "manipulacion", "trauma", "moral cuestionable", "taboo narrativo", "otro"]


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _bool_int(value):
    return 1 if value else 0


def _optional_date(enabled, value):
    return str(value) if enabled and value else None


def _select_value(value):
    return "" if value == "No aplica" else value


def _idx(options, value, default=0):
    return options.index(value) if value in options else default


def _ao3_work_id(url):
    match = re.search(r"archiveofourown\.org/works/(\d+)", str(url or ""))
    return match.group(1) if match else ""


def _detect_source(url):
    raw = str(url or "").strip()
    u = raw.lower()
    if "archiveofourown.org/works/" in u:
        return {"fuente": "AO3", "tipo": "Fanfiction", "fanfic": True, "ao3": True, "confiabilidad": 95}
    if "wattpad.com" in u:
        return {"fuente": "Wattpad", "tipo": "Fanfiction", "fanfic": True, "ao3": False, "confiabilidad": 75}
    if "fanfiction.net" in u:
        return {"fuente": "FanFiction.net", "tipo": "Fanfiction", "fanfic": True, "ao3": False, "confiabilidad": 80}
    if "royalroad.com" in u:
        return {"fuente": "RoyalRoad", "tipo": "Webnovel", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "novelupdates.com" in u:
        return {"fuente": "NovelUpdates", "tipo": "Novela ligera", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "webnovel.com" in u:
        return {"fuente": "Webnovel", "tipo": "Webnovel", "fanfic": False, "ao3": False, "confiabilidad": 75}
    if "mangadex.org" in u:
        return {"fuente": "MangaDex", "tipo": "Manga", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "myanimelist.net" in u:
        tipo = "Manga" if "/manga/" in u else "Anime"
        return {"fuente": "MyAnimeList", "tipo": tipo, "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "imdb.com" in u:
        return {"fuente": "IMDb", "tipo": "Pelicula", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "themoviedb.org" in u or "tmdb" in u:
        return {"fuente": "TMDB", "tipo": "Serie", "fanfic": False, "ao3": False, "confiabilidad": 90}
    if "openlibrary.org" in u:
        return {"fuente": "OpenLibrary", "tipo": "Libro", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "goodreads.com" in u:
        return {"fuente": "Goodreads", "tipo": "Libro", "fanfic": False, "ao3": False, "confiabilidad": 70}
    return {"fuente": "Manual", "tipo": "", "fanfic": False, "ao3": False, "confiabilidad": 40 if raw else 20}


def _quality(item):
    checks = [
        ("Título", 12, bool(item.get("titulo"))),
        ("Autor", 10, bool(item.get("autor"))),
        ("Tipo", 8, bool(item.get("tipo"))),
        ("Estado", 8, bool(item.get("estado_lectura"))),
        ("Sinopsis", 12, bool(item.get("sinopsis"))),
        ("Portada", 12, bool(item.get("portada_path"))),
        ("URL/fuente", 10, bool(item.get("link_original") or item.get("url_fuente"))),
        ("Capítulos", 8, _safe_int(item.get("capitulo_total") or item.get("capitulos_publicados"), 0) > 0),
        ("Fechas", 8, bool(item.get("fecha_publicacion") or item.get("fecha_inicio") or item.get("fecha_fin"))),
        ("Wrapped", 12, any(_safe_int(item.get(k), 0) > 0 or bool(item.get(k)) for k in ["nivel_esperanza_inicial", "nivel_satisfaccion_general", "sensor_llanto", "sensor_cringe", "es_isekai", "epoca_ambientacion"])),
    ]
    return min(100, sum(points for _, points, ok in checks if ok)), checks


def _find_duplicates(item, obras):
    url_norm = str(item.get("link_original") or item.get("url_fuente") or "").strip().lower()
    title_norm = str(item.get("titulo") or "").strip().lower()
    author_norm = str(item.get("autor") or "").strip().lower()
    ao3 = _ao3_work_id(url_norm)
    matches = []
    for obra in obras or []:
        score = 0
        motivos = []
        obra_url = str(obra.get("link_original") or "").strip().lower()
        obra_title = str(obra.get("titulo") or "").strip().lower()
        obra_author = str(obra.get("autor") or "").strip().lower()
        if url_norm and obra_url and url_norm == obra_url:
            score += 100; motivos.append("mismo link")
        if ao3 and ao3 == _ao3_work_id(obra_url):
            score += 100; motivos.append("mismo AO3 work ID")
        if title_norm and obra_title:
            ratio = difflib.SequenceMatcher(None, title_norm, obra_title).ratio()
            if ratio >= 0.78:
                score += int(ratio * 70); motivos.append(f"título parecido {int(ratio * 100)}%")
        if author_norm and obra_author and author_norm == obra_author:
            score += 20; motivos.append("mismo autor")
        if score:
            matches.append({"obra": obra, "score": min(100, score), "motivos": motivos})
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]


def _render_quality(item):
    score, checks = _quality(item)
    st.markdown(f"**Calidad para importar/Wrapped: {score}/100**")
    cols = st.columns(2)
    for idx, (label, points, ok) in enumerate(checks):
        cols[idx % 2].write(f"{'✅' if ok else '⚠️'} {label}: {'+' + str(points) if ok else '+0'}")
    return score


def _source_pool():
    pool = []
    for item in st.session_state.get("import_queue", []) or []:
        q = dict(item); q["_origen_prefill"] = "Cola de Buscar e importar"; pool.append(q)
    for item in st.session_state.get("external_results", []) or []:
        q = dict(item); q["_origen_prefill"] = "Últimos resultados del buscador"; pool.append(q)
    for item in st.session_state.get("link_batch_queue", []) or []:
        q = dict(item); q["_origen_prefill"] = "Cola de links"; pool.append(q)
    meta = st.session_state.get("link_metadata", {}) or {}
    if meta:
        q = dict(meta); q["_origen_prefill"] = "Metadata del último link"; pool.append(q)
    return pool


def _prefill_from_connected_sources():
    pool = _source_pool()
    if not pool:
        st.info("No hay datos recientes de Buscar/Importar para rellenar. Puedes llenar manualmente desde cero.")
        return {}
    labels = ["No usar"] + [f"{i+1}. {p.get('titulo') or 'Sin título'} · {p.get('tipo') or p.get('kind') or 'tipo N/D'} · {p.get('_origen_prefill')}" for i, p in enumerate(pool)]
    choice = st.selectbox("Rellenar desde Buscar/Importar", labels, key="manual_prefill_choice")
    if choice == "No usar":
        return {}
    idx = labels.index(choice) - 1
    st.success("Usando datos del buscador/importador como base. Puedes editarlos antes de guardar.")
    return pool[idx]


def render_agregar_manual(obras, add_obra, save_uploaded_file, portadas_dir, respaldos_dir):
    st.subheader("Agregar obra manualmente")
    st.caption("Conectado con Buscar/Importar y Wrapped: usa datos recientes como base, revisa duplicados, calcula calidad y guarda sensores para reportes.")

    with st.expander("🔗 Conectar con Buscar/Importar", expanded=True):
        base = _prefill_from_connected_sources()
        if base:
            st.caption(f"Origen base: {base.get('_origen_prefill', 'manual')}")
            if base.get("portada_path"):
                st.image(base.get("portada_path"), width=120)

    detected_initial = _detect_source(base.get("url_fuente") or base.get("link_original") if base else "")
    tipo_default = base.get("tipo") or detected_initial.get("tipo") or "Libro"
    tipo_preview = st.selectbox("Tipo de obra", TIPOS, index=_idx(TIPOS, tipo_default, 0), key="manual_tipo_visible")

    fanfic_data = {}
    if tipo_preview == "Fanfiction" or detected_initial.get("fanfic"):
        st.info("Modo fanfiction/canon conectado: puedes registrar obra original, fandom, ship, AU y crossover.")
        fanfic_data = render_fanfiction_fields(prefix="manual_visible")

    with st.form("obra_form_manual"):
        st.markdown("### Datos principales")
        c1, c2 = st.columns(2)
        with c1:
            titulo = st.text_input("Título *", value=base.get("titulo", ""))
            autor = st.text_input("Autor / creador / estudio", value=base.get("autor", ""))
            estado = st.selectbox("Estado personal", ESTADOS, index=_idx(ESTADOS, base.get("estado_lectura", "Pendiente"), 0))
            estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION, index=_idx(ESTADOS_PUBLICACION, base.get("estado_publicacion", "No aplica"), 6))
            favorito = st.checkbox("Marcar como favorito", value=bool(_safe_int(base.get("favorito"), 0)))
        with c2:
            division_obra = st.selectbox("Tipo de división", DIVISIONES_OBRA, index=_idx(DIVISIONES_OBRA, base.get("division_obra", "Temporada"), 0))
            etiquetas = st.text_input("Etiquetas / géneros", value=base.get("etiquetas", ""), placeholder="romance, fantasía, kdrama, comfort...")
            link_original = st.text_input("Link original / fuente", value=base.get("link_original") or base.get("url_fuente") or "")
            prioridad = st.slider("Prioridad", 0, 5, _safe_int(base.get("prioridad"), 0))
            estrellas = st.slider("Estrellas", 0, 5, _safe_int(base.get("estrellas"), 0))
            clasificacion = st.slider("Nota / clasificación", 0.0, 10.0, float(base.get("clasificacion") or 0.0), 0.5)

        sinopsis = st.text_area("Sinopsis / descripción de la obra", value=base.get("sinopsis", ""), height=140)
        comentario = st.text_area("Comentario corto / primera impresión", value=base.get("comentario", ""), height=90)
        resena = st.text_area("Reseña / opinión personal", value=base.get("resena", ""), height=120)
        mood = st.text_input("Mood", value=base.get("mood", ""), placeholder="cozy, intenso, lloré, fangirl, cringe delicioso...")
        frases_favoritas = st.text_area("Frases favoritas", value=base.get("frases_favoritas", ""), height=80)

        st.markdown("### Fechas y progreso")
        c3, c4, c5 = st.columns(3)
        with c3:
            usar_fecha_publicacion = st.checkbox("Agregar fecha de publicación / estreno", value=bool(base.get("fecha_publicacion")))
            fecha_publicacion_val = st.date_input("Fecha de publicación / estreno", value=date.today(), disabled=not usar_fecha_publicacion)
            usar_fecha_pendiente = st.checkbox("Agregar fecha a pendientes", value=bool(base.get("fecha_agregada_pendientes")))
            fecha_pendiente_val = st.date_input("Fecha agregada a pendientes", value=date.today(), disabled=not usar_fecha_pendiente)
        with c4:
            usar_fecha_inicio = st.checkbox("Agregar fecha de inicio", value=True)
            fecha_inicio_val = st.date_input("Fecha de inicio", value=date.today(), disabled=not usar_fecha_inicio)
            usar_fecha_fin = st.checkbox("Agregar fecha de finalización", value=bool(base.get("fecha_fin")))
            fecha_fin_val = st.date_input("Fecha de finalización", value=date.today(), disabled=not usar_fecha_fin)
        with c5:
            temporada_actual = st.number_input("Temporada/arco actual", min_value=1, value=max(1, _safe_int(base.get("temporada_actual"), 1)), step=1)
            temporada_total = st.number_input("Temporadas/arcos totales", min_value=1, value=max(1, _safe_int(base.get("temporada_total"), 1)), step=1)
            cap_vistos = st.number_input("Capítulos leídos/vistos", min_value=0, value=_safe_int(base.get("capitulos_vistos") or base.get("capitulo_actual"), 0), step=1)
            cap_pub = st.number_input("Capítulos publicados/emitidos", min_value=0, value=_safe_int(base.get("capitulos_publicados") or base.get("capitulo_total"), 0), step=1)
            cap_total = st.number_input("Capítulos totales esperados", min_value=0, value=_safe_int(base.get("capitulo_total") or base.get("capitulos_publicados"), 0), step=1)

        st.markdown("### Ambientación y subgénero")
        c6, c7, c8 = st.columns(3)
        with c6:
            es_isekai = st.checkbox("Es isekai", value=bool(_safe_int(base.get("es_isekai"), 0)))
            tipo_isekai = st.selectbox("Tipo de isekai", TIPOS_ISEKAI, index=_idx(TIPOS_ISEKAI, base.get("tipo_isekai", "No aplica"), 0))
            epoca_ambientacion = st.selectbox("Época / ambientación", AMBIENTACIONES, index=_idx(AMBIENTACIONES, base.get("epoca_ambientacion", "No aplica"), 0))
            mundo_principal = st.text_input("País / cultura / reino / mundo principal", value=base.get("mundo_principal", ""))
        with c7:
            nivel_construccion_mundo = st.slider("Construcción de mundo", 0, 5, _safe_int(base.get("nivel_construccion_mundo"), 0))
            nivel_politica_intriga = st.slider("Política / intriga", 0, 5, _safe_int(base.get("nivel_politica_intriga"), 0))
            nivel_magia_sistema = st.slider("Magia / sistema de poder", 0, 5, _safe_int(base.get("nivel_magia_sistema"), 0))
        with c8:
            nivel_romance = st.slider("Romance", 0, 5, _safe_int(base.get("nivel_romance"), 0))
            nivel_accion = st.slider("Acción", 0, 5, _safe_int(base.get("nivel_accion"), 0))
            nivel_drama = st.slider("Drama", 0, 5, _safe_int(base.get("nivel_drama"), 0))

        st.markdown("### Expectativas, esperanza y final")
        c9, c10, c11 = st.columns(3)
        with c9:
            expectativa_inicial = st.selectbox("Expectativa inicial", EXPECTATIVAS, index=_idx(EXPECTATIVAS, base.get("expectativa_inicial", "No aplica"), 0))
            nivel_esperanza_inicial = st.slider("Nivel de esperanza inicial", 0, 5, _safe_int(base.get("nivel_esperanza_inicial"), 0))
            le_tenia_esperanza = st.checkbox("Le tenía esperanza", value=bool(_safe_int(base.get("le_tenia_esperanza"), 0)))
            le_tenia_pocas_esperanzas = st.checkbox("Le tenía pocas esperanzas", value=bool(_safe_int(base.get("le_tenia_pocas_esperanzas"), 0)))
        with c10:
            resultado_expectativa = st.selectbox("Resultado contra expectativa", RESULTADOS_EXPECTATIVA, index=_idx(RESULTADOS_EXPECTATIVA, base.get("resultado_expectativa", "No aplica"), 0))
            nivel_decepcion = st.slider("Nivel de decepción", 0, 5, _safe_int(base.get("nivel_decepcion"), 0))
            nivel_satisfaccion_general = st.slider("Satisfacción general", 0, 5, _safe_int(base.get("nivel_satisfaccion_general"), 0))
            satisfaccion_final = st.slider("Satisfacción del final", 0, 5, _safe_int(base.get("satisfaccion_final"), 0))
        with c11:
            final_salvo_obra = st.checkbox("El final salvó la obra", value=bool(_safe_int(base.get("final_salvo_obra"), 0)))
            final_arruino_obra = st.checkbox("El final arruinó la obra", value=bool(_safe_int(base.get("final_arruino_obra"), 0)))
            autor_arruino_final = st.checkbox("El autor arruinó la obra al final", value=bool(_safe_int(base.get("autor_arruino_final"), 0)))
        motivo_esperanza = st.text_area("Por qué tenía esperanza o pocas esperanzas", value=base.get("motivo_esperanza", ""), height=70)
        como_arruino_final = st.text_area("Cómo la arruinó el autor al final", value=base.get("como_arruino_final", ""), height=70)
        comentario_final = st.text_area("Comentario del final", value=base.get("comentario_final", ""), height=70)

        st.markdown("### Sensores para Wrapped")
        c12, c13, c14 = st.columns(3)
        with c12:
            sensor_lujuria = st.checkbox("Sensor lujuria / caliente", value=bool(_safe_int(base.get("sensor_lujuria"), 0)))
            nivel_lujuria = st.slider("Nivel de lujuria", 0, 5, _safe_int(base.get("nivel_lujuria"), 0))
            sensor_llanto = st.checkbox("Sensor llanto", value=bool(_safe_int(base.get("sensor_llanto"), 0)))
            nivel_llanto = st.slider("Nivel de llanto", 0, 5, _safe_int(base.get("nivel_llanto"), 0))
            veces_llore = st.number_input("Veces que lloré", min_value=0, value=_safe_int(base.get("veces_llore"), 0), step=1)
            sensor_risa = st.checkbox("Sensor risa", value=bool(_safe_int(base.get("sensor_risa"), 0)))
            nivel_risa = st.slider("Nivel de risa", 0, 5, _safe_int(base.get("nivel_risa"), 0))
        with c13:
            sensor_aburrimiento = st.checkbox("Sensor aburrimiento", value=bool(_safe_int(base.get("sensor_aburrimiento"), 0)))
            nivel_aburrimiento = st.slider("Nivel de aburrimiento", 0, 5, _safe_int(base.get("nivel_aburrimiento"), 0))
            sensor_cringe = st.checkbox("Sensor cringe", value=bool(_safe_int(base.get("sensor_cringe"), 0)))
            nivel_cringe = st.slider("Nivel de cringe", 0, 5, _safe_int(base.get("nivel_cringe"), 0))
            tipo_cringe = st.selectbox("Tipo de cringe", TIPOS_CRINGE, index=_idx(TIPOS_CRINGE, base.get("tipo_cringe", "No aplica"), 0))
            sensor_red_flag = st.checkbox("Sensor red flag", value=bool(_safe_int(base.get("sensor_red_flag"), 0)))
            nivel_red_flag = st.slider("Nivel de red flag", 0, 5, _safe_int(base.get("nivel_red_flag"), 0))
        with c14:
            sensor_resaca_emocional = st.checkbox("Sensor resaca emocional", value=bool(_safe_int(base.get("sensor_resaca_emocional"), 0)))
            nivel_resaca_emocional = st.slider("Nivel de resaca emocional", 0, 5, _safe_int(base.get("nivel_resaca_emocional"), 0))
            sensor_tema_oscuro = st.checkbox("Sensor tema oscuro / cuestionable", value=bool(_safe_int(base.get("sensor_tema_oscuro"), 0)))
            nivel_oscuridad = st.slider("Nivel de oscuridad", 0, 5, _safe_int(base.get("nivel_oscuridad"), 0))
            tipo_tema_oscuro = st.selectbox("Tipo de tema oscuro", TIPOS_TEMA_OSCURO, index=_idx(TIPOS_TEMA_OSCURO, base.get("tipo_tema_oscuro", "No aplica"), 0))
            sensor_obra_larga = st.checkbox("Sensor obra demasiado larga", value=bool(_safe_int(base.get("sensor_obra_larga"), 0)))
            nivel_cansancio_longitud = st.slider("Cansancio por longitud", 0, 5, _safe_int(base.get("nivel_cansancio_longitud"), 0))

        st.markdown("### Archivos, imagen e importación")
        portada_url = st.text_input("URL portada", value=base.get("portada_path", ""))
        portada = st.file_uploader("Subir portada", type=["jpg", "jpeg", "png", "webp"])
        modo_respaldo = st.radio("¿Cómo quieres guardar el contenido?", ["Solo registrar la obra", "Subir obra completa", "Subir capítulos uno por uno", "Subir varios capítulos de golpe"])
        respaldo = st.file_uploader("Archivo completo de la obra", type=["pdf", "epub", "txt", "docx", "zip"]) if modo_respaldo == "Subir obra completa" else None
        if modo_respaldo in ["Subir capítulos uno por uno", "Subir varios capítulos de golpe"]:
            st.caption("Queda registrado aquí. Luego puedes cargar capítulos desde la pestaña 📝 Capitulos.")

        detected = _detect_source(link_original)
        preview = {
            "titulo": titulo.strip(), "autor": autor.strip(), "tipo": tipo_preview, "estado_lectura": estado,
            "sinopsis": sinopsis.strip(), "portada_path": portada_url.strip() or base.get("portada_path", ""),
            "link_original": link_original.strip(), "capitulo_total": int(cap_total), "capitulos_publicados": int(cap_pub),
            "fecha_publicacion": _optional_date(usar_fecha_publicacion, fecha_publicacion_val) or base.get("fecha_publicacion", ""),
            "fecha_inicio": _optional_date(usar_fecha_inicio, fecha_inicio_val),
            "nivel_esperanza_inicial": int(nivel_esperanza_inicial), "nivel_satisfaccion_general": int(nivel_satisfaccion_general),
            "sensor_llanto": _bool_int(sensor_llanto), "sensor_cringe": _bool_int(sensor_cringe),
            "es_isekai": _bool_int(es_isekai), "epoca_ambientacion": _select_value(epoca_ambientacion),
        }
        calidad_preview = _quality(preview)[0]

        st.markdown("### Confirmación inteligente")
        st.info(f"Fuente detectada: **{detected['fuente']}** · Confiabilidad: **{detected['confiabilidad']}/100** · Calidad estimada: **{calidad_preview}/100**")
        dupes = _find_duplicates(preview, obras)
        if dupes:
            st.warning(f"Posibles duplicados: {len(dupes)}")
            for d in dupes:
                st.write(f"{d['score']}% · {d['obra'].get('titulo')} · {', '.join(d['motivos'])}")
        else:
            st.success("No se detectaron duplicados fuertes por link/AO3/título/autor.")

        guardar_manual = st.form_submit_button("Guardar obra conectada")
        if guardar_manual:
            if not titulo.strip():
                st.error("El título es obligatorio")
            elif int(cap_vistos) > max(int(cap_pub), int(cap_total)) and max(int(cap_pub), int(cap_total)) > 0:
                st.error("Los capítulos vistos/leídos no pueden ser mayores que los publicados/totales.")
            else:
                uploaded_cover_path = save_uploaded_file(portada, portadas_dir) if portada is not None else ""
                data = {
                    "titulo": titulo.strip(), "autor": autor.strip(), "tipo": tipo_preview,
                    "division_obra": division_obra, "clasificacion": float(clasificacion), "estrellas": int(estrellas),
                    "comentario": comentario.strip(), "resena": resena.strip(), "mood": mood.strip(), "frases_favoritas": frases_favoritas.strip(),
                    "estado_lectura": estado, "estado_publicacion": estado_pub,
                    "fecha_publicacion": _optional_date(usar_fecha_publicacion, fecha_publicacion_val) or base.get("fecha_publicacion", ""),
                    "fecha_agregada_pendientes": _optional_date(usar_fecha_pendiente, fecha_pendiente_val) or "",
                    "temporada_actual": int(temporada_actual), "temporada_total": int(max(temporada_total, temporada_actual)),
                    "capitulo_actual": int(cap_vistos), "capitulos_vistos": int(cap_vistos),
                    "capitulos_publicados": int(cap_pub), "capitulo_total": int(cap_total),
                    "sinopsis": sinopsis.strip(), "etiquetas": etiquetas.strip(), "link_original": link_original.strip(), "link_respaldo": "",
                    "portada_path": uploaded_cover_path or portada_url.strip() or base.get("portada_path", ""),
                    "respaldo_path": save_uploaded_file(respaldo, respaldos_dir), "motivo_estado": modo_respaldo,
                    "favorito": _bool_int(favorito), "prioridad": int(prioridad),
                    "fecha_inicio": _optional_date(usar_fecha_inicio, fecha_inicio_val), "fecha_fin": _optional_date(usar_fecha_fin, fecha_fin_val),
                    "expectativa_inicial": _select_value(expectativa_inicial), "nivel_esperanza_inicial": int(nivel_esperanza_inicial),
                    "le_tenia_esperanza": _bool_int(le_tenia_esperanza), "le_tenia_pocas_esperanzas": _bool_int(le_tenia_pocas_esperanzas),
                    "motivo_esperanza": motivo_esperanza.strip(), "resultado_expectativa": _select_value(resultado_expectativa),
                    "nivel_decepcion": int(nivel_decepcion), "nivel_satisfaccion_general": int(nivel_satisfaccion_general),
                    "satisfaccion_final": int(satisfaccion_final), "final_salvo_obra": _bool_int(final_salvo_obra),
                    "final_arruino_obra": _bool_int(final_arruino_obra), "autor_arruino_final": _bool_int(autor_arruino_final),
                    "como_arruino_final": como_arruino_final.strip(), "comentario_final": comentario_final.strip(),
                    "es_isekai": _bool_int(es_isekai), "tipo_isekai": _select_value(tipo_isekai),
                    "epoca_ambientacion": _select_value(epoca_ambientacion), "mundo_principal": mundo_principal.strip(),
                    "nivel_construccion_mundo": int(nivel_construccion_mundo), "nivel_politica_intriga": int(nivel_politica_intriga),
                    "nivel_magia_sistema": int(nivel_magia_sistema), "nivel_romance": int(nivel_romance),
                    "nivel_accion": int(nivel_accion), "nivel_drama": int(nivel_drama),
                    "sensor_lujuria": _bool_int(sensor_lujuria), "nivel_lujuria": int(nivel_lujuria),
                    "sensor_llanto": _bool_int(sensor_llanto), "nivel_llanto": int(nivel_llanto), "veces_llore": int(veces_llore),
                    "sensor_risa": _bool_int(sensor_risa), "nivel_risa": int(nivel_risa),
                    "sensor_aburrimiento": _bool_int(sensor_aburrimiento), "nivel_aburrimiento": int(nivel_aburrimiento),
                    "sensor_cringe": _bool_int(sensor_cringe), "nivel_cringe": int(nivel_cringe), "tipo_cringe": _select_value(tipo_cringe),
                    "sensor_red_flag": _bool_int(sensor_red_flag), "nivel_red_flag": int(nivel_red_flag),
                    "sensor_resaca_emocional": _bool_int(sensor_resaca_emocional), "nivel_resaca_emocional": int(nivel_resaca_emocional),
                    "sensor_tema_oscuro": _bool_int(sensor_tema_oscuro), "nivel_oscuridad": int(nivel_oscuridad), "tipo_tema_oscuro": _select_value(tipo_tema_oscuro),
                    "sensor_obra_larga": _bool_int(sensor_obra_larga), "nivel_cansancio_longitud": int(nivel_cansancio_longitud),
                    "fuente_importacion": detected["fuente"], "ultima_importacion_fuente": detected["fuente"],
                    "fuente_confiabilidad": int(detected["confiabilidad"]), "ao3_work_id": _ao3_work_id(link_original),
                    "ao3_tracking": 1 if detected["ao3"] else 0,
                }
                data["calidad_datos"] = _quality(data)[0]
                if tipo_preview == "Fanfiction" or detected.get("fanfic"):
                    data.update(fanfic_data)
                add_obra(data)
                st.success(f"Obra guardada y conectada: {titulo.strip()} · calidad {data['calidad_datos']}/100")
