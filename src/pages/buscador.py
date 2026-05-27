import difflib
import re

import streamlit as st

BOOK_TYPES = ["Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"]
TV_TYPES = ["Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"]
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
FUENTES_BUSQUEDA = ["Buscar en todo", "Libros", "Manga / manhwa / novelas ligeras", "Webnovels", "Series / anime / TV", "Kdramas", "Peliculas"]
ORIGEN_TIPOS = ["Libro", "Pelicula", "Serie", "Anime", "Manga", "Manhwa", "Videojuego", "Comic", "Kdrama", "Otro"]
FUENTES_FANFIC = ["AO3", "Wattpad", "FanFiction.net", "Tumblr", "Quotev", "SpaceBattles", "Sufficient Velocity", "Webnovel", "Otro"]
TIPOS_CROSSOVER = ["No aplica", "Mundos mezclados", "Viaje dimensional", "Personajes en otro universo", "Fusion AU", "Multiverso", "Encuentro entre universos", "Otro"]
DIVISIONES_OBRA = ["Temporada", "Arco", "Volumen", "Parte", "Libro", "Saga"]


def _item_key(item):
    return f"{item.get('titulo','')}|{item.get('fuente_importacion','')}|{item.get('url_fuente','')}"


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _is_ao3(url):
    return bool(url and "archiveofourown.org/works/" in str(url))


def _ao3_work_id(url):
    match = re.search(r"archiveofourown\.org/works/(\d+)", str(url or ""))
    return match.group(1) if match else ""


def _tipo_sugerido(item, kind):
    url = str(item.get("url_fuente") or item.get("link_original") or "").lower()
    fuente = str(item.get("fuente_importacion") or "").lower()
    if _is_ao3(url):
        return "Fanfiction"
    if "wattpad" in url or "fanfiction.net" in url or "ao3" in fuente:
        return "Fanfiction"
    if kind == "movie":
        return "Pelicula"
    if kind == "kdrama":
        return "Kdrama"
    if kind == "book":
        return "Libro"
    if kind == "manga":
        return "Manga"
    if kind == "webnovel":
        return "Webnovel"
    return _opciones_tipo(kind)[0]


def _relevancia(item, query):
    if not query:
        return 0
    titulo = str(item.get("titulo") or "").lower()
    autor = str(item.get("autor") or "").lower()
    q = query.lower().strip()
    titulo_score = difflib.SequenceMatcher(None, q, titulo).ratio()
    autor_score = difflib.SequenceMatcher(None, q, autor).ratio() * 0.35 if autor else 0
    contains_bonus = 0.35 if q in titulo else 0
    return round(min(1.0, titulo_score + autor_score + contains_bonus), 3)


def _detectar_duplicados_detallado(item, obras):
    titulo = str(item.get("titulo") or "")
    url = str(item.get("url_fuente") or item.get("link_original") or "").strip().lower()
    autor = str(item.get("autor") or "").lower()
    ao3_id = _ao3_work_id(url)
    matches = []
    for obra in obras or []:
        score = 0
        motivos = []
        obra_titulo = str(obra.get("titulo") or "")
        obra_autor = str(obra.get("autor") or "").lower()
        obra_url = str(obra.get("link_original") or obra.get("url_fuente") or "").strip().lower()
        if url and obra_url and url == obra_url:
            score += 100; motivos.append("mismo link")
        if ao3_id and ao3_id == _ao3_work_id(obra_url):
            score += 100; motivos.append("mismo AO3 work ID")
        if titulo and obra_titulo:
            ratio = difflib.SequenceMatcher(None, titulo.lower(), obra_titulo.lower()).ratio()
            if ratio >= 0.78:
                score += int(ratio * 70); motivos.append(f"título parecido {int(ratio * 100)}%")
        if autor and obra_autor and autor == obra_autor:
            score += 20; motivos.append("mismo autor")
        if score:
            matches.append({"obra": obra, "score": min(100, score), "motivos": motivos})
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]


def _detectar_duplicados(titulo, obras):
    return [m["obra"] for m in _detectar_duplicados_detallado({"titulo": titulo}, obras)]


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
    item.setdefault("temporada_actual", _safe_int(item.get("temporada_actual"), 1) or 1)
    item.setdefault("temporada_total", max(1, _safe_int(item.get("temporada_total"), 1) or 1))
    item.setdefault("division_obra", item.get("division_obra") or "Temporada")
    item.setdefault("capitulos_publicados", _safe_int(item.get("capitulos_publicados"), _safe_int(item.get("capitulo_total"), 0)))
    if _is_ao3(item.get("url_fuente")):
        item.setdefault("tipo", "Fanfiction")
        item.setdefault("fuente_fanfic", "AO3")
        item.setdefault("ao3_work_id", _ao3_work_id(item.get("url_fuente")))
    return item


def _buscar_en_todo(query, buscar_global):
    todos = []
    for fuente in FUENTES_BUSQUEDA[1:]:
        try:
            resultados, kind = buscar_global(query, fuente)
            for r in resultados:
                todos.append(_normalizar_item(r, fuente, kind))
        except Exception as exc:
            todos.append({"titulo": f"Error buscando en {fuente}", "autor": "", "sinopsis": str(exc), "portada_path": "", "fuente_importacion": fuente, "grupo_resultado": fuente, "kind": "error"})
    return todos, "global"


def _quality_breakdown(item):
    parts = [
        ("Portada", 15, bool(item.get("portada_path"))),
        ("Sinopsis", 20, bool(item.get("sinopsis"))),
        ("Autor", 15, bool(item.get("autor"))),
        ("Año / fecha", 10, bool(item.get("anio") or item.get("fecha_publicacion"))),
        ("Caps/Eps", 20, _safe_int(item.get("capitulo_total") or item.get("capitulos_publicados"), 0) > 0),
        ("URL fuente", 20, bool(item.get("url_fuente") or item.get("link_original"))),
    ]
    score = sum(points for _, points, ok in parts if ok)
    return score, parts


def _calidad_score(item):
    return _quality_breakdown(item)[0]


def _calidad_100(item):
    return _quality_breakdown(item)[0]


def _chip(label, ok=True):
    estado = "✅" if ok else "⚠️"
    return f"<span class='quality-chip'>{estado} {label}</span>"


def _quality_html(item, duplicados, query="", favorito=False):
    score, parts = _quality_breakdown(item)
    has_season = int(item.get("temporada_total") or 1) > 0
    source = item.get("fuente_importacion") or "fuente externa"
    relevancia = int(_relevancia(item, query) * 100)
    heart = "❤️ Favorito" if favorito else "🤍 No favorito"
    chips = [
        f"<span class='quality-chip heart'>{heart}</span>",
        f"<span class='quality-chip strong'>Fuente: {source}</span>",
        f"<span class='quality-chip score'>Calidad de datos: {score}/100</span>",
        f"<span class='quality-chip strong'>Relevancia: {relevancia}%</span>",
        _chip("Temporadas", has_season),
    ]
    chips.extend([_chip(label, ok) for label, _, ok in parts])
    chips.append(_chip("Sin duplicado", not bool(duplicados)))
    return "<div class='quality-row'>" + "".join(chips) + "</div>"


def _inject_styles():
    st.markdown("""
        <style>
        .quality-row{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0 10px 0}
        .quality-chip{display:inline-flex;align-items:center;border-radius:999px;padding:5px 10px;font-size:.78rem;font-weight:700;background:rgba(245,240,250,.85);border:1px solid rgba(120,90,140,.18);color:#3d3145}
        .quality-chip.strong{background:rgba(235,224,247,.95);border-color:rgba(120,90,140,.28)}
        .quality-chip.score{background:rgba(231,242,255,.95);border-color:rgba(70,120,190,.25);color:#193d6b}
        .quality-chip.heart{background:rgba(255,232,240,.95);border-color:rgba(180,80,120,.3);color:#7b2144}
        .score-line{font-size:1rem;font-weight:900;color:#193d6b;margin:2px 0 8px 0;background:rgba(231,242,255,.75);border-radius:14px;padding:7px 10px;display:inline-block}
        .result-card{border:1px solid rgba(120,90,140,.15);border-radius:18px;padding:14px;margin:12px 0;background:rgba(255,255,255,.62);box-shadow:0 8px 28px rgba(30,10,50,.06)}
        .mini-note{font-size:.82rem;color:#31577c;background:rgba(231,242,255,.7);padding:7px 10px;border-radius:12px;margin:4px 0}
        </style>
        """, unsafe_allow_html=True)


def _aplicar_defaults(item, defaults):
    data = dict(item)
    data["estado_import_default"] = defaults.get("estado")
    data.setdefault("temporada_actual", defaults.get("temporada_actual", 1))
    data.setdefault("temporada_total", defaults.get("temporada_total", 1))
    data.setdefault("capitulos_vistos", defaults.get("capitulos_vistos", 0))
    data.setdefault("capitulo_actual", defaults.get("capitulos_vistos", 0))
    data.setdefault("etiquetas", defaults.get("etiquetas", "importado"))
    data.setdefault("favorito", 1 if defaults.get("favorito") else 0)
    data.setdefault("division_obra", defaults.get("division_obra", "Temporada"))
    return data


def _render_quality_breakdown(item):
    score, parts = _quality_breakdown(item)
    st.markdown(f"**Calidad de datos: {score}/100** · mide qué tan completo está el resultado, no tu opinión personal.")
    for label, points, ok in parts:
        st.write(f"{'✅' if ok else '⚠️'} {label}: {'+' + str(points) if ok else '+0'}")


def _render_fanfic_extra(prefix, item, tipo_edit):
    fanfic_detectado = tipo_edit == "Fanfiction" or _is_ao3(item.get("url_fuente") or item.get("link_original"))
    data = {}
    activar = st.checkbox("📝 Mostrar datos de fanfiction / canon", value=fanfic_detectado, key=f"{prefix}_show_fanfic")
    if activar:
        c1, c2 = st.columns(2)
        with c1:
            data["obra_original_tipo"] = st.selectbox("Tipo de obra original", ORIGEN_TIPOS, index=0, key=f"{prefix}_obra_original_tipo")
            data["obra_original_nombre"] = st.text_input("Obra original / canon", value=item.get("obra_original_nombre", ""), key=f"{prefix}_obra_original_nombre")
            data["fandom"] = st.text_input("Fandom principal", value=item.get("fandom", ""), key=f"{prefix}_fandom")
            data["ship"] = st.text_input("Ship / relación", value=item.get("ship", ""), key=f"{prefix}_ship")
        with c2:
            fuente_default = "AO3" if _is_ao3(item.get("url_fuente") or item.get("link_original")) else item.get("fuente_fanfic", "Otro")
            fuente_index = FUENTES_FANFIC.index(fuente_default) if fuente_default in FUENTES_FANFIC else len(FUENTES_FANFIC) - 1
            data["fuente_fanfic"] = st.selectbox("Fuente fanfic", FUENTES_FANFIC, index=fuente_index, key=f"{prefix}_fuente_fanfic")
            data["universo_au"] = st.text_input("AU / universo alternativo", value=item.get("universo_au", ""), key=f"{prefix}_universo_au")
            data["es_crossover"] = 1 if st.checkbox("🔀 Es crossover", value=bool(_safe_int(item.get("es_crossover"), 0)), key=f"{prefix}_es_crossover") else 0
        if data.get("es_crossover"):
            c3, c4 = st.columns(2)
            with c3:
                data["crossover_obras"] = st.text_input("Obras del crossover", value=item.get("crossover_obras", ""), key=f"{prefix}_crossover_obras")
                data["crossover_fandoms"] = st.text_input("Fandoms del crossover", value=item.get("crossover_fandoms", ""), key=f"{prefix}_crossover_fandoms")
            with c4:
                data["crossover_tipo"] = st.selectbox("Tipo de crossover", TIPOS_CROSSOVER, index=0, key=f"{prefix}_crossover_tipo")
                data["crossover_notas"] = st.text_area("Notas del crossover", value=item.get("crossover_notas", ""), key=f"{prefix}_crossover_notas")
        else:
            data.update({"crossover_obras": "", "crossover_fandoms": "", "crossover_tipo": "No aplica", "crossover_notas": ""})
    return data


def render_buscador_avanzado(obras, buscar_global, guardar_importado):
    _inject_styles()
    st.subheader("🔎 Buscar e importar")
    st.caption("Fase 7: flujo avanzado sin quitar funciones: ajustes rápidos, temporadas, AO3/fanfiction, cola, calidad 0/100, duplicados y revisión.")

    if "import_queue" not in st.session_state: st.session_state["import_queue"] = []
    if "busquedas_favoritas" not in st.session_state: st.session_state["busquedas_favoritas"] = []
    if "result_favorites" not in st.session_state: st.session_state["result_favorites"] = []
    if "historial_busquedas" not in st.session_state: st.session_state["historial_busquedas"] = []

    with st.expander("⚙️ Ajustes rápidos de importación", expanded=True):
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            estado_import = st.selectbox("Estado al importar", ESTADOS, index=0, key="buscador_estado")
            division_default = st.selectbox("División por defecto", DIVISIONES_OBRA, key="default_division_obra")
        with d2:
            default_temporada_actual = st.number_input("Temporada/arco actual por defecto", min_value=1, value=1, step=1, key="default_temporada_actual")
            default_temporada_total = st.number_input("Temporadas/arcos totales por defecto", min_value=1, value=1, step=1, key="default_temporada_total")
        with d3:
            default_caps_vistos = st.number_input("Caps vistos/leídos por defecto", min_value=0, value=0, step=1, key="default_caps_vistos")
            default_tags = st.text_input("Etiquetas por defecto", value="importado", key="default_tags")
        with d4:
            default_fav = st.checkbox("Marcar como favorito al importar", key="default_fav_import")
            vista = st.radio("Vista", ["Detallada", "Compacta", "Comparación"], horizontal=False, key="buscador_vista")
        defaults = {"estado": estado_import, "temporada_actual": int(default_temporada_actual), "temporada_total": int(max(default_temporada_total, default_temporada_actual)), "capitulos_vistos": int(default_caps_vistos), "etiquetas": default_tags, "favorito": default_fav, "division_obra": division_default}

    fuente = st.radio("¿Qué quieres buscar?", FUENTES_BUSQUEDA, horizontal=True, key="buscador_fuente")
    favs = st.session_state["busquedas_favoritas"]
    if favs:
        fav_selected = st.selectbox("⭐ Búsquedas favoritas", ["No usar"] + favs, key="fav_search_select")
        if fav_selected != "No usar": st.session_state["buscador_query"] = fav_selected

    query = st.text_input("Nombre de la obra", key="buscador_query")
    if st.button("⭐ Guardar búsqueda con filtros", key="guardar_busqueda_fav") and query.strip():
        etiqueta = f"{query.strip()} · {fuente}"
        if etiqueta not in st.session_state["busquedas_favoritas"]:
            st.session_state["busquedas_favoritas"].append(etiqueta); st.success("Búsqueda guardada con su fuente.")
        else: st.info("Ya estaba guardada.")

    if st.button("Buscar", key="buscador_btn") and query.strip():
        query_real = query.split(" · ")[0].strip()
        if fuente == "Buscar en todo": resultados, kind = _buscar_en_todo(query_real, buscar_global)
        else:
            resultados, kind = buscar_global(query_real, fuente); resultados = [_normalizar_item(r, fuente, kind) for r in resultados]
        st.session_state["external_results"] = resultados; st.session_state["external_kind"] = kind; st.session_state["external_source"] = fuente; st.session_state["external_query"] = query_real
        st.session_state["historial_busquedas"].insert(0, {"query": query_real, "fuente": fuente, "resultados": len(resultados)})
        st.session_state["historial_busquedas"] = st.session_state["historial_busquedas"][:10]

    if st.session_state["historial_busquedas"]:
        with st.expander("🕘 Historial de búsquedas", expanded=False):
            for h in st.session_state["historial_busquedas"]:
                st.write(f"{h['query']} — {h['fuente']} — {h['resultados']} resultados")

    results = st.session_state.get("external_results", [])
    kind = st.session_state.get("external_kind")
    fuente_actual = st.session_state.get("external_source", fuente)
    query_actual = st.session_state.get("external_query", query)

    if st.session_state["import_queue"]:
        with st.expander(f"📥 Cola de importación ({len(st.session_state['import_queue'])})", expanded=True):
            lote_estado = st.selectbox("Estado para importar cola", ESTADOS, index=ESTADOS.index(estado_import), key="cola_estado_lote")
            lote_tag = st.text_input("Añadir etiqueta a toda la cola", key="cola_tag_lote")
            seleccionados = []
            for idx, queued in enumerate(st.session_state["import_queue"]):
                checked = st.checkbox(f"{idx + 1}. {queued.get('titulo') or 'Sin título'} — {queued.get('tipo') or _tipo_sugerido(queued, queued.get('kind'))} — T{queued.get('temporada_actual') or 1}/{queued.get('temporada_total') or 1} — {queued.get('capitulos_vistos') or 0}/{queued.get('capitulo_total') or queued.get('capitulos_publicados') or 0} caps — calidad {_calidad_100(queued)}/100", value=True, key=f"cola_select_{idx}")
                if checked: seleccionados.append(idx)
            cqa, cqb, cqc = st.columns([1, 1, 2])
            with cqa:
                if st.button("✅ Importar seleccionados", key="importar_cola"):
                    total = 0
                    nueva_cola = []
                    for idx, queued in enumerate(st.session_state["import_queue"]):
                        if idx in seleccionados:
                            q = dict(queued)
                            if lote_tag.strip(): q["etiquetas"] = (q.get("etiquetas") or "") + ", " + lote_tag.strip()
                            guardar_importado(q, q.get("tipo") or _opciones_tipo(q.get("kind") or kind)[0], lote_estado); total += 1
                        else:
                            nueva_cola.append(queued)
                    st.session_state["import_queue"] = nueva_cola; st.success(f"Importados desde la cola: {total}")
            with cqb:
                if st.button("🗑️ Vaciar cola", key="vaciar_cola"): st.session_state["import_queue"] = []; st.success("Cola vaciada.")

    if not results:
        st.info("Busca una obra. Si no aparece, usa Importar link o Agregar manual."); return

    st.success(f"Resultados encontrados: {len(results)}")
    grupos = sorted(set([r.get("grupo_resultado") or r.get("fuente_importacion") or "Otros" for r in results]))
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Resultados", len(results)); col_r2.metric("Con portada", sum(1 for r in results if r.get("portada_path"))); col_r3.metric("Con sinopsis", sum(1 for r in results if r.get("sinopsis"))); col_r4.metric("Calidad promedio", f"{int(sum(_calidad_100(r) for r in results)/max(1,len(results)))}")

    with st.expander("🎛️ Filtros rápidos y orden", expanded=True):
        filtro_grupo = st.multiselect("Fuentes / grupos", grupos, default=grupos, key="buscador_filtro_grupo")
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        with col_f1: solo_portada = st.checkbox("Solo con portada", key="filtro_portada")
        with col_f2: solo_sinopsis = st.checkbox("Solo con sinopsis", key="filtro_sinopsis")
        with col_f3: min_calidad = st.slider("Calidad mínima", 0, 100, 0, 10, key="filtro_calidad_min")
        with col_f4: ocultar_duplicados = st.checkbox("Ocultar duplicados", key="filtro_dupes")
        with col_f5: solo_favoritos = st.checkbox("Solo favoritos ❤️", key="filtro_favoritos")
        col_f6, col_f7, col_f8 = st.columns(3)
        with col_f6: solo_url = st.checkbox("Solo con URL", key="filtro_url")
        with col_f7: solo_caps = st.checkbox("Solo con capítulos", key="filtro_caps")
        with col_f8: relevancia_min = st.slider("Relevancia mínima", 0, 100, 0, 5, key="filtro_relevancia")
        ordenar = st.selectbox("Ordenar", ["Relevancia primero", "Calidad de datos", "Favoritos primero", "Fuente", "Título A-Z"], key="orden_resultados")

    filtered = []
    favoritos = st.session_state["result_favorites"]
    for r in results:
        grupo = r.get("grupo_resultado") or r.get("fuente_importacion") or "Otros"; duplicados_tmp = _detectar_duplicados_detallado(r, obras); key = _item_key(r)
        if grupo not in filtro_grupo: continue
        if solo_portada and not r.get("portada_path"): continue
        if solo_sinopsis and not r.get("sinopsis"): continue
        if solo_url and not (r.get("url_fuente") or r.get("link_original")): continue
        if solo_caps and _safe_int(r.get("capitulo_total") or r.get("capitulos_publicados"), 0) <= 0: continue
        if _calidad_100(r) < min_calidad: continue
        if int(_relevancia(r, query_actual) * 100) < relevancia_min: continue
        if ocultar_duplicados and duplicados_tmp: continue
        if solo_favoritos and key not in favoritos: continue
        filtered.append(r)

    if ordenar == "Relevancia primero": filtered.sort(key=lambda x: (_relevancia(x, query_actual), _calidad_100(x)), reverse=True)
    elif ordenar == "Calidad de datos": filtered.sort(key=lambda x: _calidad_100(x), reverse=True)
    elif ordenar == "Favoritos primero": filtered.sort(key=lambda x: (_item_key(x) in favoritos, _relevancia(x, query_actual), _calidad_100(x)), reverse=True)
    elif ordenar == "Fuente": filtered.sort(key=lambda x: (x.get("grupo_resultado") or x.get("fuente_importacion") or "", x.get("titulo") or ""))
    else: filtered.sort(key=lambda x: (x.get("titulo") or "").lower())

    st.caption(f"Mostrando {len(filtered)} de {len(results)} resultados después de filtros.")

    for i, item in enumerate(filtered):
        item = _normalizar_item(item, item.get("fuente_importacion") or fuente_actual, item.get("kind") or kind)
        item = _aplicar_defaults(item, defaults)
        titulo_original = item.get("titulo", ""); duplicados_info = _detectar_duplicados_detallado(item, obras); item_kind = item.get("kind") or kind; key = _item_key(item); is_fav = key in st.session_state["result_favorites"] or bool(item.get("favorito")); calidad = _calidad_100(item)
        tipo_sugerido = _tipo_sugerido(item, item_kind)
        if vista == "Compacta":
            st.write(f"**{titulo_original or 'Sin título'}** · {tipo_sugerido} · calidad {calidad}/100 · T{item.get('temporada_actual')}/{item.get('temporada_total')}")
        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 4])
        with col1:
            if item.get("portada_path"): st.image(item.get("portada_path"), use_container_width=True)
            else: st.write("Sin portada")
        with col2:
            st.markdown(f"### {titulo_original or 'Sin título'}")
            st.markdown(f"<div class='score-line'>Calidad de datos: {calidad}/100 · Tipo sugerido: {tipo_sugerido}</div>", unsafe_allow_html=True)
            st.markdown(_quality_html(item, duplicados_info, query_actual, is_fav), unsafe_allow_html=True)
            st.caption(f"Grupo: {item.get('grupo_resultado') or item.get('fuente_importacion') or fuente_actual}")
            st.caption(f"{item.get('division_obra') or 'Temporada'}: T{item.get('temporada_actual') or 1} de {item.get('temporada_total') or 1}")
            if _is_ao3(item.get("url_fuente")):
                st.info(f"Detectado AO3 · Work ID: {_ao3_work_id(item.get('url_fuente'))}. Se guarda metadata/link, no capítulos completos.")
            st.write(item.get("autor") or "Autor / canal no indicado")
            if item.get("sinopsis") and vista != "Compacta": st.write(str(item.get("sinopsis"))[:700])
            if item.get("url_fuente"): st.caption(f"URL fuente: {item.get('url_fuente')}")
        if duplicados_info:
            top = duplicados_info[0]
            st.warning(f"Duplicado probable: {top['score']}% · {top['obra'].get('titulo', 'Sin título')} · motivos: {', '.join(top['motivos'])}")
            with st.expander("Ver posibles duplicados / acciones", expanded=False):
                for d in duplicados_info:
                    st.write(f"{d['score']}% — {d['obra'].get('titulo', 'Sin título')} — {', '.join(d['motivos'])}")
                st.caption("Acción disponible ahora: importar como nueva o usar los datos para editar la obra existente manualmente en Biblioteca/Exportar. La fusión automática queda preparada visualmente para no romper datos existentes.")

        col_heart, col_fast, col_queue = st.columns([1, 1, 1])
        with col_heart:
            if st.button("❤️ Quitar fav" if is_fav else "🤍 Favorito", key=f"heart_{i}"):
                if is_fav and key in st.session_state["result_favorites"]: st.session_state["result_favorites"].remove(key); st.success("Quitado de favoritos.")
                else: st.session_state["result_favorites"].append(key); st.success("Marcado como favorito.")
        with col_fast:
            if st.button("⚡ Importar rápido", key=f"quick_import_{i}"):
                item_fast = dict(item); item_fast["tipo"] = tipo_sugerido; item_fast["favorito"] = 1 if is_fav else int(default_fav)
                guardar_importado(item_fast, tipo_sugerido, estado_import); st.success(f"Importado rápido: {titulo_original}")
        with col_queue:
            if st.button("➕ Añadir a cola", key=f"queue_import_{i}"):
                exists = any((q.get("titulo") == item.get("titulo") and q.get("fuente_importacion") == item.get("fuente_importacion")) for q in st.session_state["import_queue"])
                if not exists:
                    qitem = dict(item); qitem["tipo"] = tipo_sugerido; st.session_state["import_queue"].append(qitem); st.success("Añadido a la cola.")
                else: st.info("Ya estaba en la cola.")

        with st.expander("✏️ Revisar / editar antes de importar"):
            st.markdown("#### 1. Datos principales")
            tipo_opts = _opciones_tipo(item_kind)
            if tipo_sugerido not in tipo_opts: tipo_opts = [tipo_sugerido] + tipo_opts
            col_a, col_b = st.columns(2)
            with col_a:
                titulo_edit = st.text_input("Título", value=item.get("titulo", ""), key=f"imp_titulo_{i}"); autor_edit = st.text_input("Autor / creador", value=item.get("autor", ""), key=f"imp_autor_{i}"); tipo_edit = st.selectbox("Tipo", tipo_opts, index=tipo_opts.index(tipo_sugerido) if tipo_sugerido in tipo_opts else 0, key=f"imp_tipo_{i}"); anio_edit = st.text_input("Año", value=str(item.get("anio") or ""), key=f"imp_anio_{i}")
            with col_b:
                estado_edit = st.selectbox("Estado personal", ESTADOS, index=ESTADOS.index(estado_import) if estado_import in ESTADOS else 0, key=f"imp_estado_{i}"); estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION, index=6, key=f"imp_estado_pub_{i}"); fecha_pub = st.text_input("Fecha de publicación", value=item.get("fecha_publicacion") or item.get("anio") or "", key=f"imp_fecha_pub_{i}"); fuente_edit = st.text_input("Fuente importación", value=item.get("fuente_importacion") or fuente_actual, key=f"imp_fuente_{i}")
            st.markdown("#### 2. Temporadas, progreso inicial y opinión")
            col_t0, col_t1, col_t2 = st.columns(3)
            with col_t0: division_obra = st.selectbox("Tipo de división", DIVISIONES_OBRA, index=DIVISIONES_OBRA.index(item.get("division_obra", "Temporada")) if item.get("division_obra", "Temporada") in DIVISIONES_OBRA else 0, key=f"imp_division_{i}")
            with col_t1: temporada_actual = st.number_input("Temporada/arco actual", min_value=1, value=max(1, _safe_int(item.get("temporada_actual"), 1)), step=1, key=f"imp_temporada_actual_{i}")
            with col_t2: temporada_total = st.number_input("Temporadas/arcos totales", min_value=1, value=max(1, _safe_int(item.get("temporada_total"), 1)), step=1, key=f"imp_temporada_total_{i}")
            col_c, col_d, col_e = st.columns(3)
            with col_c: capitulos_total = st.number_input("Capítulos / episodios publicados", min_value=0, value=_safe_int(item.get("capitulo_total"), _safe_int(item.get("capitulos_publicados"), 0)), step=1, key=f"imp_caps_{i}")
            with col_d: capitulos_vistos = st.number_input("Capítulos / episodios ya vistos/leídos", min_value=0, value=_safe_int(item.get("capitulos_vistos", item.get("capitulo_actual")), 0), step=1, key=f"imp_caps_vistos_{i}")
            with col_e: estrellas_personales = st.slider("Tu puntuación ⭐", 0, 5, _safe_int(item.get("estrellas"), 0), 1, key=f"imp_estrellas_{i}")
            st.markdown("#### 3. Calidad de datos y fuente")
            _render_quality_breakdown(item)
            portada_edit = st.text_input("URL portada", value=item.get("portada_path", ""), key=f"imp_portada_{i}"); etiquetas_edit = st.text_input("Etiquetas", value=item.get("etiquetas", "importado"), key=f"imp_tags_{i}"); url_fuente_edit = st.text_input("URL / link fuente", value=item.get("url_fuente", ""), key=f"imp_url_{i}"); sinopsis_edit = st.text_area("Sinopsis", value=item.get("sinopsis", ""), height=160, key=f"imp_sinopsis_{i}")
            st.markdown("#### 4. Fanfiction / AO3 / canon")
            activar_ao3 = st.checkbox("🔔 Activar seguimiento AO3 si el link es AO3", value=_is_ao3(url_fuente_edit), key=f"imp_ao3_tracking_{i}")
            fanfic_extra = _render_fanfic_extra(f"imp_fanfic_{i}", {**item, "url_fuente": url_fuente_edit}, tipo_edit)
            st.markdown("#### 5. Confirmación")
            st.info(f"Se importará como **{tipo_edit}**, estado **{estado_edit}**, {division_obra.lower()} **T{int(temporada_actual)} de {int(temporada_total)}**, progreso {int(capitulos_vistos)} / {int(capitulos_total)} y tu puntuación personal ⭐ {estrellas_personales}/5. Calidad de datos: {calidad}/100.")
            accion = st.radio("Acción", ["Importar como nueva", "Preparar actualización de existente"], horizontal=True, key=f"imp_accion_{i}")
            if accion == "Preparar actualización de existente" and duplicados_info:
                st.caption("Modo seguro: se muestra la coincidencia para revisar, pero no se fusiona automáticamente para evitar pérdida de datos.")
                st.write(f"Obra sugerida: {duplicados_info[0]['obra'].get('titulo')}")
            if st.button("✅ Confirmar importación revisada", key=f"import_edit_{i}"):
                item_editado = dict(item)
                item_editado.update({"titulo": titulo_edit.strip(), "autor": autor_edit.strip(), "tipo": tipo_edit, "anio": anio_edit.strip(), "fecha_publicacion": fecha_pub.strip(), "estado_publicacion": estado_pub, "division_obra": division_obra, "temporada_actual": int(temporada_actual), "temporada_total": int(max(temporada_total, temporada_actual)), "sinopsis": sinopsis_edit.strip(), "portada_path": portada_edit.strip(), "etiquetas": etiquetas_edit.strip(), "capitulo_total": int(capitulos_total), "capitulos_publicados": int(capitulos_total), "capitulos_vistos": int(capitulos_vistos), "capitulo_actual": int(capitulos_vistos), "estrellas": int(estrellas_personales), "favorito": 1 if is_fav else 0, "fuente_importacion": fuente_edit.strip(), "url_fuente": url_fuente_edit.strip(), "link_original": url_fuente_edit.strip(), "ao3_tracking": 1 if activar_ao3 and _is_ao3(url_fuente_edit) else 0, "ao3_work_id": _ao3_work_id(url_fuente_edit)})
                item_editado.update(fanfic_extra)
                guardar_importado(item_editado, tipo_edit, estado_edit); st.success(f"Importado revisado: {titulo_edit}")
        st.markdown("</div>", unsafe_allow_html=True); st.divider()
