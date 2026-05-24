import html
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import init_db, add_obra, update_obra, delete_obra, list_obras, get_obra, add_capitulo, list_capitulos
from src.utils import save_uploaded_file, parse_tags, PORTADAS_DIR, RESPALDOS_DIR, ensure_dirs, buscar_portada_openlibrary
from src.styles import apply_styles

st.set_page_config(page_title="Paz Mental", page_icon="📚", layout="wide")
apply_styles()
ensure_dirs()
init_db()

TIPOS = ["Libro", "Fanfiction", "Novela", "Manga", "Manhwa", "Manhua", "Webnovel", "Anime", "Serie", "Pelicula", "Documental", "Comic", "Podcast", "Otro"]
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]


def esc(value):
    return html.escape(str(value or ""))


def cover_html(path):
    if path and str(path).startswith("http"):
        return f'<img class="bm-cover" src="{esc(path)}" />'
    return '<div class="bm-cover bm-cover-empty">📖</div>'


def progress_percent(row):
    actual = int(row.get("capitulo_actual") or 0)
    total = int(row.get("capitulo_total") or 0)
    if total <= 0:
        return 0
    return min(100, round(actual / total * 100))


obras = list_obras()
df = pd.DataFrame(obras)

st.markdown(
    """
    <div class="bm-header">
      <div>
        <div class="bm-kicker">Mi biblioteca personal</div>
        <h1>Paz Mental</h1>
        <p>Un diario cozy para libros, fanfics, anime, series y peliculas.</p>
      </div>
      <div class="bm-header-badge">📚 Book memory mode</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_biblioteca, tab_agregar, tab_capitulos, tab_estadisticas, tab_recomendaciones, tab_exportar = st.tabs([
    "Inicio", "Agregar", "Capitulos", "Estadisticas", "Recomendaciones", "Exportar"
])

with tab_biblioteca:
    with st.sidebar:
        st.header("Filtros")
        q = st.text_input("Buscar")
        tipo_f = st.multiselect("Tipo", TIPOS)
        estado_f = st.multiselect("Estado", ESTADOS)
        fav_f = st.checkbox("Solo favoritos")
        min_rank = st.slider("Nota minima", 0.0, 10.0, 0.0, 0.5)

    filtered = df.copy() if not df.empty else pd.DataFrame()
    if not filtered.empty:
        filtered["clasificacion"] = pd.to_numeric(filtered["clasificacion"], errors="coerce").fillna(0)
        if q:
            text = filtered[["titulo", "autor", "etiquetas", "motivo_estado"]].fillna("").agg(" ".join, axis=1)
            filtered = filtered[text.str.contains(q, case=False)]
        if tipo_f:
            filtered = filtered[filtered["tipo"].isin(tipo_f)]
        if estado_f:
            filtered = filtered[filtered["estado_lectura"].isin(estado_f)]
        if fav_f:
            filtered = filtered[filtered["favorito"].fillna(0).astype(int) == 1]
        filtered = filtered[filtered["clasificacion"] >= min_rank]

    if df.empty:
        st.markdown('<div class="empty-state"><h3>Tu biblioteca esta vacia</h3><p>Agrega tu primera obra para empezar tu diario.</p></div>', unsafe_allow_html=True)
    else:
        stats = df.copy()
        stats["clasificacion"] = pd.to_numeric(stats["clasificacion"], errors="coerce").fillna(0)
        total = len(stats)
        terminadas = int((stats["estado_lectura"] == "Terminado").sum())
        progreso = int(stats["estado_lectura"].isin(["Leyendo", "Viendo", "Releyendo", "Rewatch"]).sum())
        favs = int(stats["favorito"].fillna(0).astype(int).sum())
        promedio = round(float(stats["clasificacion"].mean()), 1) if total else 0
        st.markdown(
            f"""
            <div class="bm-stats">
              <div class="bm-stat"><span>Total</span><strong>{total}</strong></div>
              <div class="bm-stat"><span>En progreso</span><strong>{progreso}</strong></div>
              <div class="bm-stat"><span>Terminadas</span><strong>{terminadas}</strong></div>
              <div class="bm-stat"><span>Favoritos</span><strong>{favs}</strong></div>
              <div class="bm-stat"><span>Promedio</span><strong>{promedio}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if filtered.empty:
            st.info("No hay obras que coincidan con los filtros.")
        else:
            st.markdown('<div class="shelf-title">Continuar / Biblioteca</div>', unsafe_allow_html=True)
            cards = []
            for _, row in filtered.iterrows():
                pct = progress_percent(row)
                fav = "⭐" if int(row.get("favorito") or 0) else ""
                tags = esc(row.get("etiquetas") or "sin etiquetas")
                note = esc(row.get("motivo_estado") or "")
                note_html = f'<div class="bm-note">{note}</div>' if note else ""
                cards.append(
                    f"""
                    <div class="bm-book-card">
                        <div class="bm-cover-wrap">{cover_html(row.get('portada_path'))}<div class="bm-rating">{row.get('clasificacion', 0)}/10</div></div>
                        <div class="bm-book-body">
                            <div class="bm-book-title">{fav} {esc(row.get('titulo', 'Sin titulo'))}</div>
                            <div class="bm-author">{esc(row.get('autor') or 'Autor no indicado')}</div>
                            <div class="bm-pills"><span>{esc(row.get('tipo'))}</span><span>{esc(row.get('estado_lectura'))}</span></div>
                            <div class="bm-progress-label">Progreso {esc(row.get('capitulo_actual', 0))}/{esc(row.get('capitulo_total', 0))}</div>
                            <div class="bm-progress"><div style="width:{pct}%"></div></div>
                            <div class="bm-tags">{tags}</div>
                            {note_html}
                        </div>
                    </div>
                    """
                )
            st.markdown('<div class="bm-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)

with tab_agregar:
    st.subheader("Agregar nueva obra")
    with st.form("obra_form"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Titulo *")
            autor = st.text_input("Autor / creador / estudio")
            tipo = st.selectbox("Tipo", TIPOS)
            clasificacion = st.slider("Nota personal", 0.0, 10.0, 0.0, 0.5)
            estado_lectura = st.selectbox("Estado personal", ESTADOS)
            estado_publicacion = st.selectbox("Estado de publicacion", ESTADOS_PUBLICACION)
            capitulo_actual = st.number_input("Capitulo / episodio actual", min_value=0, step=1)
            capitulo_total = st.number_input("Capitulos / episodios totales", min_value=0, step=1)
        with col2:
            etiquetas = st.text_input("Etiquetas separadas por coma")
            link_original = st.text_input("Link original")
            link_respaldo = st.text_input("Link de respaldo")
            motivo_estado = st.text_area("Opinion corta, personajes, ships, frases o nota importante")
            favorito = st.checkbox("Favorito")
            portada_url = st.text_input("URL de portada opcional")
            buscar_portada = st.checkbox("Buscar portada automaticamente si es libro", value=False)
            sin_fecha_inicio = st.checkbox("Sin fecha de inicio", value=True)
            fecha_inicio = None if sin_fecha_inicio else st.date_input("Fecha de inicio", value=date.today())
            sin_fecha_fin = st.checkbox("Sin fecha de finalizacion", value=True)
            fecha_fin = None if sin_fecha_fin else st.date_input("Fecha de finalizacion", value=date.today())
        sinopsis = st.text_area("Sinopsis / descripcion general")
        portada = st.file_uploader("Portada", type=["jpg", "jpeg", "png", "webp"])
        respaldo = st.file_uploader("Archivo de respaldo", type=["pdf", "epub", "txt", "docx", "zip", "jpg", "jpeg", "png", "webp"])
        submitted = st.form_submit_button("Guardar obra")
        if submitted:
            if not titulo.strip():
                st.error("El titulo es obligatorio.")
            else:
                portada_path = save_uploaded_file(portada, PORTADAS_DIR)
                if not portada_path and portada_url.strip():
                    portada_path = portada_url.strip()
                if not portada_path and buscar_portada:
                    portada_path = buscar_portada_openlibrary(titulo.strip(), autor.strip())
                add_obra({"titulo": titulo.strip(), "autor": autor.strip(), "tipo": tipo, "clasificacion": clasificacion, "estado_lectura": estado_lectura, "estado_publicacion": estado_publicacion, "capitulo_actual": int(capitulo_actual), "capitulo_total": int(capitulo_total), "sinopsis": sinopsis, "etiquetas": parse_tags(etiquetas), "link_original": link_original, "link_respaldo": link_respaldo, "portada_path": portada_path, "respaldo_path": save_uploaded_file(respaldo, RESPALDOS_DIR), "motivo_estado": motivo_estado, "favorito": 1 if favorito else 0, "fecha_inicio": str(fecha_inicio) if fecha_inicio else None, "fecha_fin": str(fecha_fin) if fecha_fin else None})
                st.success("Obra guardada. Recarga la pagina para verla en biblioteca.")

    st.divider()
    st.subheader("Edicion rapida")
    if obras:
        choices = {f"{o['id']} - {o['titulo']}": o["id"] for o in obras}
        selected = st.selectbox("Selecciona una obra", list(choices.keys()))
        obra = get_obra(choices[selected])
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            nuevo_cap = st.number_input("Nuevo progreso", min_value=0, value=int(obra.get("capitulo_actual") or 0), step=1)
        with col2:
            nuevo_estado = st.selectbox("Nuevo estado", ESTADOS, index=ESTADOS.index(obra.get("estado_lectura")) if obra.get("estado_lectura") in ESTADOS else 0)
        with col3:
            nuevo_rank = st.slider("Nueva nota", 0.0, 10.0, float(obra.get("clasificacion") or 0), 0.5)
        with col4:
            nuevo_fav = st.checkbox("Favorito", value=bool(obra.get("favorito")))
        nueva_opinion = st.text_area("Opinion corta", value=obra.get("motivo_estado") or "")
        if st.button("Actualizar obra"):
            update_obra(obra["id"], {"capitulo_actual": int(nuevo_cap), "estado_lectura": nuevo_estado, "clasificacion": float(nuevo_rank), "favorito": 1 if nuevo_fav else 0, "motivo_estado": nueva_opinion, "fecha_fin": str(date.today()) if nuevo_estado == "Terminado" and not obra.get("fecha_fin") else obra.get("fecha_fin")})
            st.success("Obra actualizada.")
        if st.button("Eliminar obra", type="secondary"):
            delete_obra(obra["id"])
            st.warning("Obra eliminada. Recarga la pagina.")

with tab_capitulos:
    st.subheader("Capitulos, episodios y opiniones completas")
    if not obras:
        st.info("Primero agrega una obra.")
    else:
        choices = {f"{o['id']} - {o['titulo']}": o["id"] for o in obras}
        selected = st.selectbox("Obra", list(choices.keys()), key="cap_obra")
        obra_id = choices[selected]
        with st.form("capitulo_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero = st.number_input("Numero", min_value=0, step=1)
            with col2:
                cap_titulo = st.text_input("Titulo del capitulo / episodio")
            with col3:
                fecha_lectura = st.date_input("Fecha", value=date.today())
            cap_sinopsis = st.text_area("Resumen completo")
            notas = st.text_area("Opinion, teorias, spoilers, escenas favoritas")
            if st.form_submit_button("Guardar capitulo"):
                add_capitulo({"obra_id": obra_id, "numero": int(numero), "titulo": cap_titulo, "sinopsis": cap_sinopsis, "notas": notas, "fecha_lectura": str(fecha_lectura)})
                update_obra(obra_id, {"capitulo_actual": int(numero)})
                st.success("Capitulo guardado.")
        caps = list_capitulos(obra_id)
        if caps:
            st.write("### Historial")
            for cap in caps:
                st.markdown(f"**#{cap['numero']} - {cap.get('titulo') or 'Sin titulo'}**")
                st.caption(cap.get("fecha_lectura"))
                if cap.get("sinopsis"):
                    st.write(cap.get("sinopsis"))
                if cap.get("notas"):
                    st.info(cap.get("notas"))

with tab_estadisticas:
    st.subheader("Estadisticas")
    if df.empty:
        st.info("Agrega obras para ver estadisticas.")
    else:
        stats = df.copy()
        stats["clasificacion"] = pd.to_numeric(stats["clasificacion"], errors="coerce").fillna(0)
        stats["fecha_fin_dt"] = pd.to_datetime(stats["fecha_fin"], errors="coerce")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(stats))
        c2.metric("Terminadas", int((stats["estado_lectura"] == "Terminado").sum()))
        c3.metric("En progreso", int(stats["estado_lectura"].isin(["Leyendo", "Viendo", "Releyendo", "Rewatch"]).sum()))
        c4.metric("Favoritos", int(stats["favorito"].fillna(0).astype(int).sum()))
        st.write("### Top 10")
        st.dataframe(stats.sort_values("clasificacion", ascending=False).head(10)[["titulo", "autor", "tipo", "clasificacion", "estado_lectura", "etiquetas"]], use_container_width=True)
        col_a, col_b = st.columns(2)
        with col_a:
            por_tipo = stats.groupby("tipo").size().reset_index(name="cantidad")
            st.plotly_chart(px.bar(por_tipo, x="tipo", y="cantidad", title="Obras por tipo"), use_container_width=True)
        with col_b:
            por_estado = stats.groupby("estado_lectura").size().reset_index(name="cantidad")
            st.plotly_chart(px.pie(por_estado, names="estado_lectura", values="cantidad", title="Estados"), use_container_width=True)

with tab_recomendaciones:
    st.subheader("Recomendaciones")
    if df.empty:
        st.info("Cuando agregues obras, aqui apareceran recomendaciones basadas en favoritos y notas altas.")
    else:
        base = df.copy()
        base["clasificacion"] = pd.to_numeric(base["clasificacion"], errors="coerce").fillna(0)
        amadas = base[(base["favorito"].fillna(0).astype(int) == 1) | (base["clasificacion"] >= 8.0)]
        pendientes = base[base["estado_lectura"].isin(["Pendiente", "Pausado"])]
        if amadas.empty:
            st.info("Marca favoritos o pon notas altas para que el sistema aprenda tus gustos.")
        else:
            tags = []
            for value in amadas["etiquetas"].fillna(""):
                tags.extend([t.strip() for t in value.split(",") if t.strip()])
            top_tags = pd.Series(tags).value_counts().head(10) if tags else pd.Series(dtype=int)
            if not top_tags.empty:
                st.dataframe(top_tags.reset_index().rename(columns={"index": "tag", 0: "veces"}), use_container_width=True)
            if not pendientes.empty:
                favoritas_tags = set(top_tags.index.tolist()) if not top_tags.empty else set()
                def score(row):
                    row_tags = {t.strip() for t in str(row.get("etiquetas") or "").split(",") if t.strip()}
                    return len(row_tags & favoritas_tags) + float(row.get("clasificacion") or 0) / 10
                pendientes = pendientes.copy()
                pendientes["afinidad"] = pendientes.apply(score, axis=1)
                st.dataframe(pendientes.sort_values("afinidad", ascending=False)[["titulo", "tipo", "estado_lectura", "etiquetas", "afinidad"]], use_container_width=True)

with tab_exportar:
    st.subheader("Exportar datos")
    if df.empty:
        st.info("No hay datos para exportar todavia.")
    else:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar biblioteca en CSV", csv, "paz-mental-biblioteca.csv", "text/csv")
        st.dataframe(df, use_container_width=True)
