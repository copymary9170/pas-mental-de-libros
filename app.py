import html
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import init_db, add_obra, update_obra, delete_obra, list_obras, get_obra, add_capitulo, list_capitulos
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

obras = list_obras(); df = pd.DataFrame(obras)
st.markdown("""<div class="app-hero"><div><div class="hero-label">Bookmory + TV Time personal</div><h1>Paz Mental</h1><p>Biblioteca de libros, fanfics, manga, manhwa, webnovels, kdramas, series, anime y peliculas.</p></div></div>""", unsafe_allow_html=True)
tab_search, tab_link, tab_roulette, tab_books, tab_tv, tab_add, tab_chapters, tab_stats, tab_export = st.tabs(["🔎 Buscar e importar", "🔗 Importar link", "🎲 Ruleta", "📚 Biblioteca", "📺 Series y pelis", "➕ Agregar manual", "📝 Capitulos", "📊 Stats", "⬇️ Exportar"])

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
        col1, col2, col3 = st.columns(3)
        with col1:
            tipos_ruleta = st.multiselect("Filtrar por tipo", TIPOS, default=[])
            estados_ruleta = st.multiselect("Filtrar por estado", [e for e in ESTADOS if e not in ["Terminado", "Abandonado"]], default=[])
        with col2:
            etiqueta = st.text_input("Genero / etiqueta contiene", placeholder="romance, accion, kakao, kdrama...")
            solo_con_faltantes = st.checkbox("Solo con capitulos/episodios faltantes", value=True)
        with col3:
            max_faltan = st.number_input("Maximo de capitulos/episodios faltantes (0 = sin limite)", min_value=0, value=0, step=1)
            minimo_nota = st.slider("Nota minima", 0.0, 10.0, 0.0, 0.5)
        ruleta = pendientes.copy()
        if tipos_ruleta: ruleta = ruleta[ruleta["tipo"].isin(tipos_ruleta)]
        if estados_ruleta: ruleta = ruleta[ruleta["estado_lectura"].isin(estados_ruleta)]
        if etiqueta.strip(): ruleta = ruleta[ruleta["etiquetas"].fillna("").str.contains(etiqueta.strip(), case=False)]
        if solo_con_faltantes: ruleta = ruleta[(ruleta["faltan"] > 0) | (ruleta["capitulo_total"] == 0)]
        if max_faltan > 0: ruleta = ruleta[(ruleta["faltan"] <= max_faltan) | (ruleta["capitulo_total"] == 0)]
        ruleta["clasificacion"] = pd.to_numeric(ruleta["clasificacion"], errors="coerce").fillna(0); ruleta = ruleta[ruleta["clasificacion"] >= minimo_nota]
        st.caption(f"Opciones en la ruleta: {len(ruleta)}")
        if st.button("🎲 Girar ruleta", type="primary"):
            if ruleta.empty: st.warning("No hay obras que coincidan con esos filtros.")
            else: st.session_state["ruleta_choice"] = ruleta.sample(1).iloc[0].to_dict()
        elegido = st.session_state.get("ruleta_choice")
        if elegido:
            st.markdown("### Resultado")
            col_img, col_info = st.columns([1, 3])
            with col_img:
                if elegido.get("portada_path") and str(elegido.get("portada_path")).startswith("http"): st.image(elegido.get("portada_path"), use_container_width=True)
                else: st.write("📚 Sin portada")
            with col_info:
                st.markdown(f"## {elegido.get('titulo')}"); st.write(f"**Tipo:** {elegido.get('tipo')}  |  **Estado:** {elegido.get('estado_lectura')}"); st.write(f"**Progreso:** {elegido.get('capitulo_actual',0)} / {elegido.get('capitulo_total',0)} · **Faltan:** {faltan(elegido)}"); st.write(f"**Etiquetas:** {elegido.get('etiquetas') or 'Sin etiquetas'}")
                if elegido.get("sinopsis"): st.write(elegido.get("sinopsis"))
        if not ruleta.empty: st.dataframe(ruleta[["titulo","tipo","estado_lectura","capitulo_actual","capitulo_total","faltan","etiquetas"]], use_container_width=True)

with tab_books:
    books = df[df["tipo"].isin(BOOK_TYPES)].copy() if not df.empty else pd.DataFrame(); st.markdown('<div class="section-title">Mi estanteria</div>', unsafe_allow_html=True)
    if books.empty: st.info("Aun no tienes libros, fanfics, manga, manhwa o webnovels registrados.")
    else:
        c1,c2,c3,c4=st.columns(4); c1.metric("Lecturas",len(books)); c2.metric("Terminadas",int((books["estado_lectura"]=="Terminado").sum())); c3.metric("Leyendo",int(books["estado_lectura"].isin(["Leyendo","Releyendo"]).sum())); c4.metric("Favoritas",int(books["favorito"].fillna(0).astype(int).sum()))
        q=st.text_input("Buscar en biblioteca",key="book_search")
        if q:
            text=books[["titulo","autor","etiquetas"]].fillna("").agg(" ".join,axis=1); books=books[text.str.contains(q,case=False)]
        st.markdown('<div class="bookmory-grid">'+''.join(book_card(row) for _,row in books.iterrows())+'</div>',unsafe_allow_html=True)

with tab_tv:
    tv=df[df["tipo"].isin(TV_TYPES)].copy() if not df.empty else pd.DataFrame(); st.markdown('<div class="section-title">Ahora viendo</div>',unsafe_allow_html=True)
    if tv.empty: st.info("Aun no tienes series, anime, kdramas o peliculas registradas.")
    else:
        c1,c2,c3,c4=st.columns(4); c1.metric("Pantalla",len(tv)); c2.metric("Viendo",int(tv["estado_lectura"].isin(["Viendo","Rewatch"]).sum())); c3.metric("Terminadas",int((tv["estado_lectura"]=="Terminado").sum())); c4.metric("Favoritas",int(tv["favorito"].fillna(0).astype(int).sum()))
        q=st.text_input("Buscar series, anime, kdramas o peliculas",key="tv_search")
        if q:
            text=tv[["titulo","autor","etiquetas"]].fillna("").agg(" ".join,axis=1); tv=tv[text.str.contains(q,case=False)]
        st.markdown('<div class="tv-list">'+''.join(tv_card(row) for _,row in tv.iterrows())+'</div>',unsafe_allow_html=True)

with tab_add:
    st.subheader("Agregar obra manualmente"); modo=st.radio("Tipo de registro",["Libro / fanfic / manga / webnovel","Serie / anime / kdrama / pelicula"],horizontal=True)
    with st.form("obra_form"):
        col1,col2=st.columns(2)
        with col1: titulo=st.text_input("Titulo *"); autor=st.text_input("Autor / creador / estudio"); tipo=st.selectbox("Tipo",BOOK_TYPES if modo.startswith("Libro") else TV_TYPES); clasificacion=st.slider("Nota",0.0,10.0,0.0,0.5); estado=st.selectbox("Estado",ESTADOS); estado_pub=st.selectbox("Estado de publicacion",ESTADOS_PUBLICACION)
        with col2: temporada_actual=st.number_input("Temporada actual",min_value=1,value=1,step=1,disabled=modo.startswith("Libro")); temporada_total=st.number_input("Temporadas totales",min_value=1,value=1,step=1,disabled=modo.startswith("Libro")); capitulo_actual=st.number_input("Capitulo / episodio actual",min_value=0,step=1); capitulo_total=st.number_input("Capitulos / episodios totales",min_value=0,step=1); etiquetas=st.text_input("Etiquetas"); favorito=st.checkbox("Favorito")
        sinopsis=st.text_area("Sinopsis"); opinion=st.text_area("Opinion corta"); link_original=st.text_input("Link original"); portada_url=st.text_input("URL de portada"); buscar_portada=st.checkbox("Buscar portada automaticamente en OpenLibrary",value=False,disabled=not modo.startswith("Libro")); portada=st.file_uploader("Subir portada",type=["jpg","jpeg","png","webp"]); respaldo=st.file_uploader("Respaldo general",type=["pdf","epub","txt","docx","zip"])
        if st.form_submit_button("Guardar"):
            if not titulo.strip(): st.error("El titulo es obligatorio")
            else:
                portada_path=save_uploaded_file(portada,PORTADAS_DIR)
                if not portada_path and portada_url.strip(): portada_path=portada_url.strip()
                if not portada_path and buscar_portada: portada_path=buscar_portada_openlibrary(titulo.strip(),autor.strip())
                add_obra({"titulo":titulo.strip(),"autor":autor.strip(),"tipo":tipo,"clasificacion":clasificacion,"estado_lectura":estado,"estado_publicacion":estado_pub,"temporada_actual":int(temporada_actual),"temporada_total":int(temporada_total),"capitulo_actual":int(capitulo_actual),"capitulo_total":int(capitulo_total),"sinopsis":sinopsis,"etiquetas":parse_tags(etiquetas),"link_original":link_original,"link_respaldo":"","portada_path":portada_path,"respaldo_path":save_uploaded_file(respaldo,RESPALDOS_DIR),"motivo_estado":opinion,"favorito":1 if favorito else 0,"fecha_inicio":str(date.today()),"fecha_fin":None}); st.success("Guardado. Recarga la app para verlo en su seccion.")

with tab_chapters:
    st.subheader("Capitulos, episodios y respaldo")
    if not obras: st.info("Primero agrega una obra.")
    else:
        choices={f"{o['id']} - {o['titulo']} ({o.get('tipo')})":o["id"] for o in obras}; selected=st.selectbox("Obra",list(choices.keys())); obra_id=choices[selected]; obra=get_obra(obra_id); is_tv=obra.get("tipo") in TV_TYPES
        with st.form("chapter_form"):
            col1,col2,col3=st.columns(3)
            with col1: temporada=st.number_input("Temporada",min_value=1,value=int(obra.get("temporada_actual") or 1),step=1,disabled=not is_tv)
            with col2: numero=st.number_input("Numero de capitulo / episodio",min_value=0,step=1)
            with col3: rating=st.slider("Nota",0.0,10.0,0.0,0.5)
            titulo_cap=st.text_input("Titulo del capitulo / episodio"); resumen=st.text_area("Resumen"); texto_completo=st.text_area("Texto completo / respaldo del capitulo",height=240,disabled=is_tv); notas=st.text_area("Opinion, teorias, escenas favoritas"); archivo=st.file_uploader("Archivo de respaldo del capitulo",type=["txt","pdf","docx","epub","zip"])
            if st.form_submit_button("Guardar capitulo / episodio"):
                archivo_path=save_uploaded_file(archivo,RESPALDOS_DIR); add_capitulo({"obra_id":obra_id,"temporada":int(temporada),"numero":int(numero),"titulo":titulo_cap,"sinopsis":resumen,"notas":notas,"texto_completo":texto_completo,"archivo_path":archivo_path,"rating":float(rating),"visto_leido":1,"fecha_lectura":str(date.today())}); update_obra(obra_id,{"temporada_actual":int(temporada),"capitulo_actual":int(numero)}); st.success("Guardado.")
        caps=list_capitulos(obra_id)
        if caps:
            for cap in caps:
                label=f"T{cap.get('temporada') or 1} · E{cap.get('numero')}" if is_tv else f"Capitulo {cap.get('numero')}"
                with st.expander(f"{label} - {cap.get('titulo') or 'Sin titulo'} · {cap.get('rating') or 0}/10"):
                    st.write(cap.get("sinopsis") or "Sin resumen")
                    if cap.get("notas"): st.info(cap.get("notas"))
                    if cap.get("texto_completo"): st.text_area("Texto respaldado",value=cap.get("texto_completo"),height=220,disabled=True)

with tab_stats:
    st.subheader("Estadisticas")
    if df.empty: st.info("Agrega obras para ver estadisticas.")
    else:
        stats=df.copy(); stats["clasificacion"]=pd.to_numeric(stats["clasificacion"],errors="coerce").fillna(0); col1,col2=st.columns(2)
        with col1: st.plotly_chart(px.bar(stats.groupby("tipo").size().reset_index(name="cantidad"),x="tipo",y="cantidad",title="Por tipo"),use_container_width=True)
        with col2: st.plotly_chart(px.pie(stats.groupby("estado_lectura").size().reset_index(name="cantidad"),names="estado_lectura",values="cantidad",title="Estados"),use_container_width=True)
        st.dataframe(stats.sort_values("clasificacion",ascending=False)[["titulo","tipo","estado_lectura","clasificacion","capitulo_actual","capitulo_total"]],use_container_width=True)
with tab_export:
    st.subheader("Exportar biblioteca")
    if df.empty: st.info("No hay datos.")
    else: st.download_button("Descargar CSV",df.to_csv(index=False).encode("utf-8"),"paz-mental.csv","text/csv"); st.dataframe(df,use_container_width=True)
