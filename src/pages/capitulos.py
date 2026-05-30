from datetime import date
from pathlib import Path

import streamlit as st

from src.compilador import guardar_compilado
from src.utils import save_uploaded_file, RESPALDOS_DIR


TIPOS_PANTALLA = {"Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"}
TIPOS_LECTURA = {"Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"}


def _leer_archivo_texto(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        return uploaded_file.getvalue().decode("utf-8")
    except Exception:
        try:
            return uploaded_file.getvalue().decode("latin-1")
        except Exception:
            return ""


def _temporadas_existentes(capitulos):
    temporadas = sorted({int(c.get("temporada") or 1) for c in capitulos})
    return temporadas or [1]


def _siguiente_capitulo_temporada(capitulos, temporada):
    nums = [int(c.get("numero") or 0) for c in capitulos if int(c.get("temporada") or 1) == int(temporada)]
    return (max(nums) + 1) if nums else 1


def _tipo_unidad(obra):
    tipo = obra.get("tipo") or ""
    if tipo in TIPOS_PANTALLA:
        return "episodio"
    if tipo == "Pelicula":
        return "parte"
    if tipo in ["Manga", "Manhwa", "Manhua", "Comic"]:
        return "capítulo"
    if tipo == "Fanfiction":
        return "capítulo"
    return "capítulo / episodio"


def _safe_int(value, default=0):
    try:
        if value in [None, ""]:
            return default
        return int(value)
    except Exception:
        return default


def _progreso_texto(obra, capitulos):
    vistos = _safe_int(obra.get("capitulos_vistos") or obra.get("capitulo_actual"), len(capitulos))
    total = _safe_int(obra.get("capitulo_total") or obra.get("capitulos_publicados"), 0)
    if total > 0:
        pct = min(100, round((vistos / total) * 100))
        return f"{vistos}/{total} · {pct}%"
    return f"{len(capitulos)} guardados"


def _guardar_capitulo(add_capitulo, obra_id, temporada, numero, titulo, resumen, texto, notas, mood, etiquetas, estrellas, fecha_lectura, archivo):
    archivo_path = save_uploaded_file(archivo, RESPALDOS_DIR)
    return add_capitulo({
        "obra_id": obra_id,
        "temporada": int(temporada),
        "numero": int(numero),
        "titulo": titulo.strip(),
        "sinopsis": resumen.strip(),
        "notas": notas.strip(),
        "comentario": notas.strip(),
        "etiquetas": etiquetas.strip(),
        "mood": mood.strip(),
        "frases_favoritas": "",
        "estrellas": int(estrellas),
        "favorito": 0,
        "estado": "Leido",
        "texto_completo": texto.strip(),
        "archivo_path": archivo_path,
        "rating": float(estrellas),
        "visto_leido": 1,
        "fecha_lectura": str(fecha_lectura),
    })


def _render_obra_resumen(obra, capitulos, temporadas, unidad):
    estado = obra.get("estado_lectura") or "Sin estado"
    tipo = obra.get("tipo") or "Obra"
    progreso = _progreso_texto(obra, capitulos)
    ultimo = max([_safe_int(c.get("numero"), 0) for c in capitulos], default=0)
    st.markdown(
        f"""
        <div class="pm-wide-card">
            <div>
                <div class="pm-mini-title">{obra.get('titulo') or 'Sin título'}</div>
                <div class="pm-mini-subtitle">{tipo} · {estado} · Progreso: {progreso}</div>
            </div>
            <div class="pm-mini-icon">📝</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temporadas/arcos", len(temporadas))
    c2.metric(f"{unidad.capitalize()}s", len(capitulos))
    c3.metric("Último", ultimo)
    c4.metric("Guardado", progreso)


def _render_temporadas_resumen(capitulos, temporadas, unidad):
    st.markdown("### 🗂️ Resumen por temporadas / arcos")
    if not capitulos:
        st.info("Aún no hay capítulos, episodios o partes guardadas para resumir.")
        return
    cols = st.columns(min(4, max(1, len(temporadas))))
    for idx, temp in enumerate(temporadas):
        caps_temp = [c for c in capitulos if int(c.get("temporada") or 1) == int(temp)]
        vistos = len(caps_temp)
        ultimo = max([int(c.get("numero") or 0) for c in caps_temp], default=0)
        estrellas = [float(c.get("estrellas") or c.get("rating") or 0) for c in caps_temp if float(c.get("estrellas") or c.get("rating") or 0) > 0]
        promedio = round(sum(estrellas) / len(estrellas), 1) if estrellas else 0
        with cols[idx % len(cols)]:
            st.metric(f"Temporada / arco {temp}", f"{vistos} {unidad}s", f"Último: {ultimo} · ★ {promedio}")


def _render_ultimos_capitulos(capitulos, unidad):
    if not capitulos:
        return
    st.markdown("### 🕒 Últimos registros")
    ultimos = sorted(capitulos, key=lambda c: str(c.get("created_at") or c.get("fecha_lectura") or ""), reverse=True)[:5]
    for cap in ultimos:
        titulo = cap.get("titulo") or "Sin título"
        temp = cap.get("temporada") or 1
        num = cap.get("numero") or 0
        fecha = cap.get("fecha_lectura") or "Sin fecha"
        mood = cap.get("mood") or "Sin mood"
        st.markdown(
            f"""
            <div class="pm-mini-card">
                <div>
                    <div class="pm-mini-title">T{temp} · {unidad.capitalize()} {num}: {titulo}</div>
                    <div class="pm-mini-subtitle">{fecha} · {mood}</div>
                </div>
                <div class="pm-mini-icon">★{cap.get('estrellas') or 0}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _filtrar_capitulos(capitulos, temporada_filtro, busqueda, solo_con_texto, solo_con_notas):
    filtrados = list(capitulos or [])
    if temporada_filtro != "Todas":
        filtrados = [c for c in filtrados if int(c.get("temporada") or 1) == int(temporada_filtro)]
    if busqueda.strip():
        q = busqueda.strip().lower()
        filtrados = [
            c for c in filtrados
            if q in str(c.get("titulo") or "").lower()
            or q in str(c.get("sinopsis") or "").lower()
            or q in str(c.get("notas") or c.get("comentario") or "").lower()
            or q in str(c.get("etiquetas") or "").lower()
            or q in str(c.get("mood") or "").lower()
        ]
    if solo_con_texto:
        filtrados = [c for c in filtrados if bool(c.get("texto_completo"))]
    if solo_con_notas:
        filtrados = [c for c in filtrados if bool(c.get("notas") or c.get("comentario"))]
    return filtrados


def _render_personajes(obra_id, capitulos, list_personajes, add_personaje, add_voto_personaje, list_votos_personaje, save_uploaded_file_fn, imagenes_dir):
    if not all([list_personajes, add_personaje, add_voto_personaje, list_votos_personaje]):
        st.info("Personajes todavía no están conectados en esta instalación.")
        return

    personajes = list_personajes(obra_id)
    votos = list_votos_personaje(obra_id)

    st.markdown("### 🎭 Personajes para no perderme")
    st.caption("Guarda foto, rol, descripción y evolución. Estos datos quedan listos para Wrapped: personaje favorito, más importante, más mencionado, mejor evolución y momentos clave.")

    with st.expander("➕ Crear ficha de personaje", expanded=False):
        with st.form(f"form_personaje_{obra_id}"):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre del personaje", key=f"pj_nombre_{obra_id}")
                alias = st.text_input("Alias / apodo / otro nombre", key=f"pj_alias_{obra_id}")
                rol = st.text_input("Rol", placeholder="protagonista, villano, interés amoroso, mentor...", key=f"pj_rol_{obra_id}")
                favorito = st.checkbox("Marcar como favorito", key=f"pj_fav_{obra_id}")
            with c2:
                imagen_url = st.text_input("URL de imagen / foto", key=f"pj_img_url_{obra_id}")
                imagen_file = st.file_uploader("O subir imagen", type=["jpg", "jpeg", "png", "webp"], key=f"pj_img_file_{obra_id}")
            descripcion = st.text_area("Descripción para reconocerlo", placeholder="Apariencia, personalidad, relación con otros, cómo identificarlo rápido...", key=f"pj_desc_{obra_id}")
            notas = st.text_area("Notas para Wrapped / evolución", placeholder="Primera impresión, sospechas, arco, traumas, ships, red flags, comfort...", key=f"pj_notas_{obra_id}")
            if st.form_submit_button("Guardar personaje"):
                if not nombre.strip():
                    st.error("El nombre del personaje es obligatorio.")
                else:
                    imagen_path = ""
                    if imagen_file is not None and save_uploaded_file_fn and imagenes_dir:
                        imagen_path = save_uploaded_file_fn(imagen_file, imagenes_dir)
                    add_personaje({
                        "obra_id": obra_id,
                        "nombre": nombre.strip(),
                        "alias": alias.strip(),
                        "rol": rol.strip(),
                        "descripcion": descripcion.strip(),
                        "notas": notas.strip(),
                        "imagen_path": imagen_path or imagen_url.strip(),
                        "favorito": 1 if favorito else 0,
                    })
                    st.success(f"Personaje guardado: {nombre.strip()}")

    personajes = list_personajes(obra_id)
    if personajes:
        cols = st.columns(2)
        for idx, pj in enumerate(personajes[:8]):
            with cols[idx % 2]:
                st.markdown(f"**{'⭐ ' if int(pj.get('favorito') or 0) else ''}{pj.get('nombre')}**")
                if pj.get("imagen_path"):
                    st.image(pj.get("imagen_path"), width=110)
                st.caption(f"{pj.get('rol') or 'Sin rol'} · {pj.get('alias') or 'Sin alias'}")
                if pj.get("descripcion"):
                    st.write(pj.get("descripcion"))
                if pj.get("notas"):
                    st.info(pj.get("notas"))
    else:
        st.warning("Aún no hay personajes guardados para esta obra.")

    if capitulos and personajes:
        with st.expander("📌 Registrar aparición / momento clave por capítulo", expanded=False):
            with st.form(f"form_voto_personaje_{obra_id}"):
                cap_opts = {f"T{c.get('temporada') or 1} · {c.get('numero') or 0} — {c.get('titulo') or 'Sin título'}": c.get("id") for c in capitulos}
                pj_opts = {f"{p.get('nombre')} ({p.get('rol') or 'sin rol'})": p.get("id") for p in personajes}
                cap_sel = st.selectbox("Capítulo / episodio / parte", list(cap_opts.keys()), key=f"voto_cap_{obra_id}")
                pj_sel = st.selectbox("Personaje", list(pj_opts.keys()), key=f"voto_pj_{obra_id}")
                puntos = st.slider("Importancia del momento", 1, 5, 3, key=f"voto_pts_{obra_id}")
                comentario = st.text_area("Momento clave / evolución / confusión / teoría", placeholder="Qué hizo, por qué importa, cómo cambió, si me confundí con él/ella...", key=f"voto_com_{obra_id}")
                fecha_voto = st.date_input("Fecha", value=date.today(), key=f"voto_fecha_{obra_id}")
                if st.form_submit_button("Guardar momento del personaje"):
                    add_voto_personaje({
                        "obra_id": obra_id,
                        "capitulo_id": cap_opts[cap_sel],
                        "personaje_id": pj_opts[pj_sel],
                        "fecha": str(fecha_voto),
                        "puntos": int(puntos),
                        "comentario": comentario.strip(),
                    })
                    st.success("Momento de personaje guardado para Wrapped.")

    votos = list_votos_personaje(obra_id)
    if votos:
        st.markdown("### 🧠 Momentos de personajes registrados")
        for voto in votos[:8]:
            st.markdown(
                f"""
                <div class="pm-mini-card">
                    <div>
                        <div class="pm-mini-title">{voto.get('nombre') or 'Personaje'} · T{voto.get('temporada') or '?'} {voto.get('numero') or ''}</div>
                        <div class="pm-mini-subtitle">Importancia {voto.get('puntos') or 1}/5 · {voto.get('comentario') or 'Sin comentario'}</div>
                    </div>
                    <div class="pm-mini-icon">🎭</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_capitulos(
    obras,
    list_capitulos,
    get_obra,
    add_capitulo=None,
    list_personajes=None,
    add_personaje=None,
    add_voto_personaje=None,
    list_votos_personaje=None,
    save_uploaded_file_fn=None,
    imagenes_dir=None,
):
    st.subheader("📝 Capítulos, episodios, partes, personajes y compilado")
    st.caption("Registra avances por temporada, arco o parte. Mantiene texto completo, notas, archivos, carga masiva, personajes con foto y compilado automático.")

    if not obras:
        st.info("Agrega una obra primero.")
        return

    opciones = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o['id'] for o in obras}

    seleccion = st.selectbox("Selecciona una obra", list(opciones.keys()), key="capitulos_obra")

    obra_id = opciones[seleccion]
    obra = get_obra(obra_id)
    capitulos = list_capitulos(obra_id)
    temporadas = _temporadas_existentes(capitulos)
    temporada_total = int(obra.get("temporada_total") or max(temporadas or [1]) or 1)
    temporada_actual = int(obra.get("temporada_actual") or 1)
    unidad = _tipo_unidad(obra)

    _render_obra_resumen(obra, capitulos, temporadas, unidad)
    _render_temporadas_resumen(capitulos, temporadas, unidad)
    _render_ultimos_capitulos(capitulos, unidad)
    _render_personajes(obra_id, capitulos, list_personajes, add_personaje, add_voto_personaje, list_votos_personaje, save_uploaded_file_fn, imagenes_dir)

    if add_capitulo is None:
        st.warning("La función para agregar capítulos no está conectada todavía.")
    else:
        with st.expander(f"➕ Agregar {unidad} / parte", expanded=True):
            modo = st.radio(
                "Modo de carga",
                ["Un capítulo", "Varios capítulos pegados"],
                horizontal=True,
                key=f"modo_cap_{obra_id}"
            )

            if modo == "Un capítulo":
                with st.form(f"form_capitulo_{obra_id}"):
                    st.markdown("#### Temporada / arco / parte mayor")
                    col0, col1, col2, col3 = st.columns(4)
                    with col0:
                        temporada_modo = st.radio("Temporada", ["Existente", "Nueva"], horizontal=True, key=f"temp_modo_{obra_id}")
                    with col1:
                        if temporada_modo == "Existente":
                            temporada = st.selectbox("Seleccionar temporada", temporadas, index=temporadas.index(temporada_actual) if temporada_actual in temporadas else 0, key=f"temp_select_{obra_id}")
                        else:
                            temporada = st.number_input("Nueva temporada", min_value=1, value=max(temporadas) + 1, step=1, key=f"temp_nueva_{obra_id}")
                    with col2:
                        numero = st.number_input(f"Número de {unidad}", min_value=0, value=_siguiente_capitulo_temporada(capitulos, temporada), step=1, key=f"num_{obra_id}")
                    with col3:
                        fecha_lectura = st.date_input("Fecha leído/visto", value=date.today(), key=f"fecha_{obra_id}")

                    titulo = st.text_input(f"Título del {unidad}", key=f"titulo_cap_{obra_id}")
                    resumen = st.text_area(f"Resumen / sinopsis del {unidad}", key=f"resumen_cap_{obra_id}")
                    texto = st.text_area(f"Texto completo, transcripción o notas largas del {unidad}", height=260, key=f"texto_cap_{obra_id}")
                    archivo = st.file_uploader(f"Archivo del {unidad}", type=["txt", "md", "pdf", "docx", "epub", "zip"], key=f"archivo_cap_{obra_id}")
                    archivo_texto = st.file_uploader("O subir TXT/MD para llenar el texto automáticamente", type=["txt", "md"], key=f"archivo_texto_cap_{obra_id}")
                    texto_archivo = _leer_archivo_texto(archivo_texto)
                    if texto_archivo:
                        st.info("Se detectó texto en el archivo. Se guardará junto al texto pegado.")

                    col4, col5, col6 = st.columns(3)
                    with col4:
                        estrellas = st.slider("Estrellas", 0, 5, 0, key=f"estrellas_cap_{obra_id}")
                    with col5:
                        mood = st.text_input("Mood", placeholder="intenso, cozy, triste, hype...", key=f"mood_cap_{obra_id}")
                    with col6:
                        etiquetas = st.text_input("Etiquetas", placeholder="plot twist, romance, batalla...", key=f"tags_cap_{obra_id}")

                    notas = st.text_area("Comentarios / notas / teorías", key=f"notas_cap_{obra_id}")

                    if st.form_submit_button(f"Guardar {unidad}"):
                        texto_final = (texto or "")
                        if texto_archivo:
                            texto_final = (texto_final + "\n\n" + texto_archivo).strip()
                        _guardar_capitulo(add_capitulo, obra_id, temporada, numero, titulo, resumen, texto_final, notas, mood, etiquetas, estrellas, fecha_lectura, archivo)
                        st.success(f"Registro guardado en Temporada {int(temporada)}. El compilado se actualizará automáticamente al recargar esta pestaña.")

            else:
                st.caption("Pega varios registros separados por una línea que empiece con ###. Ejemplo: ### Capítulo 1 / ### Episodio 1 / ### Parte 1")
                with st.form(f"form_masivo_{obra_id}"):
                    colm1, colm2, colm3 = st.columns(3)
                    with colm1:
                        temporada_modo = st.radio("Temporada", ["Existente", "Nueva"], horizontal=True, key=f"temp_modo_masivo_{obra_id}")
                    with colm2:
                        if temporada_modo == "Existente":
                            temporada = st.selectbox("Seleccionar temporada", temporadas, index=temporadas.index(temporada_actual) if temporada_actual in temporadas else 0, key=f"temp_masivo_select_{obra_id}")
                        else:
                            temporada = st.number_input("Nueva temporada", min_value=1, value=max(temporadas) + 1, step=1, key=f"temp_masivo_nueva_{obra_id}")
                    with colm3:
                        inicio_num = st.number_input("Número inicial", min_value=1, value=_siguiente_capitulo_temporada(capitulos, temporada), step=1, key=f"inicio_masivo_{obra_id}")
                    fecha_lectura = st.date_input("Fecha leído/visto", value=date.today(), key=f"fecha_masivo_{obra_id}")
                    texto_masivo = st.text_area("Capítulos / episodios / partes pegadas", height=360, key=f"texto_masivo_{obra_id}")
                    estrellas = st.slider("Estrellas por defecto", 0, 5, 0, key=f"estrellas_masivo_{obra_id}")
                    mood = st.text_input("Mood por defecto", key=f"mood_masivo_{obra_id}")
                    etiquetas = st.text_input("Etiquetas por defecto", key=f"tags_masivo_{obra_id}")

                    if st.form_submit_button("Guardar varios registros"):
                        bloques = []
                        actual = []
                        for line in texto_masivo.splitlines():
                            if line.strip().startswith("###") and actual:
                                bloques.append("\n".join(actual).strip())
                                actual = [line]
                            else:
                                actual.append(line)
                        if actual:
                            bloques.append("\n".join(actual).strip())

                        guardados = 0
                        for idx, bloque in enumerate([b for b in bloques if b.strip()]):
                            lineas = bloque.splitlines()
                            titulo = lineas[0].replace("###", "").strip() if lineas else f"Registro {int(inicio_num) + idx}"
                            cuerpo = "\n".join(lineas[1:]).strip() if len(lineas) > 1 else bloque
                            _guardar_capitulo(add_capitulo, obra_id, temporada, int(inicio_num) + idx, titulo, "", cuerpo, "", mood, etiquetas, estrellas, fecha_lectura, None)
                            guardados += 1
                        st.success(f"Registros guardados en Temporada {int(temporada)}: {guardados}. El compilado se actualizará automáticamente.")

    capitulos = list_capitulos(obra_id)
    if not capitulos:
        st.warning("Esta obra aún no tiene capítulos, episodios o partes guardadas.")
        return

    path, texto = guardar_compilado(obra, capitulos)

    st.success("Compilado actualizado automáticamente.")

    with st.expander("📖 Vista previa del compilado", expanded=True):
        st.text_area("Contenido compilado", value=texto, height=500, key=f"preview_{obra_id}")

    st.download_button("⬇️ Descargar compilado .md", data=texto.encode("utf-8"), file_name=f"{obra.get('titulo','obra')}_compilado.md", mime="text/markdown")

    st.caption(f"Archivo generado: {path}")

    st.markdown("### Capítulos / episodios / partes guardadas")
    temporadas = _temporadas_existentes(capitulos)
    colf1, colf2, colf3 = st.columns([1, 2, 1])
    with colf1:
        temporada_filtro = st.selectbox("Filtrar temporada", ["Todas"] + temporadas, key=f"filtro_temp_{obra_id}")
    with colf2:
        busqueda = st.text_input("Buscar por título, notas, mood o etiquetas", key=f"buscar_cap_{obra_id}")
    with colf3:
        solo_con_texto = st.checkbox("Con texto", key=f"solo_texto_{obra_id}")
        solo_con_notas = st.checkbox("Con notas", key=f"solo_notas_{obra_id}")

    capitulos_filtrados = _filtrar_capitulos(capitulos, temporada_filtro, busqueda, solo_con_texto, solo_con_notas)
    st.caption(f"Mostrando {len(capitulos_filtrados)} de {len(capitulos)} registros.")

    tabs_temporadas = _temporadas_existentes(capitulos_filtrados)
    tabs = st.tabs([f"T{t}" for t in tabs_temporadas])
    for tab, temp in zip(tabs, tabs_temporadas):
        with tab:
            caps_temp = [c for c in capitulos_filtrados if int(c.get("temporada") or 1) == int(temp)]
            caps_temp = sorted(caps_temp, key=lambda c: int(c.get("numero") or 0))
            st.caption(f"Temporada {temp}: {len(caps_temp)} registros")
            for cap in caps_temp:
                etiqueta = f"T{cap.get('temporada') or 1} · {unidad.capitalize()} {cap.get('numero') or 0}"
                titulo_cap = cap.get("titulo") or "Sin título"
                estrellas_cap = cap.get("estrellas") or cap.get("rating") or 0
                mood_cap = cap.get("mood") or "Sin mood"
                fecha_cap = cap.get("fecha_lectura") or "Sin fecha"
                with st.expander(f"{etiqueta} — {titulo_cap} · ★{estrellas_cap} · {fecha_cap}"):
                    st.caption(f"Mood: {mood_cap} · Etiquetas: {cap.get('etiquetas') or 'Sin etiquetas'}")
                    if cap.get("sinopsis"):
                        st.write(cap.get("sinopsis"))
                    if cap.get("notas") or cap.get("comentario"):
                        st.info(cap.get("notas") or cap.get("comentario"))
                    if cap.get("archivo_path"):
                        st.caption(f"Archivo: {cap.get('archivo_path')}")
                    if cap.get("texto_completo"):
                        st.text_area("Texto guardado", value=cap.get("texto_completo"), height=220, disabled=True, key=f"cap_text_{cap.get('id')}")
