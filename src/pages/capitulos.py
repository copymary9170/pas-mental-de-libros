from datetime import date
import json
from pathlib import Path

import streamlit as st

from src.compilador import guardar_compilado
from src.local_time import today_local
from src.utils import save_uploaded_file, RESPALDOS_DIR


TIPOS_PANTALLA = {"Anime", "Serie", "Kdrama", "Pelicula", "Documental", "Podcast", "Otro"}
TIPOS_LECTURA = {"Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"}
EMOCIONES = ["No aplica", "felicidad", "tristeza", "rabia", "ansiedad", "ternura", "hype", "miedo", "confusión", "comfort", "cringe", "shock", "resaca emocional", "obsesión"]
RITMOS = ["No aplica", "lento", "medio", "rápido", "adictivo", "pesado", "relleno", "montaña rusa"]
CATEGORIAS_WRAPPED = [
    "No aplica",
    "mejor capítulo/episodio",
    "peor capítulo/episodio",
    "más triste",
    "más divertido",
    "más intenso",
    "más confuso",
    "más romántico",
    "más comfort",
    "más cringe",
    "más adictivo",
    "plot twist del año",
    "cliffhanger del año",
    "escena favorita",
    "momento traumático",
    "momento de personaje",
    "relleno",
]


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


def _json(data):
    return json.dumps(data, ensure_ascii=False)


def _select_value(value):
    return "" if value == "No aplica" else value


def _progreso_texto(obra, capitulos):
    vistos = _safe_int(obra.get("capitulos_vistos") or obra.get("capitulo_actual"), len(capitulos))
    total = _safe_int(obra.get("capitulo_total") or obra.get("capitulos_publicados"), 0)
    if total > 0:
        pct = min(100, round((vistos / total) * 100))
        return f"{vistos}/{total} · {pct}%"
    return f"{len(capitulos)} guardados"


def _guardar_capitulo(add_capitulo, obra_id, temporada, numero, titulo, resumen, texto, notas, mood, etiquetas, estrellas, fecha_lectura, archivo, wrapped=None):
    archivo_path = save_uploaded_file(archivo, RESPALDOS_DIR)
    wrapped = wrapped or {}
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
        "frases_favoritas": wrapped.get("frase_favorita", ""),
        "estrellas": int(estrellas),
        "favorito": 1 if wrapped.get("favorito") else 0,
        "estado": "Leido",
        "texto_completo": texto.strip(),
        "archivo_path": archivo_path,
        "rating": float(estrellas),
        "visto_leido": 1,
        "fecha_lectura": str(fecha_lectura),
        "duracion_minutos": int(wrapped.get("duracion_minutos") or 0),
        "paginas": int(wrapped.get("paginas") or 0),
        "emocion_principal": wrapped.get("emocion_principal", ""),
        "intensidad_emocional": int(wrapped.get("intensidad_emocional") or 0),
        "ritmo": wrapped.get("ritmo", ""),
        "impacto_final": int(wrapped.get("impacto_final") or 0),
        "cliffhanger": 1 if wrapped.get("cliffhanger") else 0,
        "plot_twist": 1 if wrapped.get("plot_twist") else 0,
        "escena_favorita": wrapped.get("escena_favorita", ""),
        "momento_clave": wrapped.get("momento_clave", ""),
        "frase_favorita": wrapped.get("frase_favorita", ""),
        "categoria_wrapped": wrapped.get("categoria_wrapped", ""),
        "sensores_capitulo_json": _json(wrapped.get("sensores", {})),
        "wrapped_json": _json(wrapped),
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
        intensidad = [int(c.get("intensidad_emocional") or 0) for c in caps_temp if int(c.get("intensidad_emocional") or 0) > 0]
        intensidad_prom = round(sum(intensidad) / len(intensidad), 1) if intensidad else 0
        with cols[idx % len(cols)]:
            st.metric(f"Temporada / arco {temp}", f"{vistos} {unidad}s", f"Último: {ultimo} · ★ {promedio} · ❤ {intensidad_prom}")


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
        mood = cap.get("mood") or cap.get("emocion_principal") or "Sin mood"
        st.markdown(
            f"""
            <div class="pm-mini-card">
                <div>
                    <div class="pm-mini-title">T{temp} · {unidad.capitalize()} {num}: {titulo}</div>
                    <div class="pm-mini-subtitle">{fecha} · {mood} · impacto {cap.get('impacto_final') or 0}/5</div>
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
            or q in str(c.get("emocion_principal") or "").lower()
            or q in str(c.get("categoria_wrapped") or "").lower()
        ]
    if solo_con_texto:
        filtrados = [c for c in filtrados if bool(c.get("texto_completo"))]
    if solo_con_notas:
        filtrados = [c for c in filtrados if bool(c.get("notas") or c.get("comentario"))]
    return filtrados


def _render_reader(obra, capitulos, unidad):
    st.markdown("### 📖 Lector tipo Wattpad")
    caps = sorted([c for c in capitulos if c.get("texto_completo")], key=lambda c: (int(c.get("temporada") or 1), int(c.get("numero") or 0)))
    if not caps:
        st.info("Aún no hay capítulos con texto completo para leer. Guarda o importa texto en un capítulo para verlo aquí.")
        return
    key = f"reader_cap_id_{obra.get('id')}"
    if key not in st.session_state:
        st.session_state[key] = caps[0].get("id")
    ids = [c.get("id") for c in caps]
    if st.session_state[key] not in ids:
        st.session_state[key] = ids[0]
    idx = ids.index(st.session_state[key])
    actual = caps[idx]
    col_prev, col_select, col_next = st.columns([0.8, 2.4, 0.8])
    with col_prev:
        if st.button("⬅️ Anterior", disabled=idx == 0, key=f"reader_prev_{obra.get('id')}"):
            st.session_state[key] = ids[max(0, idx - 1)]
            st.rerun()
    with col_select:
        labels = [f"T{c.get('temporada') or 1} · {unidad.capitalize()} {c.get('numero') or 0} — {c.get('titulo') or 'Sin título'}" for c in caps]
        elegido = st.selectbox("Ir a", labels, index=idx, key=f"reader_select_{obra.get('id')}")
        nuevo_idx = labels.index(elegido)
        if nuevo_idx != idx:
            st.session_state[key] = ids[nuevo_idx]
            st.rerun()
    with col_next:
        if st.button("Siguiente ➡️", disabled=idx >= len(caps) - 1, key=f"reader_next_{obra.get('id')}"):
            st.session_state[key] = ids[min(len(caps) - 1, idx + 1)]
            st.rerun()
    st.markdown(
        f"""
        <div style="max-width:820px;margin:1.2rem auto 0 auto;padding:1.2rem 1.5rem;border-radius:22px;background:rgba(255,255,255,.86);box-shadow:0 12px 35px rgba(15,23,42,.08);">
            <div style="font-size:.82rem;font-weight:800;color:#64748b;text-transform:uppercase;letter-spacing:.08em;">{obra.get('titulo') or 'Obra'}</div>
            <h2 style="margin:.2rem 0 .25rem 0;line-height:1.15;">T{actual.get('temporada') or 1} · {unidad.capitalize()} {actual.get('numero') or 0}</h2>
            <h3 style="margin:.2rem 0 1rem 0;color:#334155;">{actual.get('titulo') or 'Sin título'}</h3>
            <div style="font-size:.88rem;color:#64748b;margin-bottom:1rem;">★ {actual.get('estrellas') or actual.get('rating') or 0} · {actual.get('fecha_lectura') or 'Sin fecha'} · {actual.get('mood') or actual.get('emocion_principal') or 'Sin mood'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    texto = actual.get("texto_completo") or ""
    st.markdown(
        f"""
        <div style="max-width:820px;margin:0 auto 1rem auto;padding:1.5rem 1.5rem 2rem 1.5rem;border-radius:0 0 22px 22px;background:white;box-shadow:0 12px 35px rgba(15,23,42,.06);font-size:1.06rem;line-height:1.85;white-space:pre-wrap;color:#1f2937;">{texto}</div>
        """,
        unsafe_allow_html=True,
    )
    if actual.get("notas") or actual.get("comentario"):
        with st.expander("📝 Mis notas de este capítulo"):
            st.write(actual.get("notas") or actual.get("comentario"))


def _render_wrapped_fields(obra_id):
    st.markdown("#### 🏆 Datos para Wrapped")
    st.caption("Esto permite después crear premios, rankings, estadísticas emocionales, rachas, top momentos y comparaciones por año.")
    c1, c2, c3 = st.columns(3)
    with c1:
        duracion_minutos = st.number_input("Minutos de sesión", min_value=0, value=0, step=5, key=f"wrap_min_{obra_id}")
        paginas = st.number_input("Páginas / avance físico", min_value=0, value=0, step=1, key=f"wrap_pag_{obra_id}")
        emocion_principal = st.selectbox("Emoción principal", EMOCIONES, key=f"wrap_emocion_{obra_id}")
        intensidad_emocional = st.slider("Intensidad emocional", 0, 5, 0, key=f"wrap_int_{obra_id}")
    with c2:
        ritmo = st.selectbox("Ritmo", RITMOS, key=f"wrap_ritmo_{obra_id}")
        impacto_final = st.slider("Impacto del cierre", 0, 5, 0, key=f"wrap_impacto_{obra_id}")
        cliffhanger = st.checkbox("Cliffhanger", key=f"wrap_cliff_{obra_id}")
        plot_twist = st.checkbox("Plot twist", key=f"wrap_twist_{obra_id}")
    with c3:
        favorito = st.checkbox("Candidato a favorito", key=f"wrap_fav_{obra_id}")
        categoria_wrapped = st.selectbox("Categoría / premio Wrapped", CATEGORIAS_WRAPPED, key=f"wrap_cat_{obra_id}")
        sensores = st.multiselect(
            "Sensores del capítulo",
            ["llanto", "risa", "cringe", "hype", "shock", "ternura", "confusión", "estrés", "comfort", "trauma", "red flag", "redención", "traición", "morbo/chisme", "resaca emocional"],
            key=f"wrap_sensores_{obra_id}",
        )
    escena_favorita = st.text_area("Escena favorita del capítulo/episodio", key=f"wrap_escena_{obra_id}")
    momento_clave = st.text_area("Momento clave / momento que debería salir en Wrapped", key=f"wrap_momento_{obra_id}")
    frase_favorita = st.text_area("Frase favorita", key=f"wrap_frase_{obra_id}")
    return {
        "duracion_minutos": int(duracion_minutos or 0),
        "paginas": int(paginas or 0),
        "emocion_principal": _select_value(emocion_principal),
        "intensidad_emocional": int(intensidad_emocional or 0),
        "ritmo": _select_value(ritmo),
        "impacto_final": int(impacto_final or 0),
        "cliffhanger": bool(cliffhanger),
        "plot_twist": bool(plot_twist),
        "favorito": bool(favorito),
        "categoria_wrapped": _select_value(categoria_wrapped),
        "sensores": {s: True for s in sensores},
        "escena_favorita": escena_favorita.strip(),
        "momento_clave": momento_clave.strip(),
        "frase_favorita": frase_favorita.strip(),
    }


def _render_personajes(obra_id, capitulos, list_personajes, add_personaje, add_voto_personaje, list_votos_personaje, save_uploaded_file_fn, imagenes_dir):
    if not all([list_personajes, add_personaje, add_voto_personaje, list_votos_personaje]):
        st.info("Personajes todavía no están conectados en esta instalación.")
        return
    personajes = list_personajes(obra_id)
    st.markdown("### 🎭 Personajes para no perderme")
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
            descripcion = st.text_area("Descripción para reconocerlo", key=f"pj_desc_{obra_id}")
            notas = st.text_area("Notas para Wrapped / evolución", key=f"pj_notas_{obra_id}")
            if st.form_submit_button("Guardar personaje"):
                if not nombre.strip():
                    st.error("El nombre del personaje es obligatorio.")
                else:
                    imagen_path = ""
                    if imagen_file is not None and save_uploaded_file_fn and imagenes_dir:
                        imagen_path = save_uploaded_file_fn(imagen_file, imagenes_dir)
                    add_personaje({"obra_id": obra_id, "nombre": nombre.strip(), "alias": alias.strip(), "rol": rol.strip(), "descripcion": descripcion.strip(), "notas": notas.strip(), "imagen_path": imagen_path or imagen_url.strip(), "favorito": 1 if favorito else 0})
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
    if capitulos and personajes:
        with st.expander("📌 Registrar aparición / momento clave por capítulo", expanded=False):
            with st.form(f"form_voto_personaje_{obra_id}"):
                cap_opts = {f"T{c.get('temporada') or 1} · {c.get('numero') or 0} — {c.get('titulo') or 'Sin título'}": c.get("id") for c in capitulos}
                pj_opts = {f"{p.get('nombre')} ({p.get('rol') or 'sin rol'})": p.get("id") for p in personajes}
                cap_sel = st.selectbox("Capítulo / episodio / parte", list(cap_opts.keys()), key=f"voto_cap_{obra_id}")
                pj_sel = st.selectbox("Personaje", list(pj_opts.keys()), key=f"voto_pj_{obra_id}")
                puntos = st.slider("Importancia del momento", 1, 5, 3, key=f"voto_pts_{obra_id}")
                comentario = st.text_area("Momento clave / evolución / confusión / teoría", key=f"voto_com_{obra_id}")
                fecha_voto = st.date_input("Fecha", value=today_local(), key=f"voto_fecha_{obra_id}")
                if st.form_submit_button("Guardar momento del personaje"):
                    add_voto_personaje({"obra_id": obra_id, "capitulo_id": cap_opts[cap_sel], "personaje_id": pj_opts[pj_sel], "fecha": str(fecha_voto), "puntos": int(puntos), "comentario": comentario.strip()})
                    st.success("Momento de personaje guardado para Wrapped.")


def render_capitulos(obras, list_capitulos, get_obra, add_capitulo=None, list_personajes=None, add_personaje=None, add_voto_personaje=None, list_votos_personaje=None, save_uploaded_file_fn=None, imagenes_dir=None):
    st.subheader("📝 Capítulos y lector")
    st.caption("Guarda capítulos y léelos dentro de la app con una vista tipo Wattpad.")
    if not obras:
        st.info("Agrega una obra primero.")
        return
    opciones = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o['id'] for o in obras}
    seleccion = st.selectbox("Selecciona una obra", list(opciones.keys()), key="capitulos_obra")
    obra_id = opciones[seleccion]
    obra = get_obra(obra_id)
    capitulos = list_capitulos(obra_id)
    temporadas = _temporadas_existentes(capitulos)
    temporada_actual = int(obra.get("temporada_actual") or 1)
    unidad = _tipo_unidad(obra)
    _render_obra_resumen(obra, capitulos, temporadas, unidad)
    modo_vista = st.radio("Vista", ["📖 Leer", "➕ Agregar capítulos", "🗂️ Gestionar / notas", "🎭 Personajes"], horizontal=True, key=f"vista_caps_{obra_id}")
    if modo_vista == "📖 Leer":
        _render_reader(obra, capitulos, unidad)
        return
    if modo_vista == "🎭 Personajes":
        _render_personajes(obra_id, capitulos, list_personajes, add_personaje, add_voto_personaje, list_votos_personaje, save_uploaded_file_fn, imagenes_dir)
        return
    if modo_vista == "➕ Agregar capítulos":
        _render_temporadas_resumen(capitulos, temporadas, unidad)
        _render_ultimos_capitulos(capitulos, unidad)
        if add_capitulo is None:
            st.warning("La función para agregar capítulos no está conectada todavía.")
            return
        with st.expander(f"➕ Agregar {unidad} / parte", expanded=True):
            modo = st.radio("Modo de carga", ["Un capítulo", "Varios capítulos pegados"], horizontal=True, key=f"modo_cap_{obra_id}")
            if modo == "Un capítulo":
                with st.form(f"form_capitulo_{obra_id}"):
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
                        fecha_lectura = st.date_input("Fecha leído/visto", value=today_local(), key=f"fecha_{obra_id}")
                    titulo = st.text_input(f"Título del {unidad}", key=f"titulo_cap_{obra_id}")
                    resumen = st.text_area(f"Resumen / sinopsis del {unidad}", key=f"resumen_cap_{obra_id}")
                    texto = st.text_area(f"Texto completo para leer dentro de la app", height=360, key=f"texto_cap_{obra_id}")
                    archivo = st.file_uploader(f"Archivo del {unidad}", type=["txt", "md", "pdf", "docx", "epub", "zip"], key=f"archivo_cap_{obra_id}")
                    archivo_texto = st.file_uploader("O subir TXT/MD para llenar el texto automáticamente", type=["txt", "md"], key=f"archivo_texto_cap_{obra_id}")
                    texto_archivo = _leer_archivo_texto(archivo_texto)
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        estrellas = st.slider("Estrellas", 0, 5, 0, key=f"estrellas_cap_{obra_id}")
                    with col5:
                        mood = st.text_input("Mood", placeholder="intenso, cozy, triste, hype...", key=f"mood_cap_{obra_id}")
                    with col6:
                        etiquetas = st.text_input("Etiquetas", placeholder="plot twist, romance, batalla...", key=f"tags_cap_{obra_id}")
                    notas = st.text_area("Comentarios / notas / teorías", key=f"notas_cap_{obra_id}")
                    wrapped = _render_wrapped_fields(obra_id)
                    if st.form_submit_button(f"Guardar {unidad}"):
                        texto_final = (texto or "")
                        if texto_archivo:
                            texto_final = (texto_final + "\n\n" + texto_archivo).strip()
                        _guardar_capitulo(add_capitulo, obra_id, temporada, numero, titulo, resumen, texto_final, notas, mood, etiquetas, estrellas, fecha_lectura, archivo, wrapped)
                        st.success(f"Registro guardado en Temporada {int(temporada)}.")
                        st.rerun()
            else:
                st.caption("Pega varios registros separados por una línea que empiece con ###. Ejemplo: ### Capítulo 1")
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
                    fecha_lectura = st.date_input("Fecha leído/visto", value=today_local(), key=f"fecha_masivo_{obra_id}")
                    texto_masivo = st.text_area("Capítulos pegados", height=360, key=f"texto_masivo_{obra_id}")
                    estrellas = st.slider("Estrellas por defecto", 0, 5, 0, key=f"estrellas_masivo_{obra_id}")
                    mood = st.text_input("Mood por defecto", key=f"mood_masivo_{obra_id}")
                    etiquetas = st.text_input("Etiquetas por defecto", key=f"tags_masivo_{obra_id}")
                    wrapped_masivo = {"emocion_principal": "", "intensidad_emocional": 0, "ritmo": "", "categoria_wrapped": "", "sensores": {}}
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
                            _guardar_capitulo(add_capitulo, obra_id, temporada, int(inicio_num) + idx, titulo, "", cuerpo, "", mood, etiquetas, estrellas, fecha_lectura, None, wrapped_masivo)
                            guardados += 1
                        st.success(f"Registros guardados: {guardados}.")
                        st.rerun()
        return
    capitulos = list_capitulos(obra_id)
    if not capitulos:
        st.warning("Esta obra aún no tiene capítulos, episodios o partes guardadas.")
        return
    path, texto = guardar_compilado(obra, capitulos)
    st.success("Compilado actualizado automáticamente.")
    with st.expander("📖 Vista previa del compilado", expanded=False):
        st.text_area("Contenido compilado", value=texto, height=500, key=f"preview_{obra_id}")
    st.download_button("⬇️ Descargar compilado .md", data=texto.encode("utf-8"), file_name=f"{obra.get('titulo','obra')}_compilado.md", mime="text/markdown")
    st.caption(f"Archivo generado: {path}")
    st.markdown("### Capítulos / episodios / partes guardadas")
    temporadas = _temporadas_existentes(capitulos)
    colf1, colf2, colf3 = st.columns([1, 2, 1])
    with colf1:
        temporada_filtro = st.selectbox("Filtrar temporada", ["Todas"] + temporadas, key=f"filtro_temp_{obra_id}")
    with colf2:
        busqueda = st.text_input("Buscar por título, notas, mood, etiquetas o Wrapped", key=f"buscar_cap_{obra_id}")
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
                mood_cap = cap.get("mood") or cap.get("emocion_principal") or "Sin mood"
                fecha_cap = cap.get("fecha_lectura") or "Sin fecha"
                impacto = cap.get("impacto_final") or 0
                with st.expander(f"{etiqueta} — {titulo_cap} · ★{estrellas_cap} · impacto {impacto}/5 · {fecha_cap}"):
                    st.caption(f"Mood: {mood_cap} · Etiquetas: {cap.get('etiquetas') or 'Sin etiquetas'} · Categoría Wrapped: {cap.get('categoria_wrapped') or 'Sin categoría'}")
                    if cap.get("sinopsis"):
                        st.write(cap.get("sinopsis"))
                    if cap.get("momento_clave"):
                        st.success(f"Momento clave: {cap.get('momento_clave')}")
                    if cap.get("escena_favorita"):
                        st.info(f"Escena favorita: {cap.get('escena_favorita')}")
                    if cap.get("frase_favorita"):
                        st.write(f"Frase favorita: {cap.get('frase_favorita')}")
                    if cap.get("notas") or cap.get("comentario"):
                        st.info(cap.get("notas") or cap.get("comentario"))
                    if cap.get("archivo_path"):
                        st.caption(f"Archivo: {cap.get('archivo_path')}")
                    if cap.get("texto_completo"):
                        st.text_area("Texto guardado", value=cap.get("texto_completo"), height=220, disabled=True, key=f"cap_text_{cap.get('id')}")
