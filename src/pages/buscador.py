import difflib

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


def _chip(label, ok=True):
    estado = "✅" if ok else "⚠️"
    return f"<span class='quality-chip'>{estado} {label}</span>"


def _quality_html(item, duplicados):
    has_cover = bool(item.get("portada_path"))
    has_synopsis = bool(item.get("sinopsis"))
    has_author = bool(item.get("autor"))
    has_year = bool(item.get("anio"))
    has_caps = int(item.get("capitulo_total") or 0) > 0
    has_url = bool(item.get("url_fuente") or item.get("link_original"))
    source = item.get("fuente_importacion") or "fuente externa"
    score = sum([has_cover, has_synopsis, has_author, has_year, has_caps, has_url])
    if score >= 5:
        calidad = "Alta"
    elif score >= 3:
        calidad = "Media"
    else:
        calidad = "Baja"
    chips = [
        f"<span class='quality-chip strong'>Fuente: {source}</span>",
        f"<span class='quality-chip strong'>Calidad: {calidad}</span>",
        _chip("Portada", has_cover),
        _chip("Sinopsis", has_synopsis),
        _chip("Autor", has_author),
        _chip("Año", has_year),
        _chip("Caps/Eps", has_caps),
        _chip("Link", has_url),
        _chip("Sin duplicado", not bool(duplicados)),
    ]
    return "<div class='quality-row'>" + "".join(chips) + "</div>"


def _inject_styles():
    st.markdown(
        """
        <style>
        .quality-row{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0 10px 0}
        .quality-chip{display:inline-flex;align-items:center;border-radius:999px;padding:5px 10px;font-size:.78rem;font-weight:700;background:rgba(245,240,250,.85);border:1px solid rgba(120,90,140,.18);color:#3d3145}
        .quality-chip.strong{background:rgba(235,224,247,.95);border-color:rgba(120,90,140,.28)}
        .result-card{border:1px solid rgba(120,90,140,.15);border-radius:18px;padding:14px;margin:12px 0;background:rgba(255,255,255,.62);box-shadow:0 8px 28px rgba(30,10,50,.06)}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_buscador_avanzado(obras, buscar_global, guardar_importado):
    _inject_styles()
    st.subheader("🔎 Buscar e importar")
    st.caption("Fase 1.5: vista previa, edición antes de importar, fuente, calidad de datos y alerta de duplicados.")

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

        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 4])
        with col1:
            if item.get("portada_path"):
                st.image(item.get("portada_path"), use_container_width=True)
            else:
                st.write("Sin portada")
        with col2:
            st.markdown(f"### {titulo_original or 'Sin título'}")
            st.markdown(_quality_html(item, duplicados), unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()
