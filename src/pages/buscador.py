import difflib

import streamlit as st

BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
FUENTES_BUSQUEDA = ["Buscar en todo", "Libros", "Manga / manhwa / novelas ligeras", "Webnovels", "Series / anime / TV", "Kdramas", "Peliculas"]


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


def _normalizar_item(item, fuente_nombre, kind=None):
    item = dict(item or {})
    item.setdefault("fuente_importacion", fuente_nombre)
    item.setdefault("grupo_resultado", fuente_nombre)
    item.setdefault("kind", kind or item.get("kind") or "")
    item.setdefault("id_externo", item.get("id") or item.get("external_id") or "")
    item.setdefault("url_fuente", item.get("url") or item.get("link") or item.get("link_original") or "")
    return item


def _buscar_en_todo(query, buscar_global):
    todos = []
    for fuente in FUENTES_BUSQUEDA[1:]:
        try:
            resultados, kind = buscar_global(query, fuente)
            for r in resultados:
                todos.append(_normalizar_item(r, fuente, kind))
        except Exception as exc:
            todos.append({
                "titulo": f"Error buscando en {fuente}",
                "autor": "",
                "sinopsis": str(exc),
                "portada_path": "",
                "fuente_importacion": fuente,
                "grupo_resultado": fuente,
                "kind": "error",
            })
    return todos, "global"


def _calidad_score(item):
    return sum([
        bool(item.get("portada_path")),
        bool(item.get("sinopsis")),
        bool(item.get("autor")),
        bool(item.get("anio")),
        int(item.get("capitulo_total") or 0) > 0,
        bool(item.get("url_fuente") or item.get("link_original")),
    ])


def _calidad_label(score):
    if score >= 5:
        return "Alta"
    if score >= 3:
        return "Media"
    return "Baja"


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
    score = _calidad_score(item)
    calidad = _calidad_label(score)
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
    st.caption("Fase 3: búsqueda global, edición completa, importación rápida, calidad, filtros y revisión antes de guardar.")

    fuente = st.radio("¿Qué quieres buscar?", FUENTES_BUSQUEDA, horizontal=True, key="buscador_fuente")
    query = st.text_input("Nombre de la obra", key="buscador_query")
    estado_import = st.selectbox("Estado al importar", ESTADOS, index=0, key="buscador_estado")

    if st.button("Buscar", key="buscador_btn") and query.strip():
        if fuente == "Buscar en todo":
            resultados, kind = _buscar_en_todo(query, buscar_global)
        else:
            resultados, kind = buscar_global(query, fuente)
            resultados = [_normalizar_item(r, fuente, kind) for r in resultados]
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
    grupos = sorted(set([r.get("grupo_resultado") or r.get("fuente_importacion") or "Otros" for r in results]))
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Resultados", len(results))
    col_r2.metric("Con portada", sum(1 for r in results if r.get("portada_path")))
    col_r3.metric("Con sinopsis", sum(1 for r in results if r.get("sinopsis")))
    col_r4.metric("Calidad alta", sum(1 for r in results if _calidad_score(r) >= 5))

    with st.expander("🎛️ Filtros rápidos y orden", expanded=True):
        filtro_grupo = st.multiselect("Fuentes / grupos", grupos, default=grupos, key="buscador_filtro_grupo")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            solo_portada = st.checkbox("Solo con portada", key="filtro_portada")
        with col_f2:
            solo_sinopsis = st.checkbox("Solo con sinopsis", key="filtro_sinopsis")
        with col_f3:
            solo_alta = st.checkbox("Solo calidad alta", key="filtro_alta")
        with col_f4:
            ocultar_duplicados = st.checkbox("Ocultar duplicados", key="filtro_dupes")
        ordenar = st.selectbox("Ordenar", ["Calidad primero", "Fuente", "Título A-Z"], key="orden_resultados")

    filtered = []
    for r in results:
        grupo = r.get("grupo_resultado") or r.get("fuente_importacion") or "Otros"
        duplicados_tmp = _detectar_duplicados(r.get("titulo", ""), obras)
        if grupo not in filtro_grupo:
            continue
        if solo_portada and not r.get("portada_path"):
            continue
        if solo_sinopsis and not r.get("sinopsis"):
            continue
        if solo_alta and _calidad_score(r) < 5:
            continue
        if ocultar_duplicados and duplicados_tmp:
            continue
        filtered.append(r)

    if ordenar == "Calidad primero":
        filtered.sort(key=lambda x: _calidad_score(x), reverse=True)
    elif ordenar == "Fuente":
        filtered.sort(key=lambda x: (x.get("grupo_resultado") or x.get("fuente_importacion") or "", x.get("titulo") or ""))
    else:
        filtered.sort(key=lambda x: (x.get("titulo") or "").lower())

    st.caption(f"Mostrando {len(filtered)} de {len(results)} resultados después de filtros.")

    for i, item in enumerate(filtered):
        item = _normalizar_item(item, item.get("fuente_importacion") or fuente_actual, item.get("kind") or kind)
        titulo_original = item.get("titulo", "")
        duplicados = _detectar_duplicados(titulo_original, obras)
        item_kind = item.get("kind") or kind

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
            st.caption(f"Grupo: {item.get('grupo_resultado') or item.get('fuente_importacion') or fuente_actual}")
            st.write(item.get("autor") or "Autor / canal no indicado")
            if item.get("sinopsis"):
                st.write(str(item.get("sinopsis"))[:700])
            if item.get("url_fuente"):
                st.caption(f"URL fuente: {item.get('url_fuente')}")

        if duplicados:
            st.warning("Posibles duplicados ya guardados: " + ", ".join([d.get("titulo", "Sin título") for d in duplicados]))

        col_fast, col_edit = st.columns([1, 3])
        with col_fast:
            if st.button("⚡ Importar rápido", key=f"quick_import_{i}"):
                guardar_importado(item, _opciones_tipo(item_kind)[0], estado_import)
                st.success(f"Importado rápido: {titulo_original}")

        with st.expander("✏️ Revisar / editar antes de importar"):
            st.markdown("#### 1. Datos principales")
            tipo_opts = _opciones_tipo(item_kind)
            col_a, col_b = st.columns(2)
            with col_a:
                titulo_edit = st.text_input("Título", value=item.get("titulo", ""), key=f"imp_titulo_{i}")
                autor_edit = st.text_input("Autor / creador", value=item.get("autor", ""), key=f"imp_autor_{i}")
                tipo_edit = st.selectbox("Tipo", tipo_opts, key=f"imp_tipo_{i}")
                anio_edit = st.text_input("Año", value=str(item.get("anio") or ""), key=f"imp_anio_{i}")
            with col_b:
                estado_edit = st.selectbox("Estado personal", ESTADOS, index=ESTADOS.index(estado_import) if estado_import in ESTADOS else 0, key=f"imp_estado_{i}")
                estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION, index=6, key=f"imp_estado_pub_{i}")
                fecha_pub = st.text_input("Fecha de publicación", value=item.get("fecha_publicacion") or item.get("anio") or "", key=f"imp_fecha_pub_{i}")
                fuente_edit = st.text_input("Fuente importación", value=item.get("fuente_importacion") or fuente_actual, key=f"imp_fuente_{i}")

            st.markdown("#### 2. Progreso inicial")
            col_c, col_d = st.columns(2)
            with col_c:
                capitulos_total = st.number_input("Capítulos / episodios publicados", min_value=0, value=int(item.get("capitulo_total") or 0), step=1, key=f"imp_caps_{i}")
            with col_d:
                capitulos_vistos = st.number_input("Capítulos / episodios ya vistos/leídos", min_value=0, value=0, step=1, key=f"imp_caps_vistos_{i}")

            st.markdown("#### 3. Portada, etiquetas y fuente")
            portada_edit = st.text_input("URL portada", value=item.get("portada_path", ""), key=f"imp_portada_{i}")
            etiquetas_edit = st.text_input("Etiquetas", value=item.get("etiquetas", "importado"), key=f"imp_tags_{i}")
            url_fuente_edit = st.text_input("URL / link fuente", value=item.get("url_fuente", ""), key=f"imp_url_{i}")
            sinopsis_edit = st.text_area("Sinopsis", value=item.get("sinopsis", ""), height=160, key=f"imp_sinopsis_{i}")

            st.markdown("#### 4. Confirmación")
            st.info(f"Se importará como **{tipo_edit}** con estado **{estado_edit}** y {int(capitulos_vistos)} / {int(capitulos_total)} capítulos.")
            if st.button("✅ Confirmar importación revisada", key=f"import_edit_{i}"):
                item_editado = dict(item)
                item_editado.update({
                    "titulo": titulo_edit.strip(),
                    "autor": autor_edit.strip(),
                    "anio": anio_edit.strip(),
                    "fecha_publicacion": fecha_pub.strip(),
                    "estado_publicacion": estado_pub,
                    "sinopsis": sinopsis_edit.strip(),
                    "portada_path": portada_edit.strip(),
                    "etiquetas": etiquetas_edit.strip(),
                    "capitulo_total": int(capitulos_total),
                    "capitulos_vistos": int(capitulos_vistos),
                    "capitulo_actual": int(capitulos_vistos),
                    "fuente_importacion": fuente_edit.strip(),
                    "url_fuente": url_fuente_edit.strip(),
                    "link_original": url_fuente_edit.strip(),
                })
                guardar_importado(item_editado, tipo_edit, estado_edit)
                st.success(f"Importado revisado: {titulo_edit}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()
