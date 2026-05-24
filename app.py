import html
from datetime import date, timedelta, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import init_db, add_obra, update_obra, delete_obra, list_obras, get_obra, add_capitulo, list_capitulos, list_actividad, add_actividad
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

st.set_page_config(page_title="Paz Mental", page_icon="📚", layout="wide")
apply_styles(); ensure_dirs(); init_db()
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
TIPOS = BOOK_TYPES + TV_TYPES
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]

def esc(value): return html.escape(str(value or ""))
def pct(row):
    actual = int(row.get("capitulo_actual") or 0); total = int(row.get("capitulo_total") or 0)
    return 0 if total <= 0 else min(100, round(actual / total * 100))
def faltan(row):
    actual = int(row.get("capitulo_actual") or 0); total = int(row.get("capitulo_total") or 0)
    return max(total - actual, 0) if total > 0 else 0
def cover_src(path): return esc(path) if path and str(path).startswith("http") else ""
def book_card(row):
    cover = cover_src(row.get("portada_path")); cover_html = f'<img src="{cover}" />' if cover else '<div class="book-empty">📖</div>'; progress = pct(row)
    return f"""<div class="bookmory-card"><div class="bookmory-cover">{cover_html}</div><div class="bookmory-title">{esc(row.get('titulo'))}</div><div class="bookmory-author">{esc(row.get('autor') or 'Autor no indicado')}</div><div class="bookmory-meta"><span>{esc(row.get('estado_lectura'))}</span><span>{esc(row.get('clasificacion'))}/10</span></div><div class="bookmory-progress"><div style="width:{progress}%"></div></div><div class="bookmory-small">Cap. {esc(row.get('capitulo_actual',0))}/{esc(row.get('capitulo_total',0))}</div></div>"""
def tv_card(row):
    cover = cover_src(row.get("portada_path")); cover_html = f'<img src="{cover}" />' if cover else '<div class="tv-empty">🎬</div>'; progress = pct(row)
    return f"""<div class="tv-card"><div class="tv-poster">{cover_html}</div><div class="tv-info"><div class="tv-title">{esc(row.get('titulo'))}</div><div class="tv-sub">T{esc(row.get('temporada_actual') or 1)} · E{esc(row.get('capitulo_actual') or 0)} de {esc(row.get('capitulo_total') or 0)}</div><div class="tv-pills"><span>{esc(row.get('tipo'))}</span><span>{esc(row.get('estado_lectura'))}</span><span>{esc(row.get('clasificacion'))}/10</span></div><div class="tv-progress"><div style="width:{progress}%"></div></div><div class="tv-note">{esc(row.get('motivo_estado') or row.get('sinopsis') or 'Sin opinion todavia')}</div></div></div>"""
def guardar_importado(item, tipo, estado):
    add_obra({"titulo": item.get("titulo", "Sin titulo"), "autor": item.get("autor", ""), "tipo": tipo, "clasificacion": 0, "estado_lectura": estado, "estado_publicacion": item.get("estado_publicacion", "No aplica"), "temporada_actual": 1, "temporada_total": int(item.get("temporada_total") or 1), "capitulo_actual": 0, "capitulo_total": int(item.get("capitulo_total") or 0), "sinopsis": item.get("sinopsis", ""), "etiquetas": item.get("etiquetas", "importado"), "link_original": item.get("link_original", ""), "link_respaldo": "", "portada_path": item.get("portada_path", ""), "respaldo_path": "", "motivo_estado": f"Importado. Año: {item.get('anio') or 'N/D'}", "favorito": 0, "fecha_inicio": str(date.today()), "fecha_fin": None})

def elapsed_minutes():
    total = st.session_state.get("timer_elapsed", 0)
    if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
        total += (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
    return max(0, int(total // 60))

obras = list_obras(); df = pd.DataFrame(obras)
st.markdown("""<div class="app-hero"><div><div class="hero-label">Bookmory + TV Time personal</div><h1>Paz Mental</h1><p>Biblioteca de libros, fanfics, manga, manhwa, webnovels, kdramas, series, anime y peliculas.</p></div></div>""", unsafe_allow_html=True)
tab_timer, tab_search, tab_link, tab_roulette, tab_calendar, tab_wrapped, tab_books, tab_tv, tab_add, tab_chapters, tab_stats, tab_export = st.tabs(["⏱️ Cronómetro", "🔎 Buscar e importar", "🔗 Importar link", "🎲 Ruleta", "📅 Calendario", "🏆 Wrapped", "📚 Biblioteca", "📺 Series y pelis", "➕ Agregar manual", "📝 Capitulos", "📊 Stats", "⬇️ Exportar"])

with tab_timer:
    st.subheader("Cronómetro de lectura")
    if not obras:
        st.info("Agrega una obra primero para usar el cronómetro.")
    else:
        lecturas = [o for o in obras if o.get("tipo") in BOOK_TYPES]
        if not lecturas: lecturas = obras
        choices = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o["id"] for o in lecturas}
        selected_timer = st.selectbox("Obra para cronometrar", list(choices.keys()), key="timer_obra")
        obra_id_timer = choices[selected_timer]
        col_a, col_b, col_c = st.columns(3)
        with col_a: cap_actual_timer = st.number_input("Capitulo actual opcional", min_value=0, value=0, step=1, key="timer_cap")
        with col_b: mood_timer = st.text_input("Mood", placeholder="cozy, intenso, lloré, fangirl...", key="timer_mood")
        with col_c: fecha_timer = st.date_input("Fecha", value=date.today(), key="timer_fecha")
        comentario_timer = st.text_area("Comentario de la sesión", placeholder="Qué leíste, cómo te sentiste, teoría, etc.", key="timer_comment")
        minutos = elapsed_minutes()
        st.metric("Tiempo acumulado", f"{minutos} min")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("▶️ Iniciar / continuar"):
                if not st.session_state.get("timer_running"):
                    st.session_state["timer_running"] = True; st.session_state["timer_started_at"] = datetime.now()
                st.rerun()
        with c2:
            if st.button("⏸️ Pausar"):
                if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                    st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed", 0) + (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
                st.session_state["timer_running"] = False; st.session_state["timer_started_at"] = None
                st.rerun()
        with c3:
            if st.button("💾 Guardar sesión"):
                if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                    st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed", 0) + (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
                final_min = max(1, int(st.session_state.get("timer_elapsed", 0) // 60))
                add_actividad({"obra_id": obra_id_timer, "capitulo_id": None, "fecha": str(fecha_timer), "tipo_actividad": "lectura cronometrada", "cantidad": 0, "minutos": final_min, "mood": mood_timer, "comentario": comentario_timer, "premio": "sesion de lectura"})
                if cap_actual_timer > 0: update_obra(obra_id_timer, {"capitulo_actual": int(cap_actual_timer), "estado_lectura": "Leyendo"})
                st.session_state["timer_elapsed"] = 0; st.session_state["timer_running"] = False; st.session_state["timer_started_at"] = None
                st.success(f"Sesión guardada: {final_min} minutos.")
        with c4:
            if st.button("🔄 Reiniciar"):
                st.session_state["timer_elapsed"] = 0; st.session_state["timer_running"] = False; st.session_state["timer_started_at"] = None
                st.rerun()
        st.caption("Tip: puedes iniciar, pausar, continuar y guardar. Al guardar, el tiempo entra al Calendario y al Wrapped.")

with tab_search:
    st.subheader("Buscar en bases de datos externas")
    fuente = st.radio("Que quieres buscar?", ["Libros", "Manga / manhwa / novelas ligeras", "Webnovels", "Series / anime / TV", "Kdramas", "Peliculas"], horizontal=True)
    query = st.text_input("Nombre de la obra", key="external_query"); estado_import = st.selectbox("Estado al importar", ESTADOS, index=0)
    if not TMDB_API_KEY and fuente in ["Peliculas", "Series / anime / TV", "Kdramas"]: st.info("Para mejores resultados agrega TMDB_API_KEY en Streamlit Secrets. Sin clave se usa busqueda secundaria.")
    buscar = st.button("Buscar")
    if buscar and query.strip():
        if fuente == "Libros": st.session_state["external_results"] = buscar_libros_openlibrary(query.strip()); st.session_state["external_kind"] = "book"
        elif fuente == "Manga / manhwa / novelas ligeras": st.session_state["external_results"] = buscar_manga_jikan(query.strip()); st.session_state["external_kind"] = "manga"
        elif fuente == "Webnovels": st.session_state["external_results"] = buscar_webnovel_openlibrary(query.strip()); st.session_state["external_kind"] = "webnovel"
        elif fuente == "Peliculas":
            resultados = buscar_peliculas_tmdb(query.strip(), TMDB_API_KEY) if TMDB_API_KEY else []
            if not resultados: resultados = buscar_peliculas_itunes(query.strip())
            st.session_state["external_results"] = resultados; st.session_state["external_kind"] = "movie"
        elif fuente == "Kdramas":
            resultados = buscar_kdramas_tmdb(query.strip(), TMDB_API_KEY) if TMDB_API_KEY else []
            if not resultados: resultados = buscar_series_tvmaze(query.strip())
            st.session_state["external_results"] = resultados; st.session_state["external_kind"] = "kdrama"
        else:
            resultados = buscar_series_tmdb(query.strip(), TMDB_API_KEY) if TMDB_API_KEY else []
            if not resultados: resultados = buscar_series_tvmaze(query.strip())
            st.session_state["external_results"] = resultados; st.session_state["external_kind"] = "tv"
    results = st.session_state.get("external_results", []); kind = st.session_state.get("external_kind")
    if results:
        st.write(f"Resultados encontrados: {len(results)}")
        for i, item in enumerate(results):
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if item.get("portada_path"): st.image(item.get("portada_path"), use_container_width=True)
                else: st.write("Sin portada")
            with col2:
                st.markdown(f"### {item.get('titulo')}"); st.write(item.get("autor") or "Autor / canal no indicado"); st.caption(f"Año: {item.get('anio') or 'N/D'} · Tags: {item.get('etiquetas') or ''}")
                if item.get("sinopsis"): st.write(item.get("sinopsis")[:500])
            with col3:
                if kind == "book": opciones = BOOK_TYPES
                elif kind == "manga": opciones = ["Manga", "Manhwa", "Manhua", "Novela ligera", "Comic"]
                elif kind == "webnovel": opciones = ["Webnovel", "Novela", "Novela ligera", "Fanfiction"]
                elif kind == "movie": opciones = ["Pelicula", "Documental", "Otro"]
                elif kind == "kdrama": opciones = ["Kdrama", "Serie"]
                else: opciones = TV_TYPES
                tipo_final = st.selectbox("Tipo", opciones, key=f"tipo_import_{i}")
                if st.button("Importar", key=f"import_{i}"): guardar_importado(item, tipo_final, estado_import); st.success(f"Importado: {item.get('titulo')}")
            st.divider()
    elif buscar and query.strip(): st.warning("No encontre resultados. Puedes agregarlo manualmente o pegar un link en la pestaña Importar link.")

with tab_link:
    st.subheader("Importar desde link")
    st.caption("Pega enlaces de KakaoPage, Naver, Munpia, Ridi, NovelUpdates, Webnovel o cualquier pagina. Puedes pegar una URL de portada o subir una imagen manualmente.")
    url = st.text_input("Link de la obra", placeholder="https://page.kakao.com/...", key="link_import_url")
    col_a, col_b = st.columns(2)
    with col_a:
        titulo_manual = st.text_input("Titulo manual opcional", placeholder="0살부터 슈퍼스타")
        autor_manual = st.text_input("Autor/plataforma opcional")
        tipo_link = st.selectbox("Tipo", ["Webnovel", "Novela ligera", "Manhwa", "Manga", "Manhua", "Fanfiction", "Libro"])
    with col_b:
        estado_link = st.selectbox("Estado", ESTADOS, index=0, key="estado_link")
        portada_link = st.text_input("URL de portada opcional")
        portada_archivo = st.file_uploader("Subir portada desde tu dispositivo", type=["jpg", "jpeg", "png", "webp"], key="portada_link_upload")
        tags_extra = st.text_input("Etiquetas extra", placeholder="kakao, coreana, romance, fantasía")
    sinopsis_link = st.text_area("Sinopsis / notas opcionales")
    if st.button("Importar link"):
        if not url.strip(): st.error("Pega un link primero.")
        else:
            item = importar_desde_link(url.strip())
            if titulo_manual.strip(): item["titulo"] = titulo_manual.strip()
            if autor_manual.strip(): item["autor"] = autor_manual.strip()
            portada_subida = save_uploaded_file(portada_archivo, PORTADAS_DIR)
            if portada_subida: item["portada_path"] = portada_subida
            elif portada_link.strip(): item["portada_path"] = portada_link.strip()
            if sinopsis_link.strip(): item["sinopsis"] = sinopsis_link.strip() + "\n\nLink original: " + url.strip()
            if tags_extra.strip(): item["etiquetas"] = item.get("etiquetas", "") + ", " + parse_tags(tags_extra)
            guardar_importado(item, tipo_link, estado_link); st.success("Link importado con portada. Revisa la Biblioteca.")

with tab_roulette:
    st.subheader("Ruleta anti-aburrimiento")
    if df.empty: st.info("Agrega obras primero para usar la ruleta.")
    else:
        base = df.copy(); base["capitulo_actual"] = pd.to_numeric(base["capitulo_actual"], errors="coerce").fillna(0).astype(int); base["capitulo_total"] = pd.to_numeric(base["capitulo_total"], errors="coerce").fillna(0).astype(int); base["faltan"] = (base["capitulo_total"] - base["capitulo_actual"]).clip(lower=0)
        pendientes = base[~base["estado_lectura"].isin(["Terminado", "Abandonado"])]
        st.write("Opciones de ruleta disponibles:", len(pendientes))
        if st.button("🎲 Girar ruleta", type="primary") and not pendientes.empty:
            st.session_state["ruleta_choice"] = pendientes.sample(1).iloc[0].to_dict()
        elegido = st.session_state.get("ruleta_choice")
        if elegido: st.success(f"Hoy toca: {elegido.get('titulo')} ({elegido.get('tipo')})")

with tab_calendar:
    st.subheader("Calendario de actividad")
    actividad = pd.DataFrame(list_actividad())
    if actividad.empty: st.info("Todavia no hay actividad. Cuando guardes capítulos o sesiones aparecerán aquí.")
    else:
        actividad["fecha"] = pd.to_datetime(actividad["fecha"], errors="coerce")
        col1, col2 = st.columns(2)
        with col1: inicio = st.date_input("Desde", value=date.today() - timedelta(days=30), key="cal_inicio")
        with col2: fin = st.date_input("Hasta", value=date.today(), key="cal_fin")
        act = actividad[(actividad["fecha"].dt.date >= inicio) & (actividad["fecha"].dt.date <= fin)].copy()
        if act.empty: st.warning("No hay actividad en ese rango.")
        else:
            por_dia = act.groupby(act["fecha"].dt.date).agg(cantidad=("cantidad","sum"), minutos=("minutos","sum")).reset_index().rename(columns={"fecha":"dia"})
            st.plotly_chart(px.bar(por_dia, x="dia", y=["cantidad","minutos"], title="Actividad por día"), use_container_width=True)
            st.dataframe(act[["fecha","titulo","tipo","tipo_actividad","cantidad","minutos","mood","comentario"]], use_container_width=True)

with tab_wrapped:
    st.subheader("Wrapped de lectura y pantalla")
    periodo = st.radio("Periodo", ["Semanal", "Mensual", "Anual"], horizontal=True)
    hoy = date.today(); inicio = hoy - timedelta(days=7) if periodo == "Semanal" else (hoy.replace(day=1) if periodo == "Mensual" else hoy.replace(month=1, day=1))
    actividad = pd.DataFrame(list_actividad(str(inicio), str(hoy)))
    if actividad.empty: st.info("Aun no hay actividad suficiente para crear un Wrapped.")
    else:
        actividad["cantidad"] = pd.to_numeric(actividad["cantidad"], errors="coerce").fillna(0); actividad["minutos"] = pd.to_numeric(actividad["minutos"], errors="coerce").fillna(0)
        c1,c2,c3,c4=st.columns(4); c1.metric("Caps/eps", int(actividad["cantidad"].sum())); c2.metric("Minutos", int(actividad["minutos"].sum())); c3.metric("Días activos", actividad["fecha"].nunique()); c4.metric("Obra reina", actividad.groupby("titulo")["cantidad"].sum().sort_values(ascending=False).index[0])
        st.plotly_chart(px.pie(actividad.groupby("tipo")["cantidad"].sum().reset_index(), names="tipo", values="cantidad", title="Distribución por categoría"), use_container_width=True)

for tab_name in []:
    pass

with tab_books:
    books = df[df["tipo"].isin(BOOK_TYPES)].copy() if not df.empty else pd.DataFrame(); st.markdown('<div class="section-title">Mi estanteria</div>', unsafe_allow_html=True)
    if books.empty: st.info("Aun no tienes libros, fanfics, manga, manhwa o webnovels registrados.")
    else: st.markdown('<div class="bookmory-grid">'+''.join(book_card(row) for _,row in books.iterrows())+'</div>',unsafe_allow_html=True)
with tab_tv:
    tv=df[df["tipo"].isin(TV_TYPES)].copy() if not df.empty else pd.DataFrame(); st.markdown('<div class="section-title">Ahora viendo</div>',unsafe_allow_html=True)
    if tv.empty: st.info("Aun no tienes series, anime, kdramas o peliculas registradas.")
    else: st.markdown('<div class="tv-list">'+''.join(tv_card(row) for _,row in tv.iterrows())+'</div>',unsafe_allow_html=True)
with tab_add:
    st.subheader("Agregar obra manualmente")
    st.info("Usa Buscar, Importar link o la versión manual existente.")
with tab_chapters:
    st.subheader("Capitulos, episodios y respaldo")
    st.info("Guarda capítulos desde la versión actual; el cronómetro ya guarda sesiones de lectura.")
with tab_stats:
    st.subheader("Estadisticas")
    if df.empty: st.info("Agrega obras para ver estadisticas.")
    else: st.plotly_chart(px.bar(df.groupby("tipo").size().reset_index(name="cantidad"), x="tipo", y="cantidad", title="Por tipo"), use_container_width=True)
with tab_export:
    st.subheader("Exportar biblioteca")
    if df.empty: st.info("No hay datos.")
    else: st.download_button("Descargar CSV",df.to_csv(index=False).encode("utf-8"),"paz-mental.csv","text/csv"); st.dataframe(df,use_container_width=True)
