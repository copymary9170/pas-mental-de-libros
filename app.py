from datetime import date
from pathlib import Path
import sys
import traceback

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

APP_VERSION = "Paz Mental deploy 2026-05-30 v33 - avance restaurado"

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
    import src.pages.biblioteca as biblioteca_page
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

st.markdown("""
<style>
.lib-action-contrast-title{font-size:.74rem;font-weight:900;line-height:1.05;color:#0f2f73!important}
.lib-action-contrast-sub{font-size:.62rem;margin-top:1px;line-height:1.12;color:#1e3a8a!important;font-weight:750}
.lib-action-contrast-pill{display:inline-block;background:#dbeafe;color:#0f2f73;border:1px solid #93c5fd;border-radius:999px;padding:1px 7px;margin-left:4px;font-size:.62rem;font-weight:900}
.lib-action-contrast-note{font-size:.60rem;color:#334155!important}
div[data-testid="stButton"] button{border-radius:9px!important;padding:.18rem .28rem!important;min-height:26px!important;font-size:.70rem!important;font-weight:900!important}
div[data-testid="stNumberInput"] input{min-height:26px!important;font-size:.72rem!important;font-weight:800!important;color:#0f172a!important;background:#eff6ff!important}
div[data-baseweb="select"]>div{min-height:26px!important;font-size:.72rem!important;background:#eff6ff!important;color:#0f172a!important}
div[data-baseweb="select"] span{color:#0f172a!important;font-size:.72rem!important;font-weight:800!important}
</style>
""", unsafe_allow_html=True)

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


def _biblioteca_quick_actions_compacta(row):
    actual = biblioteca_page._safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = biblioteca_page._safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    total_txt = publicados if publicados > 0 else "?"
    titulo = row.get("titulo") or "esta obra"
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="lib-action-contrast-title">Acciones <span class="lib-action-contrast-pill">{actual}/{total_txt}</span></div>
            <div class="lib-action-contrast-sub">{titulo[:48]} · solo esta obra</div>
            """,
            unsafe_allow_html=True,
        )
        q1, q2, q3, q4, q5, q6 = st.columns([0.42, 0.65, 0.42, 0.62, 1.55, 0.70])
        if q1.button("❤️", key=f"lib_fav_{row['id']}", help="Favorito", use_container_width=True):
            db.update_obra(row["id"], {"favorito": 0 if biblioteca_page._safe_int(row.get("favorito"), 0) else 1})
            st.rerun()
        cantidad = q2.number_input("Caps", min_value=0, value=1, step=1, key=f"lib_sum_qty_{row['id']}", label_visibility="collapsed")
        if q3.button("+", key=f"lib_sum_btn_{row['id']}", help="Sumar capítulos vistos", use_container_width=True):
            if int(cantidad or 0) <= 0:
                st.warning("Coloca un número mayor a 0 para sumar avance.")
            else:
                nuevo = actual + int(cantidad)
                if publicados > 0:
                    nuevo = min(nuevo, publicados)
                db.update_obra(row["id"], {
                    "capitulos_vistos": nuevo,
                    "capitulo_actual": nuevo,
                    "ultimo_capitulo_visto": nuevo,
                    "fecha_ultimo_capitulo_visto": str(date.today()),
                })
                st.rerun()
        if q4.button("Día", key=f"lib_done_{row['id']}", help="Poner avance al último capítulo publicado", use_container_width=True):
            db.update_obra(row["id"], {"capitulos_vistos": publicados, "capitulo_actual": publicados, "ultimo_capitulo_visto": publicados, "fecha_ultimo_capitulo_visto": str(date.today())})
            st.rerun()
        estado_col, save_col = q5.columns([0.76, 0.24])
        estado = estado_col.selectbox("Estado", biblioteca_page.ESTADOS, index=biblioteca_page.ESTADOS.index(row.get("estado_lectura")) if row.get("estado_lectura") in biblioteca_page.ESTADOS else 0, key=f"lib_estado_{row['id']}", label_visibility="collapsed")
        if save_col.button("💾", key=f"lib_save_estado_{row['id']}", help="Guardar estado", use_container_width=True):
            db.update_obra(row["id"], {"estado_lectura": estado})
            st.rerun()
        if q6.button("Gráfica", key=f"lib_graph_{row['id']}", help="Ver evolución por capítulos", use_container_width=True):
            if str(st.session_state.get("biblioteca_graph_id")) == str(row.get("id")):
                st.session_state.pop("biblioteca_graph_id", None)
            else:
                st.session_state["biblioteca_graph_id"] = row.get("id")
            st.rerun()


biblioteca_page._quick_actions = _biblioteca_quick_actions_compacta
render_biblioteca = biblioteca_page.render_biblioteca


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
