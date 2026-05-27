from __future__ import annotations

import re

import streamlit as st

from src.pages.fanfiction import render_fanfiction_fields

DIVISIONES_OBRA = ["Temporada", "Arco", "Volumen", "Parte", "Libro", "Saga"]
ESTADOS = ["Pendiente", "Leyendo", "Viendo", "Terminado", "Pausado", "Abandonado", "Releyendo", "Rewatch"]
ESTADOS_PUBLICACION = ["En emision", "Terminada", "Hiatus con aviso", "Hiatus sin aviso", "Cancelada", "Abandonada por autor", "No aplica"]
TIPOS_LINK = ["Webnovel", "Novela ligera", "Manhwa", "Manga", "Manhua", "Fanfiction", "Libro", "Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Otro"]


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _ao3_work_id(url):
    match = re.search(r"archiveofourown\.org/works/(\d+)", str(url or ""))
    return match.group(1) if match else ""


def _detect_source(url):
    raw = str(url or "").strip()
    u = raw.lower()
    if "archiveofourown.org/works/" in u:
        return {"fuente": "AO3", "tipo": "Fanfiction", "fanfic": True, "ao3": True, "confiabilidad": 95}
    if "wattpad.com" in u:
        return {"fuente": "Wattpad", "tipo": "Fanfiction", "fanfic": True, "ao3": False, "confiabilidad": 75}
    if "fanfiction.net" in u:
        return {"fuente": "FanFiction.net", "tipo": "Fanfiction", "fanfic": True, "ao3": False, "confiabilidad": 80}
    if "royalroad.com" in u:
        return {"fuente": "RoyalRoad", "tipo": "Webnovel", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "novelupdates.com" in u:
        return {"fuente": "NovelUpdates", "tipo": "Novela ligera", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "webnovel.com" in u:
        return {"fuente": "Webnovel", "tipo": "Webnovel", "fanfic": False, "ao3": False, "confiabilidad": 75}
    if "mangadex.org" in u:
        return {"fuente": "MangaDex", "tipo": "Manga", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "myanimelist.net" in u:
        tipo = "Manga" if "/manga/" in u else "Anime"
        return {"fuente": "MyAnimeList", "tipo": tipo, "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "imdb.com" in u:
        return {"fuente": "IMDb", "tipo": "Pelicula", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "themoviedb.org" in u or "tmdb" in u:
        return {"fuente": "TMDB", "tipo": "Serie", "fanfic": False, "ao3": False, "confiabilidad": 90}
    if "openlibrary.org" in u:
        return {"fuente": "OpenLibrary", "tipo": "Libro", "fanfic": False, "ao3": False, "confiabilidad": 80}
    if "goodreads.com" in u:
        return {"fuente": "Goodreads", "tipo": "Libro", "fanfic": False, "ao3": False, "confiabilidad": 70}
    return {"fuente": "Link externo", "tipo": "Webnovel", "fanfic": False, "ao3": False, "confiabilidad": 50}


def _quality(item):
    checks = [
        ("Título", 15, bool(item.get("titulo"))),
        ("Autor", 15, bool(item.get("autor"))),
        ("Sinopsis", 20, bool(item.get("sinopsis"))),
        ("Portada", 15, bool(item.get("portada_path"))),
        ("URL", 15, bool(item.get("url_fuente") or item.get("link_original"))),
        ("Capítulos", 10, _safe_int(item.get("capitulo_total") or item.get("capitulos_publicados"), 0) > 0),
        ("Fuente detectada", 10, bool(item.get("fuente_importacion"))),
    ]
    return sum(points for _, points, ok in checks if ok), checks


def _find_duplicates(url, titulo, autor, obras):
    url_norm = str(url or "").strip().lower()
    title_norm = str(titulo or "").strip().lower()
    author_norm = str(autor or "").strip().lower()
    ao3 = _ao3_work_id(url_norm)
    matches = []
    for obra in obras or []:
        score = 0
        motivos = []
        obra_url = str(obra.get("link_original") or "").strip().lower()
        obra_title = str(obra.get("titulo") or "").strip().lower()
        obra_author = str(obra.get("autor") or "").strip().lower()
        if url_norm and obra_url and url_norm == obra_url:
            score += 100; motivos.append("mismo link")
        if ao3 and ao3 == _ao3_work_id(obra_url):
            score += 100; motivos.append("mismo AO3 work ID")
        if title_norm and obra_title:
            ratio = 1 if title_norm == obra_title else 0
            if title_norm in obra_title or obra_title in title_norm:
                ratio = max(ratio, 0.85)
            if ratio >= 0.85:
                score += int(ratio * 60); motivos.append("título parecido")
        if author_norm and obra_author and author_norm == obra_author:
            score += 20; motivos.append("mismo autor")
        if score:
            matches.append({"obra": obra, "score": min(100, score), "motivos": motivos})
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]


def _render_quality(item):
    score, checks = _quality(item)
    st.markdown(f"**Calidad de datos: {score}/100**")
    for label, points, ok in checks:
        st.write(f"{'✅' if ok else '⚠️'} {label}: {'+' + str(points) if ok else '+0'}")
    return score


def _build_item(base, detected, edits, fanfic_data):
    item = dict(base or {})
    item.update(edits)
    item.update(fanfic_data or {})
    item["fuente_importacion"] = detected["fuente"]
    item["fuente_confiabilidad"] = detected["confiabilidad"]
    item["ao3_work_id"] = _ao3_work_id(item.get("url_fuente"))
    item["link_original"] = item.get("url_fuente")
    item["calidad_datos"] = _quality(item)[0]
    if detected["ao3"]:
        item["fuente_fanfic"] = "AO3"
    return item


def render_importar_link(obras, importar_desde_link, guardar_importado, save_uploaded_file, portadas_dir):
    st.subheader("🔗 Importar desde link")
    st.caption("Importador avanzado con detección de fuente, AO3, fanfiction/canon, temporadas, duplicados, calidad 0/100 e importación múltiple.")

    tab_one, tab_many = st.tabs(["Un link", "Varios links"])

    with tab_one:
        url = st.text_input("Link de la obra", key="link_single_url")
        detected = _detect_source(url)
        st.info(f"Fuente detectada: **{detected['fuente']}** · Tipo sugerido: **{detected['tipo']}** · Confiabilidad: **{detected['confiabilidad']}/100**")
        if detected["ao3"]:
            st.success(f"AO3 detectado · Work ID: {_ao3_work_id(url)} · Solo se guardará metadata pública/link, no capítulos completos.")

        if st.button("Detectar metadata desde link", key="link_detect_metadata"):
            if not url.strip():
                st.error("Pega un link primero.")
            else:
                try:
                    st.session_state["link_metadata"] = importar_desde_link(url.strip())
                    st.success("Metadata detectada. Revísala antes de importar.")
                except Exception as exc:
                    st.session_state["link_metadata"] = {"titulo": "", "autor": "", "sinopsis": "", "url_fuente": url.strip(), "link_original": url.strip()}
                    st.warning(f"No se pudo leer metadata automática. Puedes completar manualmente. Detalle: {exc}")

        base = st.session_state.get("link_metadata", {}) or {}
        if url.strip():
            base.setdefault("url_fuente", url.strip())
            base.setdefault("link_original", url.strip())

        st.markdown("### Revisar antes de importar")
        col_a, col_b = st.columns(2)
        with col_a:
            titulo = st.text_input("Título", value=base.get("titulo", ""), key="link_titulo")
            autor = st.text_input("Autor / creador", value=base.get("autor", ""), key="link_autor")
            tipo_index = TIPOS_LINK.index(detected["tipo"]) if detected["tipo"] in TIPOS_LINK else 0
            tipo = st.selectbox("Tipo", TIPOS_LINK, index=tipo_index, key="link_tipo")
            estado = st.selectbox("Estado personal", ESTADOS, index=0, key="link_estado")
            favorito = st.checkbox("Marcar como favorito", key="link_favorito")
            estrellas = st.slider("Tu puntuación personal ⭐", 0, 5, 0, 1, key="link_estrellas")
        with col_b:
            estado_pub = st.selectbox("Estado de publicación", ESTADOS_PUBLICACION, index=0 if detected["ao3"] else 6, key="link_estado_pub")
            fecha_pub = st.text_input("Fecha de publicación", value=base.get("fecha_publicacion", ""), key="link_fecha_pub")
            division = st.selectbox("Tipo de división", DIVISIONES_OBRA, key="link_division")
            temporada_actual = st.number_input("Temporada/arco actual", min_value=1, value=1, step=1, key="link_temp_actual")
            temporada_total = st.number_input("Temporadas/arcos totales", min_value=1, value=1, step=1, key="link_temp_total")
            ao3_tracking = st.checkbox("Activar seguimiento AO3", value=detected["ao3"], disabled=not detected["ao3"], key="link_ao3_tracking")

        col_c, col_d, col_e = st.columns(3)
        with col_c:
            caps_publicados = st.number_input("Capítulos publicados", min_value=0, value=_safe_int(base.get("capitulo_total"), 0), step=1, key="link_caps_pub")
        with col_d:
            caps_total = st.number_input("Capítulos totales esperados", min_value=0, value=_safe_int(base.get("capitulo_total"), 0), step=1, key="link_caps_total")
        with col_e:
            caps_vistos = st.number_input("Capítulos vistos/leídos", min_value=0, value=0, step=1, key="link_caps_vistos")

        etiquetas = st.text_input("Etiquetas", value=base.get("etiquetas", "importado, link"), key="link_tags")
        portada_url = st.text_input("URL portada", value=base.get("portada_path", ""), key="link_portada_url")
        portada_upload = st.file_uploader("Subir portada desde tu dispositivo", type=["jpg", "jpeg", "png", "webp"], key="link_portada_upload")
        sinopsis = st.text_area("Sinopsis / descripción", value=base.get("sinopsis", ""), height=180, key="link_sinopsis")

        fanfic_data = {}
        if tipo == "Fanfiction" or detected["fanfic"]:
            st.markdown("### Fanfiction / canon / crossover")
            fanfic_data = render_fanfiction_fields(prefix="link_fanfic")

        portada_subida_path = ""
        if portada_upload is not None:
            portada_subida_path = save_uploaded_file(portada_upload, portadas_dir)

        edits = {
            "titulo": titulo.strip(),
            "autor": autor.strip(),
            "tipo": tipo,
            "estado_publicacion": estado_pub,
            "fecha_publicacion": fecha_pub.strip(),
            "division_obra": division,
            "temporada_actual": int(temporada_actual),
            "temporada_total": int(max(temporada_total, temporada_actual)),
            "capitulo_total": int(caps_total or caps_publicados),
            "capitulos_publicados": int(caps_publicados or caps_total),
            "capitulos_vistos": int(caps_vistos),
            "capitulo_actual": int(caps_vistos),
            "estrellas": int(estrellas),
            "favorito": 1 if favorito else 0,
            "sinopsis": sinopsis.strip(),
            "etiquetas": etiquetas.strip(),
            "url_fuente": url.strip(),
            "link_original": url.strip(),
            "portada_path": portada_subida_path or portada_url.strip(),
            "ao3_tracking": 1 if ao3_tracking and detected["ao3"] else 0,
        }
        item_preview = _build_item(base, detected, edits, fanfic_data)

        st.markdown("### Calidad, duplicados y confirmación")
        quality = _render_quality(item_preview)
        dupes = _find_duplicates(url, titulo, autor, obras)
        if dupes:
            st.warning(f"Posibles duplicados encontrados: {len(dupes)}")
            for d in dupes:
                st.write(f"{d['score']}% · {d['obra'].get('titulo')} · {', '.join(d['motivos'])}")
        else:
            st.success("No se detectaron duplicados exactos por link/AO3/título+autor.")

        st.info(f"Se importará como **{tipo}**, estado **{estado}**, {division.lower()} **T{int(temporada_actual)} de {int(max(temporada_total, temporada_actual))}**, progreso **{int(caps_vistos)} / {int(caps_publicados or caps_total)}**, calidad **{quality}/100**.")
        if st.button("✅ Confirmar importación desde link", key="link_confirm_import"):
            if not url.strip():
                st.error("El link es obligatorio.")
            elif not titulo.strip():
                st.error("El título es obligatorio antes de importar.")
            elif caps_vistos > max(caps_publicados, caps_total) and max(caps_publicados, caps_total) > 0:
                st.error("Los capítulos vistos/leídos no pueden ser mayores que los publicados/totales.")
            else:
                guardar_importado(item_preview, tipo, estado)
                st.success(f"Importado desde link: {titulo}")

    with tab_many:
        st.markdown("### Importar varios links")
        raw_links = st.text_area("Pega varios links, uno por línea", height=180, key="multi_links")
        estado_lote = st.selectbox("Estado para lote", ESTADOS, index=0, key="multi_estado")
        tags_lote = st.text_input("Etiquetas para lote", value="importado, lote", key="multi_tags")
        if st.button("Preparar cola de links", key="multi_prepare"):
            links = [line.strip() for line in raw_links.splitlines() if line.strip()]
            queue = []
            for link in links:
                detected_multi = _detect_source(link)
                queue.append({
                    "url_fuente": link,
                    "link_original": link,
                    "titulo": link.rstrip("/").split("/")[-1] or "Sin título",
                    "autor": "",
                    "tipo": detected_multi["tipo"],
                    "fuente_importacion": detected_multi["fuente"],
                    "fuente_confiabilidad": detected_multi["confiabilidad"],
                    "etiquetas": tags_lote,
                    "ao3_work_id": _ao3_work_id(link),
                    "ao3_tracking": 1 if detected_multi["ao3"] else 0,
                    "temporada_actual": 1,
                    "temporada_total": 1,
                    "capitulo_actual": 0,
                    "capitulo_total": 0,
                    "capitulos_publicados": 0,
                    "capitulos_vistos": 0,
                    "calidad_datos": 30,
                })
            st.session_state["link_batch_queue"] = queue
            st.success(f"Links preparados: {len(queue)}")

        queue = st.session_state.get("link_batch_queue", [])
        if queue:
            st.markdown("### Cola de links")
            selected = []
            for idx, item in enumerate(queue):
                checked = st.checkbox(f"{idx + 1}. {item.get('titulo')} · {item.get('fuente_importacion')} · {item.get('tipo')}", value=True, key=f"multi_select_{idx}")
                if checked:
                    selected.append(idx)
            if st.button("✅ Importar links seleccionados", key="multi_import"):
                total = 0
                for idx, item in enumerate(queue):
                    if idx in selected:
                        guardar_importado(item, item.get("tipo") or "Webnovel", estado_lote)
                        total += 1
                st.success(f"Importados desde lote: {total}")
                st.session_state["link_batch_queue"] = []
