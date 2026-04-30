port streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

from src.database import init_db, add_obra, update_obra, delete_obra, list_obras, get_obra, add_capitulo, list_capitulos
from src.utils import save_uploaded_file, parse_tags, PORTADAS_DIR, RESPALDOS_DIR, ensure_dirs
from src.styles import apply_styles

st.set_page_config(page_title="Pas Mental de Libros", page_icon="📚", layout="wide")
apply_styles()
ensure_dirs()
init_db()

TIPOS = ["Libro", "Fanfiction", "Novela", "Manga", "Manhwa", "Manhua", "Webnovel", "Otro"]
ESTADOS_LECTURA = ["Pendiente", "Leyendo", "Terminado", "Pausado", "Abandonado"]
ESTADOS_PUBLICACION = ["En emisión", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor"]

st.title("📚 Pas Mental de Libros")
st.caption("Biblioteca personal, respaldo de lecturas y ranking mensual/anual.")

tab_biblioteca, tab_agregar, tab_capitulos, tab_estadisticas = st.tabs(
    ["Biblioteca", "Agregar / editar obra", "Capítulos y notas", "Rankings"]
)

obras = list_obras()
df = pd.DataFrame(obras)

with tab_biblioteca:
    st.subheader("Biblioteca")

    with st.sidebar:
        st.header("Filtros")
        q = st.text_input("Buscar título o autor")
        tipo_f = st.multiselect("Tipo", TIPOS)
        lectura_f = st.multiselect("Estado de lectura", ESTADOS_LECTURA)
        publicacion_f = st.multiselect("Estado de publicación", ESTADOS_PUBLICACION)
        min_rank = st.slider("Ranking mínimo", 0.0, 5.0, 0.0, 0.5)
        tag_q = st.text_input("Etiqueta contiene")

    filtered = df.copy() if not df.empty else pd.DataFrame()
    if not filtered.empty:
        if q:
            mask = filtered["titulo"].fillna("").str.contains(q, case=False) | filtered["autor"].fillna("").str.contains(q, case=False)
            filtered = filtered[mask]
        if tipo_f:
            filtered = filtered[filtered["tipo"].isin(tipo_f)]
        if lectura_f:
            filtered = filtered[filtered["estado_lectura"].isin(lectura_f)]
        if publicacion_f:
            filtered = filtered[filtered["estado_publicacion"].isin(publicacion_f)]
        filtered = filtered[filtered["clasificacion"].fillna(0) >= min_rank]
        if tag_q:
            filtered = filtered[filtered["etiquetas"].fillna("").str.contains(tag_q, case=False)]

    if filtered.empty:
        st.info("Todavía no hay obras registradas o no coinciden con los filtros.")
    else:
        for _, obra in filtered.iterrows():
            st.markdown('<div class="book-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 4])
            with col1:
                portada = obra.get("portada_path")
                if portada and Path(portada).exists():
                    st.image(portada, use_column_width=True)
                else:
                    st.write("📖 Sin portada")
            with col2:
                fav = "⭐ " if obra.get("favorito") else ""
                st.markdown(f"### {fav}{obra.get('titulo', 'Sin título')}")
                st.markdown(f"**Autor:** {obra.get('autor') or 'No indicado'}")
                st.markdown(
                    f"<span class='status-pill'>{obra.get('tipo')}</span>"
                    f"<span class='status-pill'>{obra.get('estado_lectura')}</span>"
                    f"<span class='status-pill'>{obra.get('estado_publicacion')}</span>",
                    unsafe_allow_html=True,
                )
                st.write(f"**Ranking:** {obra.get('clasificacion', 0)} / 5")
                st.write(f"**Capítulo:** {obra.get('capitulo_actual', 0)} / {obra.get('capitulo_total', 0)}")
                st.write(f"**Etiquetas:** {obra.get('etiquetas') or 'Sin etiquetas'}")
                if obra.get("sinopsis"):
                    st.write(obra.get("sinopsis"))
                if obra.get("link_original"):
                    st.link_button("Abrir link original", obra.get("link_original"))
                if obra.get("link_respaldo"):
                    st.link_button("Abrir link respaldo", obra.get("link_respaldo"))
                if obra.get("respaldo_path") and Path(obra.get("respaldo_path")).exists():
                    with open(obra.get("respaldo_path"), "rb") as f:
                        st.download_button("Descargar respaldo subido", f, file_name=Path(obra.get("respaldo_path")).name)
            st.markdown("</div>", unsafe_allow_html=True)

with tab_agregar:
    st.subheader("Agregar nueva obra")

    with st.form("obra_form"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título *")
            autor = st.text_input("Autor")
            tipo = st.selectbox("Tipo", TIPOS)
            clasificacion = st.slider("Clasificación / ranking personal", 0.0, 5.0, 0.0, 0.5)
            estado_lectura = st.selectbox("Estado de lectura", ESTADOS_LECTURA)
            estado_publicacion = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION)
            capitulo_actual = st.number_input("Capítulo actual", min_value=0, step=1)
            capitulo_total = st.number_input("Capítulos totales", min_value=0, step=1)
        with col2:
            etiquetas = st.text_input("Etiquetas separadas por coma")
            link_original = st.text_input("Link original")
            link_respaldo = st.text_input("Link de respaldo")
            motivo_estado = st.text_area("Motivo de pausa, abandono o nota de hiatus")
            favorito = st.checkbox("Favorito")
            fecha_inicio = st.date_input("Fecha de inicio", value=None)
            fecha_fin = st.date_input("Fecha de finalización", value=None)
        sinopsis = st.text_area("Sinopsis general")
        portada = st.file_uploader("Portada", type=["jpg", "jpeg", "png", "webp"])
        respaldo = st.file_uploader("Archivo de respaldo", type=["pdf", "epub", "txt", "docx", "zip", "jpg", "jpeg", "png", "webp"])

        submitted = st.form_submit_button("Guardar obra")
        if submitted:
            if not titulo.strip():
                st.error("El título es obligatorio.")
            else:
                portada_path = save_uploaded_file(portada, PORTADAS_DIR)
                respaldo_path = save_uploaded_file(respaldo, RESPALDOS_DIR)
                add_obra({
                    "titulo": titulo.strip(),
                    "autor": autor.strip(),
                    "tipo": tipo,
                    "clasificacion": clasificacion,
                    "estado_lectura": estado_lectura,
                    "estado_publicacion": estado_publicacion,
                    "capitulo_actual": int(capitulo_actual),
                    "capitulo_total": int(capitulo_total),
                    "sinopsis": sinopsis,
                    "etiquetas": parse_tags(etiquetas),
                    "link_original": link_original,
                    "link_respaldo": link_respaldo,
                    "portada_path": portada_path,
                    "respaldo_path": respaldo_path,
                    "motivo_estado": motivo_estado,
                    "favorito": 1 if favorito else 0,
                    "fecha_inicio": str(fecha_inicio) if fecha_inicio else None,
                    "fecha_fin": str(fecha_fin) if fecha_fin else None,
                })
                st.success("Obra guardada. Recarga la página para verla en biblioteca.")

    st.divider()
    st.subheader("Edición rápida")
    if obras:
        choices = {f"{o['id']} - {o['titulo']}": o["id"] for o in obras}
        selected = st.selectbox("Selecciona una obra", list(choices.keys()))
        obra = get_obra(choices[selected])
        col1, col2, col3 = st.columns(3)
        with col1:
            nuevo_cap = st.number_input("Nuevo capítulo actual", min_value=0, value=int(obra.get("capitulo_actual") or 0), step=1)
        with col2:
            nuevo_estado = st.selectbox("Nuevo estado de lectura", ESTADOS_LECTURA, index=ESTADOS_LECTURA.index(obra.get("estado_lectura")) if obra.get("estado_lectura") in ESTADOS_LECTURA else 0)
        with col3:
            nuevo_rank = st.slider("Nuevo ranking", 0.0, 5.0, float(obra.get("clasificacion") or 0), 0.5)
        if st.button("Actualizar obra"):
            update_obra(obra["id"], {
                "capitulo_actual": int(nuevo_cap),
                "estado_lectura": nuevo_estado,
                "clasificacion": float(nuevo_rank),
                "fecha_fin": str(date.today()) if nuevo_estado == "Terminado" and not obra.get("fecha_fin") else obra.get("fecha_fin"),
            })
            st.success("Obra actualizada.")
        if st.button("Eliminar obra", type="secondary"):
            delete_obra(obra["id"])
            st.warning("Obra eliminada. Recarga la página.")

with tab_capitulos:
    st.subheader("Capítulos, sinopsis y notas")
    if not obras:
        st.info("Primero agrega una obra.")
    else:
        choices = {f"{o['id']} - {o['titulo']}": o["id"] for o in obras}
        selected = st.selectbox("Obra", list(choices.keys()), key="cap_obra")
        obra_id = choices[selected]

        with st.form("capitulo_form"):
            col1, col2 = st.columns(2)
            with col1:
                numero = st.number_input("Número de capítulo", min_value=0, step=1)
                cap_titulo = st.text_input("Título del capítulo")
            with col2:
                fecha_lectura = st.date_input("Fecha de lectura", value=date.today())
            cap_sinopsis = st.text_area("Sinopsis del capítulo")
            notas = st.text_area("Notas personales")
            if st.form_submit_button("Guardar capítulo"):
                add_capitulo({
                    "obra_id": obra_id,
                    "numero": int(numero),
                    "titulo": cap_titulo,
                    "sinopsis": cap_sinopsis,
                    "notas": notas,
                    "fecha_lectura": str(fecha_lectura),
                })
                update_obra(obra_id, {"capitulo_actual": int(numero)})
                st.success("Capítulo guardado.")

        caps = list_capitulos(obra_id)
        if caps:
            st.write("### Historial de capítulos")
            for cap in caps:
                st.markdown(f"**Capítulo {cap['numero']} — {cap.get('titulo') or 'Sin título'}**")
                st.caption(cap.get("fecha_lectura"))
                if cap.get("sinopsis"):
                    st.write(cap.get("sinopsis"))
                if cap.get("notas"):
                    st.info(cap.get("notas"))

with tab_estadisticas:
    st.subheader("Rankings mensual y anual")
    if df.empty:
        st.info("Agrega obras para ver estadísticas.")
    else:
        stats = df.copy()
        stats["fecha_fin_dt"] = pd.to_datetime(stats["fecha_fin"], errors="coerce")
        stats["clasificacion"] = pd.to_numeric(stats["clasificacion"], errors="coerce").fillna(0)
        terminadas = stats[stats["estado_lectura"] == "Terminado"].copy()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total obras", len(stats))
        c2.metric("Terminadas", len(terminadas))
        c3.metric("Leyendo", int((stats["estado_lectura"] == "Leyendo").sum()))
        c4.metric("En hiatus", int(stats["estado_publicacion"].fillna("").str.contains("Hiatus").sum()))

        if not terminadas.empty:
            terminadas["mes"] = terminadas["fecha_fin_dt"].dt.to_period("M").astype(str)
            terminadas["anio"] = terminadas["fecha_fin_dt"].dt.year.astype("Int64")

            st.write("### Mejor ranking personal")
            top = stats.sort_values("clasificacion", ascending=False).head(10)
            st.dataframe(top[["titulo", "autor", "tipo", "clasificacion", "estado_lectura", "estado_publicacion"]], use_container_width=True)

            st.write("### Obras terminadas por mes")
            por_mes = terminadas.groupby("mes").size().reset_index(name="cantidad")
            fig = px.bar(por_mes, x="mes", y="cantidad", title="Terminadas por mes")
            st.plotly_chart(fig, use_container_width=True)

            st.write("### Obras terminadas por año")
            por_anio = terminadas.groupby("anio").size().reset_index(name="cantidad")
            fig2 = px.bar(por_anio, x="anio", y="cantidad", title="Terminadas por año")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Cuando marques obras como terminadas con fecha de finalización aparecerán los rankings mensual/anual.")
