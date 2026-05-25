import html
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import src.database as db
from src.utils import save_uploaded_file, parse_tags, PORTADAS_DIR, RESPALDOS_DIR, ensure_dirs, buscar_portada_openlibrary
try:
    from src.utils import buscar_libros_openlibrary, buscar_series_tvmaze, buscar_peliculas_itunes, buscar_peliculas_tmdb, buscar_series_tmdb, buscar_manga_jikan, buscar_webnovel_openlibrary, buscar_kdramas_tmdb, importar_desde_link
except ImportError:
    def buscar_libros_openlibrary(query): return []
    def buscar_series_tvmaze(query): return []
    def buscar_peliculas_itunes(query): return []
    def buscar_peliculas_tmdb(query, api_key=""): return []
    def buscar_series_tmdb(query, api_key=""): return []
    def buscar_manga_jikan(query): return []
    def buscar_webnovel_openlibrary(query): return []
    def buscar_kdramas_tmdb(query, api_key=""): return []
    def importar_desde_link(url): return {"titulo":"Obra importada por link","autor":"link externo","tipo":"Webnovel","anio":"","sinopsis":url,"portada_path":"","capitulo_total":0,"temporada_total":1,"etiquetas":"importado por link, webnovel","estado_publicacion":"No aplica","link_original":url}
from src.styles import apply_styles

init_db = db.init_db
add_obra = db.add_obra
update_obra = db.update_obra
list_obras = db.list_obras
add_actividad = getattr(db, "add_actividad", lambda data: None)
list_actividad = getattr(db, "list_actividad", lambda fecha_inicio=None, fecha_fin=None: [])

st.set_page_config(page_title="Paz Mental", page_icon="📚", layout="wide")
apply_styles(); ensure_dirs(); init_db()
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
TIPOS = BOOK_TYPES + TV_TYPES
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]

def esc(value): return html.escape(str(value or ""))
def fmt_time(minutes):
    minutes = int(minutes or 0); h = minutes // 60; m = minutes % 60
    return f"{h}h {m}m" if h else f"{m}m"
def pct(row):
    actual = int(row.get("capitulo_actual") or row.get("capitulos_vistos") or 0); total = int(row.get("capitulo_total") or row.get("capitulos_publicados") or 0)
    return 0 if total <= 0 else min(100, round(actual / total * 100))
def cover_src(path): return esc(path) if path and str(path).startswith("http") else ""
def book_card(row):
    cover = cover_src(row.get("portada_path")); cover_html = f'<img src="{cover}" />' if cover else '<div class="book-empty">📖</div>'; progress = pct(row)
    return f"""<div class="bookmory-card"><div class="bookmory-cover">{cover_html}</div><div class="bookmory-title">{esc(row.get('titulo'))}</div><div class="bookmory-author">{esc(row.get('autor') or 'Autor no indicado')}</div><div class="bookmory-meta"><span>{esc(row.get('estado_lectura'))}</span><span>{esc(row.get('clasificacion'))}/10</span></div><div class="bookmory-progress"><div style="width:{progress}%"></div></div><div class="bookmory-small">Leído: {esc(row.get('capitulos_vistos') or row.get('capitulo_actual') or 0)} / Publicados: {esc(row.get('capitulos_publicados') or row.get('capitulo_total') or 0)}</div><div class="bookmory-small">Tiempo: {fmt_time(row.get('tiempo_total_minutos'))} · Última: {esc(row.get('fecha_ultima_sesion') or 'N/D')}</div></div>"""
def tv_card(row):
    cover = cover_src(row.get("portada_path")); cover_html = f'<img src="{cover}" />' if cover else '<div class="tv-empty">🎬</div>'; progress = pct(row)
    return f"""<div class="tv-card"><div class="tv-poster">{cover_html}</div><div class="tv-info"><div class="tv-title">{esc(row.get('titulo'))}</div><div class="tv-sub">Visto {esc(row.get('capitulos_vistos') or row.get('capitulo_actual') or 0)} · Emitidos {esc(row.get('capitulos_publicados') or row.get('capitulo_total') or 0)} · Estado {esc(row.get('estado_publicacion') or 'N/D')}</div><div class="tv-pills"><span>{esc(row.get('tipo'))}</span><span>{esc(row.get('estado_lectura'))}</span><span>{fmt_time(row.get('tiempo_total_minutos'))}</span></div><div class="tv-progress"><div style="width:{progress}%"></div></div><div class="tv-note">Último visto: {esc(row.get('ultimo_capitulo_visto') or 0)} · Fecha: {esc(row.get('fecha_ultimo_capitulo_visto') or row.get('fecha_ultima_sesion') or 'N/D')}</div></div></div>"""
def guardar_importado(item, tipo, estado):
    add_obra({"titulo": item.get("titulo", "Sin titulo"), "autor": item.get("autor", ""), "tipo": tipo, "clasificacion": 0, "estado_lectura": estado, "estado_publicacion": item.get("estado_publicacion", "No aplica"), "temporada_actual": 1, "temporada_total": int(item.get("temporada_total") or 1), "capitulo_actual": 0, "capitulo_total": int(item.get("capitulo_total") or 0), "capitulos_publicados": int(item.get("capitulo_total") or 0), "capitulos_vistos": 0, "sinopsis": item.get("sinopsis", ""), "etiquetas": item.get("etiquetas", "importado"), "link_original": item.get("link_original", ""), "link_respaldo": "", "portada_path": item.get("portada_path", ""), "respaldo_path": "", "motivo_estado": f"Importado. Año: {item.get('anio') or 'N/D'}", "favorito": 0, "fecha_inicio": str(date.today()), "fecha_fin": None})

def elapsed_minutes():
    total = st.session_state.get("timer_elapsed", 0)
    if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
        total += (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
    return max(0, int(total // 60))

def buscar_global(query, fuente):
    q = query.strip()
    if fuente == "Libros": return buscar_libros_openlibrary(q), "book"
    if fuente == "Manga / manhwa / novelas ligeras":
        resultados = buscar_manga_jikan(q) or buscar_libros_openlibrary(q)
        return resultados, "manga"
    if fuente == "Webnovels":
        resultados = buscar_webnovel_openlibrary(q) or buscar_manga_jikan(q)
        return resultados, "webnovel"
    if fuente == "Peliculas":
        resultados = buscar_peliculas_tmdb(q, TMDB_API_KEY) if TMDB_API_KEY else []
        resultados = resultados or buscar_peliculas_itunes(q) or buscar_series_tvmaze(q)
        return resultados, "movie"
    if fuente == "Kdramas":
        resultados = buscar_kdramas_tmdb(q, TMDB_API_KEY) if TMDB_API_KEY else []
        resultados = resultados or buscar_series_tvmaze(q)
        return resultados, "kdrama"
    resultados = buscar_series_tmdb(q, TMDB_API_KEY) if TMDB_API_KEY else []
    resultados = resultados or buscar_series_tvmaze(q)
    return resultados, "tv"

obras = list_obras(); df = pd.DataFrame(obras)
st.markdown("""<div class="app-hero"><div><div class="hero-label">Bookmory + TV Time personal</div><h1>Paz Mental</h1><p>Biblioteca de libros, fanfics, manga, manhwa, webnovels, kdramas, series, anime y peliculas.</p></div></div>""", unsafe_allow_html=True)
tab_timer, tab_search, tab_link, tab_roulette, tab_calendar, tab_wrapped, tab_books, tab_tv, tab_add, tab_chapters, tab_stats, tab_export = st.tabs(["⏱️ Cronómetro", "🔎 Buscar e importar", "🔗 Importar link", "🎲 Ruleta", "📅 Calendario", "🏆 Wrapped", "📚 Biblioteca", "📺 Series y pelis", "➕ Agregar manual", "📝 Capitulos", "📊 Stats", "⬇️ Exportar"])

with tab_timer:
    st.subheader("Cronómetro de lectura")
    if not obras: st.info("Agrega una obra primero para usar el cronómetro.")
    else:
        lecturas = [o for o in obras if o.get("tipo") in BOOK_TYPES] or obras
        choices = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o["id"] for o in lecturas}
        selected_timer = st.selectbox("Obra para cronometrar", list(choices.keys()), key="timer_obra")
        obra_id_timer = choices[selected_timer]
        obra_timer = next((o for o in obras if o["id"] == obra_id_timer), {})
        st.caption(f"Tiempo total registrado: {fmt_time(obra_timer.get('tiempo_total_minutos'))} · Última sesión: {fmt_time(obra_timer.get('tiempo_ultima_sesion_minutos'))}")
        col_a, col_b, col_c = st.columns(3)
        with col_a: cap_actual_timer = st.number_input("Capitulo actual opcional", min_value=0, value=0, step=1, key="timer_cap")
        with col_b: mood_timer = st.text_input("Mood", placeholder="cozy, intenso, lloré, fangirl...", key="timer_mood")
        with col_c: fecha_timer = st.date_input("Fecha", value=date.today(), key="timer_fecha")
        comentario_timer = st.text_area("Comentario de la sesión", key="timer_comment")
        minutos = elapsed_minutes(); st.metric("Tiempo acumulado", f"{minutos} min")
        c1,c2,c3,c4=st.columns(4)
        with c1:
            if st.button("▶️ Iniciar / continuar"):
                if not st.session_state.get("timer_running"):
                    st.session_state["timer_running"] = True; st.session_state["timer_started_at"] = datetime.now()
                st.rerun()
        with c2:
            if st.button("⏸️ Pausar"):
                if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                    st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed",0)+(datetime.now()-st.session_state["timer_started_at"]).total_seconds()
                st.session_state["timer_running"] = False; st.session_state["timer_started_at"] = None; st.rerun()
        with c3:
            if st.button("💾 Guardar sesión"):
                if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                    st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed",0)+(datetime.now()-st.session_state["timer_started_at"]).total_seconds()
                final_min = max(1, int(st.session_state.get("timer_elapsed",0)//60))
                add_actividad({"obra_id": obra_id_timer, "capitulo_id": None, "fecha": str(fecha_timer), "tipo_actividad": "lectura cronometrada", "cantidad": 0, "minutos": final_min, "mood": mood_timer, "comentario": comentario_timer, "premio": "sesion de lectura"})
                if cap_actual_timer > 0: update_obra(obra_id_timer, {"capitulo_actual": int(cap_actual_timer), "capitulos_vistos": int(cap_actual_timer), "ultimo_capitulo_visto": int(cap_actual_timer), "fecha_ultimo_capitulo_visto": str(fecha_timer), "estado_lectura": "Leyendo"})
                st.session_state["timer_elapsed"] = 0; st.session_state["timer_running"] = False; st.session_state["timer_started_at"] = None; st.success(f"Sesión guardada: {final_min} minutos.")
        with c4:
            if st.button("🔄 Reiniciar"):
                st.session_state["timer_elapsed"] = 0; st.session_state["timer_running"] = False; st.session_state["timer_started_at"] = None; st.rerun()

with tab_search:
    st.subheader("Buscar en bases de datos externas")
    fuente = st.radio("Que quieres buscar?", ["Libros", "Manga / manhwa / novelas ligeras", "Webnovels", "Series / anime / TV", "Kdramas", "Peliculas"], horizontal=True)
    query = st.text_input("Nombre de la obra", key="external_query")
    estado_import = st.selectbox("Estado al importar", ESTADOS, index=0)
    if fuente in ["Peliculas", "Series / anime / TV", "Kdramas"] and not TMDB_API_KEY:
        st.warning("Para mejores resultados en películas/series agrega TMDB_API_KEY en Streamlit Secrets. Mientras tanto usaré búsquedas alternativas.")
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
                if item.get("portada_path"): st.image(item.get("portada_path"), use_container_width=True)
                else: st.write("Sin portada")
            with col2:
                st.markdown(f"### {item.get('titulo')}")
                st.write(item.get("autor") or "Autor / canal no indicado")
                st.caption(f"Año: {item.get('anio') or 'N/D'} · Tags: {item.get('etiquetas') or ''}")
                if item.get("sinopsis"): st.write(str(item.get("sinopsis"))[:600])
            with col3:
                if kind == "book": opciones = BOOK_TYPES
                elif kind == "manga": opciones = ["Manga", "Manhwa", "Manhua", "Novela ligera", "Comic"]
                elif kind == "webnovel": opciones = ["Webnovel", "Novela", "Novela ligera", "Fanfiction"]
                elif kind == "movie": opciones = ["Pelicula", "Documental", "Otro"]
                elif kind == "kdrama": opciones = ["Kdrama", "Serie"]
                else: opciones = TV_TYPES
                tipo_final = st.selectbox("Tipo", opciones, key=f"tipo_import_{i}")
                if st.button("Importar", key=f"import_{i}"):
                    guardar_importado(item, tipo_final, estado_import); st.success(f"Importado: {item.get('titulo')}")
            st.divider()

with tab_link:
    st.subheader("Importar desde link")
    url = st.text_input("Link de la obra", placeholder="https://page.kakao.com/...", key="link_import_url")
    titulo_manual = st.text_input("Titulo manual opcional", placeholder="0살부터 슈퍼스타")
    tipo_link = st.selectbox("Tipo", ["Webnovel", "Novela ligera", "Manhwa", "Manga", "Manhua", "Fanfiction", "Libro"])
    portada_archivo = st.file_uploader("Subir portada desde tu dispositivo", type=["jpg","jpeg","png","webp"], key="portada_link_upload")
    if st.button("Importar link"):
        if not url.strip(): st.error("Pega un link primero.")
        else:
            item = importar_desde_link(url.strip())
            if titulo_manual.strip(): item["titulo"] = titulo_manual.strip()
            portada_subida = save_uploaded_file(portada_archivo, PORTADAS_DIR)
            if portada_subida: item["portada_path"] = portada_subida
            guardar_importado(item, tipo_link, "Pendiente"); st.success("Link importado.")

with tab_roulette:
    st.subheader("Ruleta anti-aburrimiento")
    if df.empty: st.info("Agrega obras primero.")
    else:
        pendientes = df[~df["estado_lectura"].isin(["Terminado","Abandonado"])]
        if st.button("🎲 Girar ruleta", type="primary") and not pendientes.empty: st.success(f"Hoy toca: {pendientes.sample(1).iloc[0]['titulo']}")

with tab_calendar:
    st.subheader("Calendario de actividad")
    actividad = pd.DataFrame(list_actividad())
    if actividad.empty: st.info("Todavia no hay actividad.")
    else: st.dataframe(actividad, use_container_width=True)

with tab_wrapped:
    st.subheader("Wrapped")
    actividad = pd.DataFrame(list_actividad())
    if actividad.empty: st.info("Aun no hay actividad suficiente.")
    else: st.metric("Minutos totales", int(pd.to_numeric(actividad["minutos"], errors="coerce").fillna(0).sum()))

with tab_books:
    books = df[df["tipo"].isin(BOOK_TYPES)].copy() if not df.empty else pd.DataFrame(); st.markdown('<div class="section-title">Mi estanteria</div>', unsafe_allow_html=True)
    if books.empty: st.info("Aun no tienes libros registrados.")
    else: st.markdown('<div class="bookmory-grid">'+''.join(book_card(row) for _,row in books.iterrows())+'</div>', unsafe_allow_html=True)
with tab_tv:
    tv = df[df["tipo"].isin(TV_TYPES)].copy() if not df.empty else pd.DataFrame(); st.markdown('<div class="section-title">Ahora viendo</div>', unsafe_allow_html=True)
    if tv.empty: st.info("Aun no tienes series o peliculas registradas.")
    else: st.markdown('<div class="tv-list">'+''.join(tv_card(row) for _,row in tv.iterrows())+'</div>', unsafe_allow_html=True)
with tab_add:
    st.subheader("Agregar obra manualmente")
    with st.form("obra_form_manual"):
        titulo=st.text_input("Titulo *"); tipo=st.selectbox("Tipo", TIPOS); estado=st.selectbox("Estado", ESTADOS); estado_pub=st.selectbox("Estado de publicacion", ESTADOS_PUBLICACION)
        capitulo_actual=st.number_input("Capitulos leidos/vistos", min_value=0, step=1); capitulos_publicados=st.number_input("Capitulos publicados/emitidos", min_value=0, step=1); capitulo_total=st.number_input("Capitulos totales esperados", min_value=0, step=1)
        st.markdown("### Modo de respaldo")
        modo_respaldo=st.radio("Como quieres guardar el contenido?", ["Solo registrar la obra", "Subir obra completa", "Subir capitulos uno por uno", "Subir varios capitulos de golpe"])
        respaldo = st.file_uploader("Archivo completo de la obra", type=["pdf","epub","txt","docx","zip"]) if modo_respaldo == "Subir obra completa" else None
        if st.form_submit_button("Guardar obra"):
            if not titulo.strip(): st.error("El titulo es obligatorio")
            else:
                add_obra({"titulo":titulo,"autor":"","tipo":tipo,"clasificacion":0,"estado_lectura":estado,"estado_publicacion":estado_pub,"capitulo_actual":int(capitulo_actual),"capitulos_vistos":int(capitulo_actual),"capitulos_publicados":int(capitulos_publicados),"capitulo_total":int(capitulo_total),"sinopsis":"","etiquetas":"","link_original":"","link_respaldo":"","portada_path":"","respaldo_path":save_uploaded_file(respaldo,RESPALDOS_DIR),"motivo_estado":modo_respaldo,"favorito":0,"fecha_inicio":str(date.today()),"fecha_fin":None}); st.success("Guardado")
with tab_chapters:
    st.subheader("Capitulos, episodios y respaldo")
    st.info("Próximo paso: restaurar formulario avanzado de capítulos.")
with tab_stats:
    st.subheader("Estadisticas")
    if not df.empty: st.plotly_chart(px.bar(df.groupby("tipo").size().reset_index(name="cantidad"), x="tipo", y="cantidad"), use_container_width=True)
with tab_export:
    st.subheader("Exportar biblioteca")
    if not df.empty: st.download_button("Descargar CSV", df.to_csv(index=False).encode("utf-8"), "paz-mental.csv", "text/csv"); st.dataframe(df, use_container_width=True)
