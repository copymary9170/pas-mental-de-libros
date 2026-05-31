from __future__ import annotations

from datetime import date
import json
import re

import streamlit as st

from src.pages.fanfiction import render_fanfiction_fields

DIVISIONES_OBRA = ["Temporada", "Arco", "Volumen", "Parte", "Libro", "Saga"]
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
TIPOS_LINK = ["Webnovel", "Novela ligera", "Manhwa", "Manga", "Manhua", "Fanfiction", "Libro", "Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
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


def _bool_int(value):
    return 1 if value else 0


def _select_value(value):
    return "" if value == "No aplica" else value


def _idx(options, value, default=0):
    return options.index(value) if value in options else default


def _json(data):
    return json.dumps(data, ensure_ascii=False)


def _optional_date(enabled, value):
    return str(value) if enabled and value else None


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
    return {"fuente": "Link externo", "tipo": "Webnovel", "fanfic": False, "ao3": False, "confiabilidad": 50}


def _quality(item):
    checks = [
        ("Título", 10, bool(item.get("titulo"))),
        ("Autor", 8, bool(item.get("autor"))),
        ("Tipo", 7, bool(item.get("tipo"))),
        ("Estado", 7, bool(item.get("estado_lectura"))),
        ("Sinopsis", 10, bool(item.get("sinopsis"))),
        ("Portada", 10, bool(item.get("portada_path"))),
        ("URL", 10, bool(item.get("url_fuente") or item.get("link_original"))),
        ("Capítulos", 8, _safe_int(item.get("capitulo_total") or item.get("capitulos_publicados"), 0) > 0),
        ("Fuente detectada", 8, bool(item.get("fuente_importacion"))),
        ("Reseña/mood", 7, bool(item.get("resena") or item.get("mood") or item.get("comentario"))),
        ("Wrapped", 15, any(_safe_int(item.get(k), 0) > 0 or bool(item.get(k)) for k in ["nivel_esperanza_inicial", "nivel_satisfaccion_general", "sensor_llanto", "sensor_cringe", "es_isekai", "epoca_ambientacion", "senales_wrapped_json", "sensores_wrapped_json", "ranking_personal_json"])),
    ]
    return min(100, sum(points for _, points, ok in checks if ok)), checks


def _find_duplicates(url, titulo, autor, obras):
    url_norm = str(url or "").strip().lower()
    title_norm = str(titulo or "").strip().lower()
    author_norm = str(autor or "").strip().lower()
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
            ratio = 1 if title_norm == obra_title else 0
            if title_norm in obra_title or obra_title in title_norm:
                ratio = max(ratio, 0.85)
            if ratio >= 0.85:
                score += int(ratio * 60); motivos.append("título parecido")
        if author_norm and obra_author and author_norm == obra_author:
            score += 20; motivos.append("mismo autor")
        if score:
            matches.append({"obra": obra, "score": min(100, score), "motivos": motivos})
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]


def _render_quality(item):
    score, checks = _quality(item)
    st.markdown(f"**Calidad de datos: {score}/100**")
    for label, points, ok in checks:
        st.write(f"{'✅' if ok else '⚠️'} {label}: {'+' + str(points) if ok else '+0'}")
    return score


def _build_item(base, detected, edits, fanfic_data):
    item = dict(base or {})
    item.update(edits)
    item.update(fanfic_data or {})
    item["fuente_importacion"] = detected["fuente"]
    item["fuente_confiabilidad"] = detected["confiabilidad"]
    item["ao3_work_id"] = _ao3_work_id(item.get("url_fuente"))
    item["link_original"] = item.get("url_fuente")
    item["calidad_datos"] = _quality(item)[0]
    if detected["ao3"]:
        item["fuente_fanfic"] = "AO3"
    return item


def _render_manual_extra_fields(base):
    st.markdown("### Campos extra iguales a ➕ Agregar")
    with st.expander("📝 Opinión, notas, escenas y reseña", expanded=False):
        comentario = st.text_area("Comentario corto / primera impresión", value=base.get("comentario", ""), height=80, key="link_comentario")
        resena = st.text_area("Reseña / opinión personal", value=base.get("resena", ""), height=100, key="link_resena")
        mood = st.text_input("Mood", value=base.get("mood", ""), placeholder="cozy, intenso, lloré, fangirl, cringe delicioso...", key="link_mood")
        frases_favoritas = st.text_area("Frases favoritas", value=base.get("frases_favoritas", ""), height=70, key="link_frases")
        escenas_favoritas = st.text_area("Escenas favoritas", value=base.get("escenas_favoritas", ""), height=70, key="link_escenas")
        momentos_marcantes = st.text_area("Momentos que me marcaron", value=base.get("momentos_marcantes", ""), height=70, key="link_momentos")
        spoilers = st.text_area("Spoilers / notas con spoiler", value=base.get("spoilers", ""), height=70, key="link_spoilers")
        lo_recomendaria = st.selectbox("¿Lo recomendaría?", RECOMENDARIA, index=_idx(RECOMENDARIA, base.get("lo_recomendaria", "No aplica"), 0), key="link_recomienda")
    with st.expander("📅 Fechas adicionales", expanded=False):
        c1, c2, c3 = st.columns(3)
        usar_fecha_pendiente = c1.checkbox("Agregar fecha a pendientes", value=bool(base.get("fecha_agregada_pendientes")), key="link_usar_fecha_pend")
        fecha_pendiente_val = c1.date_input("Fecha agregada a pendientes", value=date.today(), disabled=not usar_fecha_pendiente, key="link_fecha_pend")
        usar_fecha_inicio = c2.checkbox("Agregar fecha de inicio", value=bool(base.get("fecha_inicio")), key="link_usar_fecha_inicio")
        fecha_inicio_val = c2.date_input("Fecha de inicio", value=date.today(), disabled=not usar_fecha_inicio, key="link_fecha_inicio")
        usar_fecha_fin = c3.checkbox("Agregar fecha de finalización", value=bool(base.get("fecha_fin")), key="link_usar_fecha_fin")
        fecha_fin_val = c3.date_input("Fecha de finalización", value=date.today(), disabled=not usar_fecha_fin, key="link_fecha_fin")
    with st.expander("🌍 Ambientación y subgénero", expanded=False):
        c4, c5, c6 = st.columns(3)
        es_isekai = c4.checkbox("Es isekai", value=bool(_safe_int(base.get("es_isekai"), 0)), key="link_isekai")
        tipo_isekai = c4.selectbox("Tipo de isekai", TIPOS_ISEKAI, index=_idx(TIPOS_ISEKAI, base.get("tipo_isekai", "No aplica"), 0), key="link_tipo_isekai")
        epoca_ambientacion = c4.selectbox("Época / ambientación", AMBIENTACIONES, index=_idx(AMBIENTACIONES, base.get("epoca_ambientacion", "No aplica"), 0), key="link_epoca")
        mundo_principal = c4.text_input("País / cultura / reino / mundo principal", value=base.get("mundo_principal", ""), key="link_mundo")
        nivel_construccion_mundo = c5.slider("Construcción de mundo", 0, 5, _safe_int(base.get("nivel_construccion_mundo"), 0), key="link_mundo_nivel")
        nivel_politica_intriga = c5.slider("Política / intriga", 0, 5, _safe_int(base.get("nivel_politica_intriga"), 0), key="link_politica")
        nivel_magia_sistema = c5.slider("Magia / sistema de poder", 0, 5, _safe_int(base.get("nivel_magia_sistema"), 0), key="link_magia")
        nivel_romance = c6.slider("Romance", 0, 5, _safe_int(base.get("nivel_romance"), 0), key="link_romance")
        nivel_accion = c6.slider("Acción", 0, 5, _safe_int(base.get("nivel_accion"), 0), key="link_accion")
        nivel_drama = c6.slider("Drama", 0, 5, _safe_int(base.get("nivel_drama"), 0), key="link_drama")
    with st.expander("🏆 Señales para Wrapped automático", expanded=False):
        w1, w2, w3 = st.columns(3)
        como_empece = w1.selectbox("Cómo la empecé", COMO_EMPECE, key="link_como_empece")
        retome_despues_pausa = w1.checkbox("La retomé después de pausarla", key="link_retome")
        la_vi_con_alguien = w1.checkbox("La vi/leí con alguien", key="link_con_alguien")
        disfrute_mas = w1.selectbox("La disfruté más", DISFRUTE_MAS, key="link_disfrute_mas")
        nivel_obsesion = w2.selectbox("Nivel de obsesión", NIVELES_OBSESION, key="link_obsesion")
        busquedas_extra = w2.multiselect("Me hizo buscar", ["teorías", "fanarts", "edits", "fanfiction", "entrevistas", "nada"], key="link_busquedas")
        la_recomende = w2.checkbox("La recomendé", key="link_recomende")
        la_mencione_mucho = w2.checkbox("La mencioné mucho", key="link_mencione")
        saco_bloqueo = w3.checkbox("Me sacó de un bloqueo", key="link_saco_bloqueo")
        metio_bloqueo = w3.checkbox("Me metió en un bloqueo", key="link_metio_bloqueo")
        estado_emocional = w3.text_input("Estado emocional al verla/leerla", key="link_estado_emocional")
        momento_personal = w3.selectbox("Momento personal", MOMENTOS_PERSONALES, key="link_momento_personal")
    with st.expander("🎯 Expectativas, esperanza y final", expanded=False):
        e1, e2, e3 = st.columns(3)
        expectativa_inicial = e1.selectbox("Expectativa inicial", EXPECTATIVAS, index=_idx(EXPECTATIVAS, base.get("expectativa_inicial", "No aplica"), 0), key="link_expectativa")
        nivel_esperanza_inicial = e1.slider("Nivel de esperanza inicial", 0, 5, _safe_int(base.get("nivel_esperanza_inicial"), 0), key="link_nivel_esperanza")
        le_tenia_esperanza = e1.checkbox("Le tenía esperanza", value=bool(_safe_int(base.get("le_tenia_esperanza"), 0)), key="link_tenia_esperanza")
        le_tenia_pocas_esperanzas = e1.checkbox("Le tenía pocas esperanzas", value=bool(_safe_int(base.get("le_tenia_pocas_esperanzas"), 0)), key="link_poca_esperanza")
        resultado_expectativa = e2.selectbox("Resultado contra expectativa", RESULTADOS_EXPECTATIVA, index=_idx(RESULTADOS_EXPECTATIVA, base.get("resultado_expectativa", "No aplica"), 0), key="link_resultado_exp")
        nivel_decepcion = e2.slider("Nivel de decepción", 0, 5, _safe_int(base.get("nivel_decepcion"), 0), key="link_decepcion")
        nivel_satisfaccion_general = e2.slider("Satisfacción general", 0, 5, _safe_int(base.get("nivel_satisfaccion_general"), 0), key="link_satisfaccion")
        satisfaccion_final = e2.slider("Satisfacción del final", 0, 5, _safe_int(base.get("satisfaccion_final"), 0), key="link_satisfaccion_final")
        final_salvo_obra = e3.checkbox("El final salvó la obra", value=bool(_safe_int(base.get("final_salvo_obra"), 0)), key="link_final_salvo")
        final_arruino_obra = e3.checkbox("El final arruinó la obra", value=bool(_safe_int(base.get("final_arruino_obra"), 0)), key="link_final_arruino")
        autor_arruino_final = e3.checkbox("El autor arruinó la obra al final", value=bool(_safe_int(base.get("autor_arruino_final"), 0)), key="link_autor_arruino")
        motivo_esperanza = st.text_area("Por qué tenía esperanza o pocas esperanzas", value=base.get("motivo_esperanza", ""), height=70, key="link_motivo_esperanza")
        como_arruino_final = st.text_area("Cómo la arruinó el autor al final", value=base.get("como_arruino_final", ""), height=70, key="link_como_arruino")
        comentario_final = st.text_area("Comentario del final", value=base.get("comentario_final", ""), height=70, key="link_comentario_final")
    with st.expander("🚨 Sensores para Wrapped", expanded=False):
        s1, s2, s3 = st.columns(3)
        sensor_lujuria = s1.checkbox("Sensor lujuria / caliente", value=bool(_safe_int(base.get("sensor_lujuria"), 0)), key="link_sensor_lujuria")
        nivel_lujuria = s1.slider("Nivel de lujuria", 0, 5, _safe_int(base.get("nivel_lujuria"), 0), key="link_nivel_lujuria")
        sensor_llanto = s1.checkbox("Sensor llanto", value=bool(_safe_int(base.get("sensor_llanto"), 0)), key="link_sensor_llanto")
        nivel_llanto = s1.slider("Nivel de llanto", 0, 5, _safe_int(base.get("nivel_llanto"), 0), key="link_nivel_llanto")
        veces_llore = s1.number_input("Veces que lloré", min_value=0, value=_safe_int(base.get("veces_llore"), 0), step=1, key="link_veces_llore")
        sensor_risa = s1.checkbox("Sensor risa", value=bool(_safe_int(base.get("sensor_risa"), 0)), key="link_sensor_risa")
        nivel_risa = s1.slider("Nivel de risa", 0, 5, _safe_int(base.get("nivel_risa"), 0), key="link_nivel_risa")
        sensor_aburrimiento = s2.checkbox("Sensor aburrimiento", value=bool(_safe_int(base.get("sensor_aburrimiento"), 0)), key="link_sensor_aburrimiento")
        nivel_aburrimiento = s2.slider("Nivel de aburrimiento", 0, 5, _safe_int(base.get("nivel_aburrimiento"), 0), key="link_nivel_aburrimiento")
        sensor_cringe = s2.checkbox("Sensor cringe", value=bool(_safe_int(base.get("sensor_cringe"), 0)), key="link_sensor_cringe")
        nivel_cringe = s2.slider("Nivel de cringe", 0, 5, _safe_int(base.get("nivel_cringe"), 0), key="link_nivel_cringe")
        tipo_cringe = s2.selectbox("Tipo de cringe", TIPOS_CRINGE, index=_idx(TIPOS_CRINGE, base.get("tipo_cringe", "No aplica"), 0), key="link_tipo_cringe")
        sensor_red_flag = s3.checkbox("Sensor red flag", value=bool(_safe_int(base.get("sensor_red_flag"), 0)), key="link_sensor_red_flag")
        nivel_red_flag = s3.slider("Nivel de red flag", 0, 5, _safe_int(base.get("nivel_red_flag"), 0), key="link_nivel_red_flag")
        sensor_resaca_emocional = s3.checkbox("Sensor resaca emocional", value=bool(_safe_int(base.get("sensor_resaca_emocional"), 0)), key="link_sensor_resaca")
        nivel_resaca_emocional = s3.slider("Nivel de resaca emocional", 0, 5, _safe_int(base.get("nivel_resaca_emocional"), 0), key="link_nivel_resaca")
        sensor_tema_oscuro = s3.checkbox("Sensor tema oscuro", value=bool(_safe_int(base.get("sensor_tema_oscuro"), 0)), key="link_sensor_oscuro")
        nivel_oscuridad = s3.slider("Nivel de oscuridad", 0, 5, _safe_int(base.get("nivel_oscuridad"), 0), key="link_nivel_oscuro")
        tipo_tema_oscuro = s3.selectbox("Tipo de tema oscuro", TIPOS_TEMA_OSCURO, index=_idx(TIPOS_TEMA_OSCURO, base.get("tipo_tema_oscuro", "No aplica"), 0), key="link_tipo_oscuro")

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
    }
    return {
        "comentario": comentario.strip(),
        "resena": resena.strip(),
        "mood": mood.strip(),
        "frases_favoritas": frases_favoritas.strip(),
        "escenas_favoritas": escenas_favoritas.strip(),
        "momentos_marcantes": momentos_marcantes.strip(),
        "spoilers": spoilers.strip(),
        "lo_recomendaria": _select_value(lo_recomendaria),
        "fecha_agregada_pendientes": _optional_date(usar_fecha_pendiente, fecha_pendiente_val),
        "fecha_inicio": _optional_date(usar_fecha_inicio, fecha_inicio_val),
        "fecha_fin": _optional_date(usar_fecha_fin, fecha_fin_val),
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
        "senales_wrapped_json": _json(senales_wrapped),
        "sensores_wrapped_json": _json(sensores_wrapped),
    }


def render_importar_link(obras, importar_desde_link, guardar_importado, save_uploaded_file, portadas_dir):
    st.subheader("🔗 Importar desde link")
    st.caption("Importador avanzado con detección de fuente, AO3, fanfiction/canon, temporadas, duplicados, calidad 0/100, campos de Wrapped e importación múltiple.")

    tab_one, tab_many = st.tabs(["Un link", "Varios links"])

    with tab_one:
        url = st.text_input("Link de la obra", key="link_single_url")
        detected = _detect_source(url)
        st.info(f"Fuente detectada: **{detected['fuente']}** · Tipo sugerido: **{detected['tipo']}** · Confiabilidad: **{detected['confiabilidad']}/100**")
        if detected["ao3"]:
            st.success(f"AO3 detectado · Work ID: {_ao3_work_id(url)} · Solo se guardará metadata pública/link, no capítulos completos.")

        if st.button("Detectar metadata desde link", key="link_detect_metadata"):
            if not url.strip():
                st.error("Pega un link primero.")
            else:
                try:
                    st.session_state["link_metadata"] = importar_desde_link(url.strip())
                    st.success("Metadata detectada. Revísala antes de importar.")
                except Exception as exc:
                    st.session_state["link_metadata"] = {"titulo": "", "autor": "", "sinopsis": "", "url_fuente": url.strip(), "link_original": url.strip()}
                    st.warning(f"No se pudo leer metadata automática. Puedes completar manualmente. Detalle: {exc}")

        base = st.session_state.get("link_metadata", {}) or {}
        if url.strip():
            base.setdefault("url_fuente", url.strip())
            base.setdefault("link_original", url.strip())

        st.markdown("### Revisar antes de importar")
        col_a, col_b = st.columns(2)
        with col_a:
            titulo = st.text_input("Título", value=base.get("titulo", ""), key="link_titulo")
            autor = st.text_input("Autor / creador / estudio", value=base.get("autor", ""), key="link_autor")
            tipo_index = TIPOS_LINK.index(detected["tipo"]) if detected["tipo"] in TIPOS_LINK else 0
            tipo = st.selectbox("Tipo", TIPOS_LINK, index=tipo_index, key="link_tipo")
            estado = st.selectbox("Estado personal", ESTADOS, index=0, key="link_estado")
            favorito = st.checkbox("Marcar como favorito", key="link_favorito")
            estrellas = st.slider("Tu puntuación personal ⭐", 0, 5, 0, 1, key="link_estrellas")
            clasificacion = st.slider("Nota / clasificación", 0.0, 10.0, float(base.get("clasificacion") or 0.0), 0.5, key="link_clasificacion")
            prioridad = st.slider("Prioridad", 0, 5, _safe_int(base.get("prioridad"), 0), key="link_prioridad")
        with col_b:
            estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION, index=0 if detected["ao3"] else 6, key="link_estado_pub")
            fecha_pub = st.text_input("Fecha de publicación", value=base.get("fecha_publicacion", ""), key="link_fecha_pub")
            division = st.selectbox("Tipo de división", DIVISIONES_OBRA, key="link_division")
            temporada_actual = st.number_input("Temporada/arco actual", min_value=1, value=1, step=1, key="link_temp_actual")
            temporada_total = st.number_input("Temporadas/arcos totales", min_value=1, value=1, step=1, key="link_temp_total")
            ao3_tracking = st.checkbox("Activar seguimiento AO3", value=detected["ao3"], disabled=not detected["ao3"], key="link_ao3_tracking")

        col_c, col_d, col_e = st.columns(3)
        with col_c:
            caps_publicados_desconocidos = st.checkbox("Publicados desconocidos (?)", value=_safe_int(base.get("capitulos_publicados") or base.get("capitulo_total"), 0) <= 0, key="link_caps_pub_unknown")
            caps_publicados = st.number_input("Capítulos publicados", min_value=0, value=_safe_int(base.get("capitulos_publicados") or base.get("capitulo_total"), 0), step=1, disabled=caps_publicados_desconocidos, key="link_caps_pub")
        with col_d:
            caps_total_desconocido = st.checkbox("Total esperado desconocido (?)", value=_safe_int(base.get("capitulo_total"), 0) <= 0, key="link_caps_total_unknown")
            caps_total = st.number_input("Capítulos totales esperados", min_value=0, value=_safe_int(base.get("capitulo_total") or base.get("capitulos_publicados"), 0), step=1, disabled=caps_total_desconocido, key="link_caps_total")
        with col_e:
            caps_vistos = st.number_input("Capítulos vistos/leídos", min_value=0, value=0, step=1, key="link_caps_vistos")

        etiquetas = st.text_input("Etiquetas", value=base.get("etiquetas", "importado, link"), key="link_tags")
        portada_url = st.text_input("URL portada", value=base.get("portada_path", ""), key="link_portada_url")
        portada_upload = st.file_uploader("Subir portada desde tu dispositivo", type=["jpg", "jpeg", "png", "webp"], key="link_portada_upload")
        link_respaldo = st.text_input("Link respaldo / copia", value=base.get("link_respaldo", ""), key="link_respaldo")
        sinopsis = st.text_area("Sinopsis / descripción", value=base.get("sinopsis", ""), height=180, key="link_sinopsis")

        fanfic_data = {}
        if tipo == "Fanfiction" or detected["fanfic"]:
            st.markdown("### Fanfiction / canon / crossover")
            fanfic_data = render_fanfiction_fields(prefix="link_fanfic")

        manual_extra = _render_manual_extra_fields(base)

        caps_publicados_final = 0 if caps_publicados_desconocidos else int(caps_publicados)
        caps_total_final = 0 if caps_total_desconocido else int(caps_total)
        edits = {
            "titulo": titulo.strip(),
            "autor": autor.strip(),
            "tipo": tipo,
            "estado_lectura": estado,
            "estado_publicacion": estado_pub,
            "fecha_publicacion": fecha_pub.strip(),
            "division_obra": division,
            "temporada_actual": int(temporada_actual),
            "temporada_total": int(max(temporada_total, temporada_actual)),
            "capitulo_total": caps_total_final,
            "capitulos_publicados": caps_publicados_final,
            "capitulos_vistos": int(caps_vistos),
            "capitulo_actual": int(caps_vistos),
            "estrellas": int(estrellas),
            "clasificacion": float(clasificacion),
            "prioridad": int(prioridad),
            "favorito": 1 if favorito else 0,
            "sinopsis": sinopsis.strip(),
            "etiquetas": etiquetas.strip(),
            "url_fuente": url.strip(),
            "link_original": url.strip(),
            "link_respaldo": link_respaldo.strip(),
            "portada_path": portada_url.strip(),
            "ao3_tracking": 1 if ao3_tracking and detected["ao3"] else 0,
        }
        edits.update(manual_extra)
        item_preview = _build_item(base, detected, edits, fanfic_data)

        st.markdown("### Calidad, duplicados y confirmación")
        quality = _render_quality(item_preview)
        dupes = _find_duplicates(url, titulo, autor, obras)
        if dupes:
            st.warning(f"Posibles duplicados encontrados: {len(dupes)}")
            for d in dupes:
                st.write(f"{d['score']}% · {d['obra'].get('titulo')} · {', '.join(d['motivos'])}")
        else:
            st.success("No se detectaron duplicados exactos por link/AO3/título+autor.")

        progreso_max = max(caps_publicados_final, caps_total_final)
        st.info(f"Se importará como **{tipo}**, estado **{estado}**, {division.lower()} **T{int(temporada_actual)} de {int(max(temporada_total, temporada_actual))}**, progreso **{int(caps_vistos)} / {progreso_max if progreso_max else '?'}**, calidad **{quality}/100**.")
        if st.button("✅ Confirmar importación desde link", key="link_confirm_import"):
            if not url.strip():
                st.error("El link es obligatorio.")
            elif not titulo.strip():
                st.error("El título es obligatorio antes de importar.")
            elif int(caps_vistos) > progreso_max and progreso_max > 0:
                st.error("Los capítulos vistos/leídos no pueden ser mayores que los publicados/totales.")
            else:
                final_item = dict(item_preview)
                if portada_upload is not None:
                    final_item["portada_path"] = save_uploaded_file(portada_upload, portadas_dir)
                    final_item["calidad_datos"] = _quality(final_item)[0]
                guardar_importado(final_item, tipo, estado)
                st.success(f"Importado desde link: {titulo}")

    with tab_many:
        st.markdown("### Importar varios links")
        raw_links = st.text_area("Pega varios links, uno por línea", height=180, key="multi_links")
        estado_lote = st.selectbox("Estado para lote", ESTADOS, index=0, key="multi_estado")
        tags_lote = st.text_input("Etiquetas para lote", value="importado, lote", key="multi_tags")
        if st.button("Preparar cola de links", key="multi_prepare"):
            links = [line.strip() for line in raw_links.splitlines() if line.strip()]
            queue = []
            for link in links:
                detected_multi = _detect_source(link)
                queue.append({
                    "url_fuente": link,
                    "link_original": link,
                    "titulo": link.rstrip("/").split("/")[-1] or "Sin título",
                    "autor": "",
                    "tipo": detected_multi["tipo"],
                    "fuente_importacion": detected_multi["fuente"],
                    "fuente_confiabilidad": detected_multi["confiabilidad"],
                    "etiquetas": tags_lote,
                    "ao3_work_id": _ao3_work_id(link),
                    "ao3_tracking": 1 if detected_multi["ao3"] else 0,
                    "temporada_actual": 1,
                    "temporada_total": 1,
                    "capitulo_actual": 0,
                    "capitulo_total": 0,
                    "capitulos_publicados": 0,
                    "capitulos_vistos": 0,
                    "calidad_datos": 30,
                })
            st.session_state["link_batch_queue"] = queue
            st.success(f"Links preparados: {len(queue)}")

        queue = st.session_state.get("link_batch_queue", [])
        if queue:
            st.markdown("### Cola de links")
            selected = []
            for idx, item in enumerate(queue):
                checked = st.checkbox(f"{idx + 1}. {item.get('titulo')} · {item.get('fuente_importacion')} · {item.get('tipo')}", value=True, key=f"multi_select_{idx}")
                if checked:
                    selected.append(idx)
            if st.button("✅ Importar links seleccionados", key="multi_import"):
                total = 0
                for idx, item in enumerate(queue):
                    if idx in selected:
                        guardar_importado(item, item.get("tipo") or "Webnovel", estado_lote)
                        total += 1
                st.success(f"Importados desde lote: {total}")
                st.session_state["link_batch_queue"] = []
