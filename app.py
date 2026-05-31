from datetime import date
from pathlib import Path
import sys
import traceback

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

APP_VERSION = "Paz Mental deploy 2026-05-30 v25 - biblioteca con evolución por capítulos"

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
    from src.pages.biblioteca_insights import render_biblioteca_insights
    from src.pages.agregar_manual import render_agregar_manual
    from src.pages.inicio import render_inicio
    from src.pages.ruleta import render_ruleta
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

NAV_OPTIONS = [
    "🏠 Inicio",
    "🔎 Buscar",
    "⏱️ Cronómetro",
    "🏆 Wrapped",
    "📚 Biblioteca",
    "🎲 Ruleta",
    "➕ Agregar",
    "🔗 Links",
    "🔔 AO3",
    "📝 Capítulos",
    "📅 Calendario",
    "🌌 Canons",
    "🧰 Diagnóstico",
    "⬇️ Exportar",
]


def ir_a(seccion):
    st.session_state["main_nav"] = seccion
    st.rerun()


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


def _to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
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
        bool(item.get("mood") or item.get("resena") or item.get("comentario")),
    ]
    weights = [12, 8, 8, 12, 12, 12, 8, 8, 8]
    return min(100, sum(w for ok, w in zip(checks, weights) if ok))


def guardar_importado(item, tipo, estado):
    cap_total = _to_int(item.get("capitulo_total"), 0)
    cap_publicados = _to_int(item.get("capitulos_publicados"), cap_total)
    cap_vistos = _to_int(item.get("capitulos_vistos", item.get("capitulo_actual")), 0)
    temporada_actual = max(1, _to_int(item.get("temporada_actual"), 1))
    temporada_total = max(1, _to_int(item.get("temporada_total"), temporada_actual))
    fuente = item.get("fuente_importacion", item.get("ultima_importacion_fuente", "fuente externa"))

    data = dict(item)
    data.update({
        "titulo": item.get("titulo", "Sin titulo"),
        "autor": item.get("autor", ""),
        "tipo": tipo or item.get("tipo", "Otro"),
        "estado_lectura": estado or item.get("estado_lectura", "Pendiente"),
        "estado_publicacion": item.get("estado_publicacion", "No aplica"),
        "temporada_actual": temporada_actual,
        "temporada_total": temporada_total,
        "capitulo_actual": cap_vistos,
        "capitulo_total": cap_total,
        "capitulos_publicados": cap_publicados,
        "capitulos_vistos": cap_vistos,
        "ultimo_capitulo_visto": cap_vistos,
        "ultimo_capitulo_publicado": cap_publicados,
        "clasificacion": _to_float(item.get("clasificacion"), 0),
        "estrellas": _to_int(item.get("estrellas"), 0),
        "favorito": _to_int(item.get("favorito"), 0),
        "prioridad": _to_int(item.get("prioridad"), 0),
        "es_crossover": _to_int(item.get("es_crossover"), 0),
        "ao3_tracking": _to_int(item.get("ao3_tracking"), 0),
        "fuente_confiabilidad": _to_int(item.get("fuente_confiabilidad"), 0),
        "ultima_importacion_fuente": fuente,
        "fecha_inicio": item.get("fecha_inicio") or str(date.today()),
        "link_original": item.get("link_original") or item.get("url_fuente", ""),
        "link_respaldo": item.get("link_respaldo", ""),
        "portada_path": item.get("portada_path", ""),
        "etiquetas": item.get("etiquetas", "importado"),
        "sinopsis": item.get("sinopsis", ""),
        "motivo_estado": item.get("motivo_estado") or f"Importado desde {fuente}.",
    })
    data["calidad_datos"] = _to_int(item.get("calidad_datos"), 0) or _quality_import(data)
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

if "main_nav" not in st.session_state or st.session_state["main_nav"] not in NAV_OPTIONS:
    st.session_state["main_nav"] = "🏠 Inicio"

nav = st.radio("Navegación", NAV_OPTIONS, horizontal=True, key="main_nav", label_visibility="collapsed")

if nav != "🏠 Inicio":
    c_nav1, c_nav2 = st.columns(2)
    with c_nav1:
        if st.button("🏠 Volver al inicio", key=f"volver_inicio_{nav}"):
            ir_a("🏠 Inicio")
    with c_nav2:
        if st.button("🔙 Ir a biblioteca", key=f"volver_biblioteca_{nav}"):
            ir_a("📚 Biblioteca")

if nav == "🏠 Inicio":
    render_inicio(obras)
elif nav == "🔎 Buscar":
    st.info("Versión del buscador: Fase 8 pro con cache, merge seguro, paginación, tags y preview.")
    render_buscador_avanzado(obras, buscar_global, guardar_importado)
elif nav == "⏱️ Cronómetro":
    render_cronometro(obras, db.add_actividad, db.update_obra, db.list_actividad)
elif nav == "🏆 Wrapped":
    render_reportes(obras, db.list_actividad, getattr(db, "list_capitulos", None), getattr(db, "list_votos_personaje", None))
elif nav == "📚 Biblioteca":
    render_biblioteca(obras)
    render_biblioteca_insights(obras, getattr(db, "list_capitulos", None))
elif nav == "🎲 Ruleta":
    render_ruleta(obras)
elif nav == "➕ Agregar":
    render_agregar_manual(obras, db.add_obra, save_uploaded_file, PORTADAS_DIR, RESPALDOS_DIR)
elif nav == "🔗 Links":
    render_importar_link(obras, importar_desde_link, guardar_importado, save_uploaded_file, PORTADAS_DIR)
elif nav == "🔔 AO3":
    render_ao3_updates(obras)
elif nav == "📝 Capítulos":
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
elif nav == "📅 Calendario":
    render_calendario(db.list_actividad)
elif nav == "🌌 Canons":
    render_canons(db.add_canon, db.list_canons)
elif nav == "🧰 Diagnóstico":
    render_diagnostico()
elif nav == "⬇️ Exportar":
    st.subheader("Exportar")
    if df.empty:
        st.info("No hay datos para exportar.")
    else:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, "paz_mental_export.csv", "text/csv")
        st.download_button("Descargar JSON", df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"), "paz_mental_export.json", "application/json")
