from datetime import date
from pathlib import Path
import sys
import traceback

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

APP_VERSION = "Paz Mental deploy 2026-05-30 v22 - fallback personajes"

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
    from src.pages.cronometro import render_cronometro
    from src.pages.buscador import render_buscador_avanzado
    from src.pages.importar_link import render_importar_link
    from src.pages.calendario import render_calendario
    from src.pages.capitulos import render_capitulos
    from src.pages.reportes import render_reportes
    from src.pages.canons import render_canons
    from src.pages.ao3_updates import render_ao3_updates
    from src.pages.diagnostico import render_diagnostico
    from src.pages.biblioteca import render_biblioteca
    from src.pages.agregar_manual import render_agregar_manual
    from src.pages.inicio import render_inicio
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


def _quality_import(item):
    checks = [
        bool(item.get("titulo")),
        bool(item.get("autor")),
        bool(item.get("tipo")),
        bool(item.get("sinopsis")),
        bool(item.get("portada_path")),
        bool(item.get("link_original") or item.get("url_fuente")),
        _to_int(item.get("capitulo_total") or item.get("capitulos_publicados"), 0) > 0,
        bool(item.get("fecha_publicacion") or item.get("anio")),
    ]
    weights = [15, 10, 10, 15, 15, 15, 10, 10]
    return sum(w for ok, w in zip(checks, weights) if ok)


def guardar_importado(item, tipo, estado):
    cap_total = _to_int(item.get("capitulo_total"), 0)
    cap_publicados = _to_int(item.get("capitulos_publicados"), cap_total)
    cap_vistos = _to_int(item.get("capitulos_vistos", item.get("capitulo_actual")), 0)
    temporada_actual = max(1, _to_int(item.get("temporada_actual"), 1))
    temporada_total = max(1, _to_int(item.get("temporada_total"), temporada_actual))
    fuente = item.get("fuente_importacion", item.get("ultima_importacion_fuente", "fuente externa"))
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
        "calidad_datos": _to_int(item.get("calidad_datos"), 0) or _quality_import({**item, "tipo": tipo}),
        "ultima_importacion_fuente": fuente,
        "clasificacion": float(item.get("clasificacion") or 0),
        "estrellas": _to_int(item.get("estrellas"), 0),
        "comentario": item.get("comentario", ""),
        "resena": item.get("resena", ""),
        "mood": item.get("mood", ""),
        "frases_favoritas": item.get("frases_favoritas", ""),
        "estado_lectura": estado,
        "estado_publicacion": item.get("estado_publicacion", "No aplica"),
        "fecha_publicacion": item.get("fecha_publicacion", item.get("anio", "")),
        "fecha_agregada_pendientes": item.get("fecha_agregada_pendientes", ""),
        "temporada_actual": temporada_actual,
        "temporada_total": temporada_total,
        "capitulo_actual": cap_vistos,
        "capitulo_total": cap_total,
        "capitulos_publicados": cap_publicados,
        "capitulos_vistos": cap_vistos,
        "sinopsis": item.get("sinopsis", ""),
        "etiquetas": item.get("etiquetas", "importado"),
        "link_original": item.get("link_original") or item.get("url_fuente", ""),
        "link_respaldo": item.get("link_respaldo", ""),
        "portada_path": item.get("portada_path", ""),
        "respaldo_path": item.get("respaldo_path", ""),
        "motivo_estado": item.get("motivo_estado") or f"Importado desde {fuente}. Año: {item.get('anio') or 'N/D'}. URL: {item.get('url_fuente') or item.get('link_original') or 'N/D'}. {' | '.join(motivo_extra)}",
        "favorito": _to_int(item.get("favorito"), 0),
        "prioridad": _to_int(item.get("prioridad"), 0),
        "fecha_inicio": item.get("fecha_inicio") or str(date.today()),
        "fecha_fin": item.get("fecha_fin"),
        "expectativa_inicial": item.get("expectativa_inicial", ""),
        "nivel_esperanza_inicial": _to_int(item.get("nivel_esperanza_inicial"), 0),
        "le_tenia_esperanza": _to_int(item.get("le_tenia_esperanza"), 0),
        "le_tenia_pocas_esperanzas": _to_int(item.get("le_tenia_pocas_esperanzas"), 0),
        "motivo_esperanza": item.get("motivo_esperanza", ""),
        "resultado_expectativa": item.get("resultado_expectativa", ""),
        "nivel_decepcion": _to_int(item.get("nivel_decepcion"), 0),
        "nivel_satisfaccion_general": _to_int(item.get("nivel_satisfaccion_general"), 0),
        "satisfaccion_final": _to_int(item.get("satisfaccion_final"), 0),
        "final_salvo_obra": _to_int(item.get("final_salvo_obra"), 0),
        "final_arruino_obra": _to_int(item.get("final_arruino_obra"), 0),
        "autor_arruino_final": _to_int(item.get("autor_arruino_final"), 0),
        "como_arruino_final": item.get("como_arruino_final", ""),
        "comentario_final": item.get("comentario_final", ""),
        "es_isekai": _to_int(item.get("es_isekai"), 0),
        "tipo_isekai": item.get("tipo_isekai", ""),
        "epoca_ambientacion": item.get("epoca_ambientacion", ""),
        "mundo_principal": item.get("mundo_principal", ""),
        "nivel_construccion_mundo": _to_int(item.get("nivel_construccion_mundo"), 0),
        "nivel_politica_intriga": _to_int(item.get("nivel_politica_intriga"), 0),
        "nivel_magia_sistema": _to_int(item.get("nivel_magia_sistema"), 0),
        "nivel_romance": _to_int(item.get("nivel_romance"), 0),
        "nivel_accion": _to_int(item.get("nivel_accion"), 0),
        "nivel_drama": _to_int(item.get("nivel_drama"), 0),
        "sensor_lujuria": _to_int(item.get("sensor_lujuria"), 0),
        "nivel_lujuria": _to_int(item.get("nivel_lujuria"), 0),
        "sensor_llanto": _to_int(item.get("sensor_llanto"), 0),
        "nivel_llanto": _to_int(item.get("nivel_llanto"), 0),
        "veces_llore": _to_int(item.get("veces_llore"), 0),
        "sensor_risa": _to_int(item.get("sensor_risa"), 0),
        "nivel_risa": _to_int(item.get("nivel_risa"), 0),
        "sensor_aburrimiento": _to_int(item.get("sensor_aburrimiento"), 0),
        "nivel_aburrimiento": _to_int(item.get("nivel_aburrimiento"), 0),
        "sensor_cringe": _to_int(item.get("sensor_cringe"), 0),
        "nivel_cringe": _to_int(item.get("nivel_cringe"), 0),
        "tipo_cringe": item.get("tipo_cringe", ""),
        "sensor_red_flag": _to_int(item.get("sensor_red_flag"), 0),
        "nivel_red_flag": _to_int(item.get("nivel_red_flag"), 0),
        "sensor_resaca_emocional": _to_int(item.get("sensor_resaca_emocional"), 0),
        "nivel_resaca_emocional": _to_int(item.get("nivel_resaca_emocional"), 0),
        "sensor_tema_oscuro": _to_int(item.get("sensor_tema_oscuro"), 0),
        "nivel_oscuridad": _to_int(item.get("nivel_oscuridad"), 0),
        "tipo_tema_oscuro": item.get("tipo_tema_oscuro", ""),
        "sensor_obra_larga": _to_int(item.get("sensor_obra_larga"), 0),
        "nivel_cansancio_longitud": _to_int(item.get("nivel_cansancio_longitud"), 0),
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

tab_home, tab_search, tab_timer, tab_reports, tab_books, tab_add, tab_link, tab_ao3, tab_chapters, tab_calendar, tab_canons, tab_diag, tab_export = st.tabs([
    "🏠 Inicio",
    "🔎 Buscar",
    "⏱️ Cronómetro",
    "🏆 Wrapped",
    "📚 Biblioteca",
    "➕ Agregar",
    "🔗 Links",
    "🔔 AO3",
    "📝 Capítulos",
    "📅 Calendario",
    "🌌 Canons",
    "🧰 Diagnóstico",
    "⬇️ Exportar",
])

with tab_home:
    render_inicio(obras)

with tab_search:
    st.info("Versión del buscador: Fase 8 pro con cache, merge seguro, paginación, tags y preview.")
    render_buscador_avanzado(obras, buscar_global, guardar_importado)

with tab_timer:
    render_cronometro(obras, db.add_actividad, db.update_obra, db.list_actividad)

with tab_reports:
    render_reportes(obras, db.list_actividad)

with tab_books:
    render_biblioteca(obras)

with tab_add:
    render_agregar_manual(obras, db.add_obra, save_uploaded_file, PORTADAS_DIR, RESPALDOS_DIR)

with tab_link:
    render_importar_link(obras, importar_desde_link, guardar_importado, save_uploaded_file, PORTADAS_DIR)

with tab_ao3:
    render_ao3_updates(obras)

with tab_chapters:
    render_capitulos(
        obras,
        db.list_capitulos,
        db.get_obra,
        db.add_capitulo,
        getattr(db, "list_personajes", None),
        getattr(db, "add_personaje", None),
        getattr(db, "add_voto_personaje", None),
        getattr(db, "list_votos_personaje", None),
        save_uploaded_file,
        PORTADAS_DIR,
    )

with tab_calendar:
    render_calendario(db.list_actividad)

with tab_canons:
    render_canons(db.add_canon, db.list_canons)

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
