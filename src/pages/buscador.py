import difflib
from datetime import date

import streamlit as st

BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]


def _detectar_duplicados(titulo, obras):
    if not titulo or not obras:
        return []
    nombres = [(o.get("titulo", ""), o) for o in obras]
    matches = []
    for nombre, obra in nombres:
        ratio = difflib.SequenceMatcher(None, titulo.lower(), str(nombre).lower()).ratio()
        if ratio >= 0.78:
            matches.append((ratio, obra))
    matches.sort(key=lambda x: x[0], reverse=True)
    return [obra for _, obra in matches[:5]]


def _opciones_tipo(kind):
    if kind == "movie":
        return ["Pelicula", "Documental", "Otro"]
    if kind == "kdrama":
        return ["Kdrama", "Serie"]
    if kind in ["manga", "webnovel"]:
        return ["Manga", "Manhwa", "Manhua", "Novela ligera", "Webnovel", "Fanfiction"]
    if kind == "book":
        return BOOK_TYPES
    return TV_TYPES


def _normalizar_item(item, fuente_nombre):
    item = dict(item or {})
    item.setdefault("fuente_importacion", fuente_nombre)
    item.setdefault("id_externo", item.get("id") or item.get("external_id") or "")
    item.setdefault("url_fuente", item.get("url") or item.get("link") or item.get("link_original") or "")
    return item


def render_buscador_avanzado(obras, buscar_global, guardar_importado):
    st.subheader("🔎 Buscar e importar")
    st.caption("Fase 1: vista previa, edición antes de importar, fuente del resultado y alerta de duplicados.")

    fuente = st.radio(
        "¿Qué quieres buscar?",
        ["Libros", "Manga / manhwa / novelas ligeras", "Webnovels", "Series / anime / TV", "Kdramas", "Peliculas"],
        horizontal=True,
        key="buscador_fuente",
    )
    query = st.text_input("Nombre de la obra", key="buscador_query")
    estado_import = st.selectbox("Estado al importar", ESTADOS, index=0, key="buscador_estado")

    if st.button("Buscar", key="buscador_btn") and query.strip():
        resultados, kind = buscar_global(query, fuente)
        resultados = [_normalizar_item(r, fuente) for r in resultados]
        st.session_state["external_results"] = resultados
        st.session_state["external_kind"] = kind
        st.session_state["external_source"] = fuente

    results = st.session_state.get("external_results", [])
    kind = st.session_state.get("external_kind")
    fuente_actual = st.session_state.get("external_source", fuente)

    if not results:
        st.info("Busca una obra. Si no aparece, usa Importar link o Agregar manual.")
        return

    st.success(f"Resultados encontrados: {len(results)}")

    for i, item in enumerate(results):
        item = _normalizar_item(item, fuente_actual)
        titulo_original = item.get("titulo", "")
        duplicados = _detectar_duplicados(titulo_original, obras)

        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                if item.get("portada_path"):
                    st.image(item.get("portada_path"), use_container_width=True)
                else:
                    st.write("Sin portada")
            with col2:
                st.markdown(f"### {titulo_original or 'Sin título'}")
                st.caption(f"Fuente: {item.get('fuente_importacion') or fuente_actual} · Año: {item.get('anio') or 'N/D'}")
                st.write(item.get("autor") or "Autor / canal no indicado")
                if item.get("sinopsis"):
                    st.write(str(item.get("sinopsis"))[:700])
                if item.get("url_fuente"):
                    st.caption(f"URL fuente: {item.get('url_fuente')}")

            if duplicados:
                st.warning("Posibles duplicados ya guardados: " + ", ".join([d.get("titulo", "Sin título") for d in duplicados]))

            with st.expander("✏️ Editar antes de importar"):
                tipo_opts = _opciones_tipo(kind)
                col_a, col_b = st.columns(2)
                with col_a:
                    titulo_edit = st.text_input("Título", value=item.get("titulo", ""), key=f"imp_titulo_{i}")
                    autor_edit = st.text_input("Autor / creador", value=item.get("autor", ""), key=f"imp_autor_{i}")
                    tipo_edit = st.selectbox("Tipo", tipo_opts, key=f"imp_tipo_{i}")
                    anio_edit = st.text_input("Año", value=str(item.get("anio") or ""), key=f"imp_anio_{i}")
                with col_b:
                    portada_edit = st.text_input("URL portada", value=item.get("portada_path", ""), key=f"imp_portada_{i}")
                    etiquetas_edit = st.text_input("Etiquetas", value=item.get("etiquetas", "importado"), key=f"imp_tags_{i}")
                    capitulos_total = st.number_input("Capítulos / episodios publicados", min_value=0, value=int(item.get("capitulo_total") or 0), step=1, key=f"imp_caps_{i}")
                    fuente_edit = st.text_input("Fuente importación", value=item.get("fuente_importacion") or fuente_actual, key=f"imp_fuente_{i}")
                sinopsis_edit = st.text_area("Sinopsis", value=item.get("sinopsis", ""), height=160, key=f"imp_sinopsis_{i}")
                url_fuente_edit = st.text_input("URL / link fuente", value=item.get("url_fuente", ""), key=f"imp_url_{i}")

                col_import, col_skip = st.columns([1, 3])
                with col_import:
                    if st.button("Importar editado", key=f"import_edit_{i}"):
                        item_editado = dict(item)
                        item_editado.update({
                            "titulo": titulo_edit.strip(),
                            "autor": autor_edit.strip(),
                            "anio": anio_edit.strip(),
                            "sinopsis": sinopsis_edit.strip(),
                            "portada_path": portada_edit.strip(),
                            "etiquetas": etiquetas_edit.strip(),
                            "capitulo_total": int(capitulos_total),
                            "fuente_importacion": fuente_edit.strip(),
                            "url_fuente": url_fuente_edit.strip(),
                            "link_original": url_fuente_edit.strip(),
                        })
                        guardar_importado(item_editado, tipo_edit, estado_import)
                        st.success(f"Importado: {titulo_edit}")

        st.divider()
