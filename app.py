from datetime import date, datetime

import pandas as pd
import streamlit as st

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
from src.pages.calendario import render_calendario
from src.pages.capitulos import render_capitulos
from src.pages.fanfiction import render_fanfiction_fields, fanfiction_badges

st.set_page_config(page_title="Paz Mental", page_icon="📚", layout="wide")
apply_styles()
ensure_dirs()
db.init_db()

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
TIPOS = BOOK_TYPES + TV_TYPES
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]


def fmt_time(minutes):
    minutes = int(minutes or 0)
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if h else f"{m}m"


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


def guardar_importado(item, tipo, estado):
    db.add_obra({
        "titulo": item.get("titulo", "Sin titulo"),
        "autor": item.get("autor", ""),
        "tipo": tipo,
        "clasificacion": 0,
        "estado_lectura": estado,
        "estado_publicacion": item.get("estado_publicacion", "No aplica"),
        "temporada_actual": 1,
        "temporada_total": int(item.get("temporada_total") or 1),
        "capitulo_actual": 0,
        "capitulo_total": int(item.get("capitulo_total") or 0),
        "capitulos_publicados": int(item.get("capitulo_total") or 0),
        "capitulos_vistos": 0,
        "sinopsis": item.get("sinopsis", ""),
        "etiquetas": item.get("etiquetas", "importado"),
        "link_original": item.get("link_original", ""),
        "link_respaldo": "",
        "portada_path": item.get("portada_path", ""),
        "respaldo_path": "",
        "motivo_estado": f"Importado. Año: {item.get('anio') or 'N/D'}",
        "favorito": 0,
        "fecha_inicio": str(date.today()),
        "fecha_fin": None,
    })


def mini_card(row):
    portada = row.get("portada_path") or ""
    img = f'<img src="{portada}" />' if str(portada).startswith("http") else '<div class="book-empty">📖</div>'
    leidos = row.get("capitulos_vistos") or row.get("capitulo_actual") or 0
    publicados = row.get("capitulos_publicados") or row.get("capitulo_total") or 0
    badges = fanfiction_badges(row)
    sinopsis = (row.get("sinopsis") or "Sin sinopsis todavía.")[:180]
    return f"""
    <div class="bookmory-card">
      <div class="bookmory-cover">{img}</div>
      <div class="bookmory-title">{row.get('titulo','')}</div>
      <div class="bookmory-author">{row.get('autor') or 'Autor no indicado'}</div>
      <div class="bookmory-meta"><span>{row.get('tipo')}</span><span>{row.get('estado_lectura')}</span></div>
      <div class="bookmory-small">{badges}</div>
      <div class="bookmory-small">{sinopsis}</div>
      <div class="bookmory-small">{leidos} / {publicados} caps</div>
      <div class="bookmory-small">Tiempo: {fmt_time(row.get('tiempo_total_minutos'))}</div>
    </div>
    """


def elapsed_minutes():
    total = st.session_state.get("timer_elapsed", 0)
    if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
        total += (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
    return max(0, int(total // 60))


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

tab_timer, tab_search, tab_link, tab_calendar, tab_books, tab_add, tab_chapters, tab_export = st.tabs([
    "⏱️ Cronómetro",
    "🔎 Buscar e importar",
    "🔗 Importar link",
    "📅 Calendario",
    "📚 Biblioteca",
    "➕ Agregar manual",
    "📝 Capitulos",
    "⬇️ Exportar",
])

with tab_timer:
    st.subheader("Cronómetro de lectura")
    if not obras:
        st.info("Agrega una obra primero.")
    else:
        opciones = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o["id"] for o in obras}
        seleccion = st.selectbox("Obra", list(opciones.keys()), key="timer_obra")
        obra_id = opciones[seleccion]
        obra = next((o for o in obras if o["id"] == obra_id), {})
        st.caption(f"Tiempo total: {fmt_time(obra.get('tiempo_total_minutos'))} · Última sesión: {fmt_time(obra.get('tiempo_ultima_sesion_minutos'))}")
        cap_actual = st.number_input("Capítulo actual opcional", min_value=0, value=0, step=1)
        mood = st.text_input("Mood")
        comentario = st.text_area("Comentario de la sesión")
        fecha = st.date_input("Fecha", value=date.today())
        st.metric("Tiempo acumulado", f"{elapsed_minutes()} min")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("▶️ Iniciar / continuar"):
                if not st.session_state.get("timer_running"):
                    st.session_state["timer_running"] = True
                    st.session_state["timer_started_at"] = datetime.now()
                st.rerun()
        with c2:
            if st.button("⏸️ Pausar"):
                if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                    st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed", 0) + (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
                st.session_state["timer_running"] = False
                st.session_state["timer_started_at"] = None
                st.rerun()
        with c3:
            if st.button("💾 Guardar sesión"):
                if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                    st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed", 0) + (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
                final_min = max(1, int(st.session_state.get("timer_elapsed", 0) // 60))
                db.add_actividad({"obra_id": obra_id, "capitulo_id": None, "fecha": str(fecha), "tipo_actividad": "lectura cronometrada", "cantidad": 0, "minutos": final_min, "mood": mood, "comentario": comentario, "premio": "sesion de lectura"})
                if cap_actual > 0:
                    db.update_obra(obra_id, {"capitulo_actual": int(cap_actual), "capitulos_vistos": int(cap_actual), "ultimo_capitulo_visto": int(cap_actual), "fecha_ultimo_capitulo_visto": str(fecha), "estado_lectura": "Leyendo"})
                st.session_state["timer_elapsed"] = 0
                st.session_state["timer_running"] = False
                st.session_state["timer_started_at"] = None
                st.success(f"Sesión guardada: {final_min} minutos.")
        with c4:
            if st.button("🔄 Reiniciar"):
                st.session_state["timer_elapsed"] = 0
                st.session_state["timer_running"] = False
                st.session_state["timer_started_at"] = None
                st.rerun()

with tab_search:
    st.subheader("Buscar en bases externas")
    fuente = st.radio("¿Qué quieres buscar?", ["Libros", "Manga / manhwa / novelas ligeras", "Webnovels", "Series / anime / TV", "Kdramas", "Peliculas"], horizontal=True)
    query = st.text_input("Nombre de la obra")
    estado_import = st.selectbox("Estado al importar", ESTADOS, index=0)
    if st.button("Buscar") and query.strip():
        resultados, kind = buscar_global(query, fuente)
        st.session_state["external_results"] = resultados
        st.session_state["external_kind"] = kind
    results = st.session_state.get("external_results", [])
    kind = st.session_state.get("external_kind")
    if results:
        st.success(f"Resultados encontrados: {len(results)}")
        for i, item in enumerate(results):
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if item.get("portada_path"):
                    st.image(item.get("portada_path"), use_container_width=True)
            with col2:
                st.markdown(f"### {item.get('titulo')}")
                st.write(item.get("autor") or "Autor / canal no indicado")
                if item.get("sinopsis"):
                    st.write(str(item.get("sinopsis"))[:600])
            with col3:
                if kind == "movie":
                    opciones = ["Pelicula", "Documental", "Otro"]
                elif kind == "kdrama":
                    opciones = ["Kdrama", "Serie"]
                elif kind in ["manga", "webnovel"]:
                    opciones = ["Manga", "Manhwa", "Manhua", "Novela ligera", "Webnovel", "Fanfiction"]
                else:
                    opciones = BOOK_TYPES if kind == "book" else TV_TYPES
                tipo_final = st.selectbox("Tipo", opciones, key=f"tipo_import_{i}")
                if st.button("Importar", key=f"import_{i}"):
                    guardar_importado(item, tipo_final, estado_import)
                    st.success("Importado")
            st.divider()

with tab_link:
    st.subheader("Importar desde link")
    url = st.text_input("Link de la obra")
    titulo_manual = st.text_input("Título manual opcional")
    tipo_link = st.selectbox("Tipo", ["Webnovel", "Novela ligera", "Manhwa", "Manga", "Manhua", "Fanfiction", "Libro"])
    sinopsis_link = st.text_area("Sinopsis / descripción")
    portada = st.file_uploader("Subir portada desde tu dispositivo", type=["jpg", "jpeg", "png", "webp"])
    if st.button("Importar link"):
        if not url.strip():
            st.error("Pega un link primero.")
        else:
            item = importar_desde_link(url.strip())
            if titulo_manual.strip():
                item["titulo"] = titulo_manual.strip()
            if sinopsis_link.strip():
                item["sinopsis"] = sinopsis_link.strip()
            portada_subida = save_uploaded_file(portada, PORTADAS_DIR)
            if portada_subida:
                item["portada_path"] = portada_subida
            guardar_importado(item, tipo_link, "Pendiente")
            st.success("Link importado.")

with tab_calendar:
    render_calendario(db.list_actividad)

with tab_books:
    st.subheader("Biblioteca")
    if df.empty:
        st.info("Aún no tienes obras registradas.")
    else:
        st.markdown('<div class="bookmory-grid">' + ''.join(mini_card(row) for _, row in df.iterrows()) + '</div>', unsafe_allow_html=True)

with tab_add:
    st.subheader("Agregar obra manualmente")
    with st.form("obra_form_manual"):
        titulo = st.text_input("Título *")
        autor = st.text_input("Autor / creador / estudio")
        tipo = st.selectbox("Tipo", TIPOS)
        sinopsis = st.text_area("Sinopsis / descripción de la obra", height=160)
        etiquetas = st.text_input("Etiquetas / géneros", placeholder="romance, fantasía, kdrama, comfort...")
        estado = st.selectbox("Estado personal", ESTADOS)
        estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION)
        cap_vistos = st.number_input("Capítulos leídos/vistos", min_value=0, step=1)
        cap_pub = st.number_input("Capítulos publicados/emitidos", min_value=0, step=1)
        cap_total = st.number_input("Capítulos totales esperados", min_value=0, step=1)
        fanfic_data = {}
        if tipo == "Fanfiction":
            fanfic_data = render_fanfiction_fields(prefix="manual")
        portada = st.file_uploader("Subir portada", type=["jpg", "jpeg", "png", "webp"])
        st.markdown("### Modo de respaldo")
        modo_respaldo = st.radio("¿Cómo quieres guardar el contenido?", ["Solo registrar la obra", "Subir obra completa", "Subir capítulos uno por uno", "Subir varios capítulos de golpe"])
        respaldo = st.file_uploader("Archivo completo de la obra", type=["pdf", "epub", "txt", "docx", "zip"]) if modo_respaldo == "Subir obra completa" else None
        if st.form_submit_button("Guardar obra"):
            if not titulo.strip():
                st.error("El título es obligatorio")
            else:
                data = {"titulo": titulo.strip(), "autor": autor.strip(), "tipo": tipo, "clasificacion": 0, "estado_lectura": estado, "estado_publicacion": estado_pub, "capitulo_actual": int(cap_vistos), "capitulos_vistos": int(cap_vistos), "capitulos_publicados": int(cap_pub), "capitulo_total": int(cap_total), "sinopsis": sinopsis.strip(), "etiquetas": etiquetas.strip(), "link_original": "", "link_respaldo": "", "portada_path": save_uploaded_file(portada, PORTADAS_DIR), "respaldo_path": save_uploaded_file(respaldo, RESPALDOS_DIR), "motivo_estado": modo_respaldo, "favorito": 0, "fecha_inicio": str(date.today()), "fecha_fin": None}
                data.update(fanfic_data)
                db.add_obra(data)
                st.success("Obra guardada.")

with tab_chapters:
    render_capitulos(obras, db.list_capitulos, db.get_obra)

with tab_export:
    st.subheader("Exportar biblioteca")
    if df.empty:
        st.info("No hay datos.")
    else:
        st.download_button("Descargar CSV", df.to_csv(index=False).encode("utf-8"), "paz-mental.csv", "text/csv")
        st.dataframe(df, use_container_width=True)
