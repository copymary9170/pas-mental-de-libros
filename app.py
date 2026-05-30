from datetime import date
from pathlib import Path
import sys
import traceback

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

APP_VERSION = "Paz Mental deploy 2026-05-28 v16 - agregar manual avanzado"

try:
    import src.database as db
    from src.styles import apply_styles
    from src.utils import (
        ensure_dirs,
        save_uploaded_file,
        PORTADAS_DIR,
        RESPALDOS_DIR,
        buscar_libros_openlibrary,
        buscar_series_tvmaze,
        buscar_peliculas_itunes,
        buscar_peliculas_tmdb,
        buscar_series_tmdb,
        buscar_manga_jikan,
        buscar_webnovel_openlibrary,
        buscar_kdramas_tmdb,
        importar_desde_link,
    )
    from src.pages.cronometro import render_cronometro, fmt_time
    from src.pages.buscador import render_buscador_avanzado
    from src.pages.importar_link import render_importar_link
    from src.pages.calendario import render_calendario
    from src.pages.capitulos import render_capitulos
    from src.pages.fanfiction import render_fanfiction_fields, fanfiction_badges
    from src.pages.reportes import render_reportes
    from src.pages.canons import render_canons
    from src.pages.ao3_updates import render_ao3_updates
    from src.pages.diagnostico import render_diagnostico
    from src.pages.biblioteca import render_biblioteca
except Exception:
    st.set_page_config(page_title="Paz Mental - Error", page_icon="⚠️", layout="wide")
    st.error("La app falló durante la importación inicial. Copia este diagnóstico completo y pégalo en el chat.")
    st.code(traceback.format_exc(), language="python")
    st.stop()

st.set_page_config(page_title="Paz Mental", page_icon="📚", layout="wide")
apply_styles()
ensure_dirs()
db.init_db()
st.caption(APP_VERSION)

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
TIPOS = BOOK_TYPES + TV_TYPES
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
EXPECTATIVAS = ["No aplica", "ninguna", "baja", "media", "alta", "demasiado hype"]
RESULTADOS_EXPECTATIVA = ["No aplica", "supero", "cumplio", "decepciono", "fue diferente"]
TIPOS_ISEKAI = ["No aplica", "reencarnacion", "transmigracion", "invocacion", "sistema", "regreso en el tiempo", "villana", "juego", "portal", "otro"]
AMBIENTACIONES = ["No aplica", "contemporanea", "medieval", "victoriana", "antigua", "futurista", "distopica", "historica real", "fantasia historica", "otra"]
TIPOS_CRINGE = ["No aplica", "divertido", "incomodo", "vergüenza ajena", "malo", "delicioso"]
TIPOS_TEMA_OSCURO = ["No aplica", "violencia", "abuso", "manipulacion", "trauma", "moral cuestionable", "taboo narrativo", "otro"]


def buscar_global(query, fuente):
    q = query.strip()
    if fuente == "Libros":
        return buscar_libros_openlibrary(q), "book"
    if fuente == "Manga / manhwa / novelas ligeras":
        return (buscar_manga_jikan(q) or buscar_libros_openlibrary(q)), "manga"
    if fuente == "Webnovels":
        return (buscar_webnovel_openlibrary(q) or buscar_manga_jikan(q)), "webnovel"
    if fuente == "Peliculas":
        resultados = buscar_peliculas_tmdb(q, TMDB_API_KEY) if TMDB_API_KEY else []
        return (resultados or buscar_peliculas_itunes(q) or buscar_series_tvmaze(q)), "movie"
    if fuente == "Kdramas":
        resultados = buscar_kdramas_tmdb(q, TMDB_API_KEY) if TMDB_API_KEY else []
        return (resultados or buscar_series_tvmaze(q)), "kdrama"
    resultados = buscar_series_tmdb(q, TMDB_API_KEY) if TMDB_API_KEY else []
    return (resultados or buscar_series_tvmaze(q)), "tv"


def _to_int(value, default=0):
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


def guardar_importado(item, tipo, estado):
    cap_total = _to_int(item.get("capitulo_total"), 0)
    cap_publicados = _to_int(item.get("capitulos_publicados"), cap_total)
    cap_vistos = _to_int(item.get("capitulos_vistos", item.get("capitulo_actual")), 0)
    temporada_actual = max(1, _to_int(item.get("temporada_actual"), 1))
    temporada_total = max(1, _to_int(item.get("temporada_total"), temporada_actual))
    motivo_extra = []
    if item.get("division_obra"):
        motivo_extra.append(f"División: {item.get('division_obra')}")
    if item.get("ao3_work_id"):
        motivo_extra.append(f"AO3 work ID: {item.get('ao3_work_id')}")
    if item.get("ao3_tracking"):
        motivo_extra.append("Seguimiento AO3 activado")

    data = {
        "titulo": item.get("titulo", "Sin titulo"),
        "autor": item.get("autor", ""),
        "tipo": tipo,
        "obra_original_tipo": item.get("obra_original_tipo", ""),
        "obra_original_nombre": item.get("obra_original_nombre", ""),
        "fandom": item.get("fandom", ""),
        "ship": item.get("ship", ""),
        "universo_au": item.get("universo_au", ""),
        "fuente_fanfic": item.get("fuente_fanfic", ""),
        "es_crossover": _to_int(item.get("es_crossover"), 0),
        "crossover_obras": item.get("crossover_obras", ""),
        "crossover_fandoms": item.get("crossover_fandoms", ""),
        "crossover_tipo": item.get("crossover_tipo", ""),
        "crossover_notas": item.get("crossover_notas", ""),
        "division_obra": item.get("division_obra", ""),
        "ao3_work_id": item.get("ao3_work_id", ""),
        "ao3_tracking": _to_int(item.get("ao3_tracking"), 0),
        "fuente_confiabilidad": _to_int(item.get("fuente_confiabilidad"), 0),
        "calidad_datos": _to_int(item.get("calidad_datos"), 0),
        "ultima_importacion_fuente": item.get("fuente_importacion", ""),
        "clasificacion": 0,
        "estrellas": _to_int(item.get("estrellas"), 0),
        "estado_lectura": estado,
        "estado_publicacion": item.get("estado_publicacion", "No aplica"),
        "fecha_publicacion": item.get("fecha_publicacion", ""),
        "temporada_actual": temporada_actual,
        "temporada_total": temporada_total,
        "capitulo_actual": cap_vistos,
        "capitulo_total": cap_total,
        "capitulos_publicados": cap_publicados,
        "capitulos_vistos": cap_vistos,
        "sinopsis": item.get("sinopsis", ""),
        "etiquetas": item.get("etiquetas", "importado"),
        "link_original": item.get("link_original") or item.get("url_fuente", ""),
        "link_respaldo": "",
        "portada_path": item.get("portada_path", ""),
        "respaldo_path": "",
        "motivo_estado": f"Importado desde {item.get('fuente_importacion', 'fuente externa')}. Año: {item.get('anio') or 'N/D'}. URL: {item.get('url_fuente') or 'N/D'}. {' | '.join(motivo_extra)}",
        "favorito": _to_int(item.get("favorito"), 0),
        "fecha_inicio": str(date.today()),
        "fecha_fin": None,
    }
    db.add_obra(data)


obras = db.list_obras()
df = pd.DataFrame(obras)

st.markdown("""
<div class="app-hero">
  <div>
    <div class="hero-label">Bookmory + TV Time personal</div>
    <h1>Paz Mental</h1>
    <p>Biblioteca de libros, fanfics, manga, manhwa, webnovels, kdramas, series, anime y peliculas.</p>
  </div>
</div>
""", unsafe_allow_html=True)

tab_timer, tab_search, tab_link, tab_calendar, tab_ao3, tab_books, tab_reports, tab_canons, tab_add, tab_chapters, tab_diag, tab_export = st.tabs([
    "⏱️ Cronómetro",
    "🔎 Buscar e importar",
    "🔗 Importar link",
    "📅 Calendario",
    "🔔 AO3",
    "📚 Biblioteca",
    "🏆 Wrapped / Reportes",
    "🌌 Canons",
    "➕ Agregar manual",
    "📝 Capitulos",
    "🧰 Diagnóstico",
    "⬇️ Exportar",
])

with tab_timer:
    render_cronometro(obras, db.add_actividad, db.update_obra, db.list_actividad)

with tab_search:
    st.info("Versión del buscador: Fase 8 pro con cache, merge seguro, paginación, tags y preview.")
    render_buscador_avanzado(obras, buscar_global, guardar_importado)

with tab_link:
    render_importar_link(obras, importar_desde_link, guardar_importado, save_uploaded_file, PORTADAS_DIR)

with tab_calendar:
    render_calendario(db.list_actividad)

with tab_ao3:
    render_ao3_updates(obras)

with tab_books:
    render_biblioteca(obras)

with tab_reports:
    render_reportes(obras, db.list_actividad)

with tab_canons:
    render_canons(db.add_canon, db.list_canons)

with tab_add:
    st.subheader("Agregar obra manualmente")
    st.caption("Formulario ampliado: lo básico sigue arriba, y los campos extra ayudan a reportes, rankings y Wrapped.")
    tipo_preview = st.selectbox("Tipo de obra", TIPOS, key="manual_tipo_visible")
    fanfic_data = {}
    if tipo_preview == "Fanfiction":
        st.info("Seleccionaste Fanfiction. Aquí puedes registrar canon, fandom, ship, AU y crossovers.")
        fanfic_data = render_fanfiction_fields(prefix="manual_visible")

    with st.form("obra_form_manual"):
        st.markdown("### Datos principales")
        c1, c2 = st.columns(2)
        with c1:
            titulo = st.text_input("Título *")
            autor = st.text_input("Autor / creador / estudio")
            estado = st.selectbox("Estado personal", ESTADOS)
            estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION)
            favorito = st.checkbox("Marcar como favorito")
        with c2:
            st.caption(f"Tipo seleccionado: {tipo_preview}")
            etiquetas = st.text_input("Etiquetas / géneros", placeholder="romance, fantasía, kdrama, comfort...")
            link_original = st.text_input("Link original / fuente")
            prioridad = st.slider("Prioridad", 0, 5, 0)
            estrellas = st.slider("Estrellas", 0, 5, 0)
            clasificacion = st.slider("Nota / clasificación", 0.0, 10.0, 0.0, 0.5)

        sinopsis = st.text_area("Sinopsis / descripción de la obra", height=140)
        comentario = st.text_area("Comentario corto / primera impresión", height=90)
        resena = st.text_area("Reseña / opinión personal", height=120)
        mood = st.text_input("Mood", placeholder="cozy, intenso, lloré, fangirl, cringe delicioso...")
        frases_favoritas = st.text_area("Frases favoritas", height=80)

        st.markdown("### Fechas y progreso")
        c3, c4, c5 = st.columns(3)
        with c3:
            usar_fecha_publicacion = st.checkbox("Agregar fecha de publicación / estreno")
            fecha_publicacion_val = st.date_input("Fecha de publicación / estreno", value=date.today(), disabled=not usar_fecha_publicacion)
            usar_fecha_pendiente = st.checkbox("Agregar fecha a pendientes")
            fecha_pendiente_val = st.date_input("Fecha agregada a pendientes", value=date.today(), disabled=not usar_fecha_pendiente)
        with c4:
            usar_fecha_inicio = st.checkbox("Agregar fecha de inicio", value=True)
            fecha_inicio_val = st.date_input("Fecha de inicio", value=date.today(), disabled=not usar_fecha_inicio)
            usar_fecha_fin = st.checkbox("Agregar fecha de finalización")
            fecha_fin_val = st.date_input("Fecha de finalización", value=date.today(), disabled=not usar_fecha_fin)
        with c5:
            temporada_actual = st.number_input("Temporada actual", min_value=1, value=1, step=1)
            temporada_total = st.number_input("Temporadas totales", min_value=1, value=1, step=1)
            cap_vistos = st.number_input("Capítulos leídos/vistos", min_value=0, step=1)
            cap_pub = st.number_input("Capítulos publicados/emitidos", min_value=0, step=1)
            cap_total = st.number_input("Capítulos totales esperados", min_value=0, step=1)

        st.markdown("### Ambientación y subgénero")
        c6, c7, c8 = st.columns(3)
        with c6:
            es_isekai = st.checkbox("Es isekai")
            tipo_isekai = st.selectbox("Tipo de isekai", TIPOS_ISEKAI)
            epoca_ambientacion = st.selectbox("Época / ambientación", AMBIENTACIONES)
            mundo_principal = st.text_input("País / cultura / reino / mundo principal")
        with c7:
            nivel_construccion_mundo = st.slider("Construcción de mundo", 0, 5, 0)
            nivel_politica_intriga = st.slider("Política / intriga", 0, 5, 0)
            nivel_magia_sistema = st.slider("Magia / sistema de poder", 0, 5, 0)
        with c8:
            nivel_romance = st.slider("Romance", 0, 5, 0)
            nivel_accion = st.slider("Acción", 0, 5, 0)
            nivel_drama = st.slider("Drama", 0, 5, 0)

        st.markdown("### Expectativas, esperanza y final")
        c9, c10, c11 = st.columns(3)
        with c9:
            expectativa_inicial = st.selectbox("Expectativa inicial", EXPECTATIVAS)
            nivel_esperanza_inicial = st.slider("Nivel de esperanza inicial", 0, 5, 0)
            le_tenia_esperanza = st.checkbox("Le tenía esperanza")
            le_tenia_pocas_esperanzas = st.checkbox("Le tenía pocas esperanzas")
        with c10:
            resultado_expectativa = st.selectbox("Resultado contra expectativa", RESULTADOS_EXPECTATIVA)
            nivel_decepcion = st.slider("Nivel de decepción", 0, 5, 0)
            nivel_satisfaccion_general = st.slider("Satisfacción general", 0, 5, 0)
            satisfaccion_final = st.slider("Satisfacción del final", 0, 5, 0)
        with c11:
            final_salvo_obra = st.checkbox("El final salvó la obra")
            final_arruino_obra = st.checkbox("El final arruinó la obra")
            autor_arruino_final = st.checkbox("El autor arruinó la obra al final")
        motivo_esperanza = st.text_area("Por qué tenía esperanza o pocas esperanzas", height=70)
        como_arruino_final = st.text_area("Cómo la arruinó el autor al final", height=70)
        comentario_final = st.text_area("Comentario del final", height=70)

        st.markdown("### Sensores para Wrapped")
        c12, c13, c14 = st.columns(3)
        with c12:
            sensor_lujuria = st.checkbox("Sensor lujuria / caliente")
            nivel_lujuria = st.slider("Nivel de lujuria", 0, 5, 0)
            sensor_llanto = st.checkbox("Sensor llanto")
            nivel_llanto = st.slider("Nivel de llanto", 0, 5, 0)
            veces_llore = st.number_input("Veces que lloré", min_value=0, step=1)
            sensor_risa = st.checkbox("Sensor risa")
            nivel_risa = st.slider("Nivel de risa", 0, 5, 0)
        with c13:
            sensor_aburrimiento = st.checkbox("Sensor aburrimiento")
            nivel_aburrimiento = st.slider("Nivel de aburrimiento", 0, 5, 0)
            sensor_cringe = st.checkbox("Sensor cringe")
            nivel_cringe = st.slider("Nivel de cringe", 0, 5, 0)
            tipo_cringe = st.selectbox("Tipo de cringe", TIPOS_CRINGE)
            sensor_red_flag = st.checkbox("Sensor red flag")
            nivel_red_flag = st.slider("Nivel de red flag", 0, 5, 0)
        with c14:
            sensor_resaca_emocional = st.checkbox("Sensor resaca emocional")
            nivel_resaca_emocional = st.slider("Nivel de resaca emocional", 0, 5, 0)
            sensor_tema_oscuro = st.checkbox("Sensor tema oscuro / cuestionable")
            nivel_oscuridad = st.slider("Nivel de oscuridad", 0, 5, 0)
            tipo_tema_oscuro = st.selectbox("Tipo de tema oscuro", TIPOS_TEMA_OSCURO)
            sensor_obra_larga = st.checkbox("Sensor obra demasiado larga")
            nivel_cansancio_longitud = st.slider("Cansancio por longitud", 0, 5, 0)

        st.markdown("### Archivos e imágenes")
        portada = st.file_uploader("Subir portada", type=["jpg", "jpeg", "png", "webp"])
        st.markdown("### Modo de respaldo")
        modo_respaldo = st.radio("¿Cómo quieres guardar el contenido?", ["Solo registrar la obra", "Subir obra completa", "Subir capítulos uno por uno", "Subir varios capítulos de golpe"])
        respaldo = st.file_uploader("Archivo completo de la obra", type=["pdf", "epub", "txt", "docx", "zip"]) if modo_respaldo == "Subir obra completa" else None
        if modo_respaldo in ["Subir capítulos uno por uno", "Subir varios capítulos de golpe"]:
            st.caption("Este modo queda registrado en la obra. Los capítulos se pueden cargar desde la pestaña 📝 Capitulos.")

        guardar_manual = st.form_submit_button("Guardar obra")
        if guardar_manual:
            if not titulo.strip():
                st.error("El título es obligatorio")
            else:
                data = {
                    "titulo": titulo.strip(),
                    "autor": autor.strip(),
                    "tipo": tipo_preview,
                    "clasificacion": float(clasificacion),
                    "estrellas": int(estrellas),
                    "comentario": comentario.strip(),
                    "resena": resena.strip(),
                    "mood": mood.strip(),
                    "frases_favoritas": frases_favoritas.strip(),
                    "estado_lectura": estado,
                    "estado_publicacion": estado_pub,
                    "fecha_publicacion": _optional_date(usar_fecha_publicacion, fecha_publicacion_val) or "",
                    "fecha_agregada_pendientes": _optional_date(usar_fecha_pendiente, fecha_pendiente_val) or "",
                    "temporada_actual": int(temporada_actual),
                    "temporada_total": int(temporada_total),
                    "capitulo_actual": int(cap_vistos),
                    "capitulos_vistos": int(cap_vistos),
                    "capitulos_publicados": int(cap_pub),
                    "capitulo_total": int(cap_total),
                    "sinopsis": sinopsis.strip(),
                    "etiquetas": etiquetas.strip(),
                    "link_original": link_original.strip(),
                    "link_respaldo": "",
                    "portada_path": save_uploaded_file(portada, PORTADAS_DIR),
                    "respaldo_path": save_uploaded_file(respaldo, RESPALDOS_DIR),
                    "motivo_estado": modo_respaldo,
                    "favorito": _bool_int(favorito),
                    "prioridad": int(prioridad),
                    "fecha_inicio": _optional_date(usar_fecha_inicio, fecha_inicio_val),
                    "fecha_fin": _optional_date(usar_fecha_fin, fecha_fin_val),
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
                }
                if tipo_preview == "Fanfiction":
                    data.update(fanfic_data)
                db.add_obra(data)
                st.success("Obra guardada con datos ampliados.")

with tab_chapters:
    render_capitulos(obras, db.list_capitulos, db.get_obra, db.add_capitulo)

with tab_diag:
    render_diagnostico()

with tab_export:
    st.subheader("Exportar")
    if df.empty:
        st.info("No hay datos para exportar.")
    else:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, "paz_mental_export.csv", "text/csv")
        st.download_button("Descargar JSON", df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"), "paz_mental_export.json", "application/json")
