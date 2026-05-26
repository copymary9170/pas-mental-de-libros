from datetime import date
from pathlib import Path

import streamlit as st

from src.compilador import guardar_compilado
from src.utils import save_uploaded_file, RESPALDOS_DIR


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


def _guardar_capitulo(add_capitulo, obra_id, temporada, numero, titulo, resumen, texto, notas, mood, etiquetas, estrellas, fecha_lectura, archivo):
    archivo_path = save_uploaded_file(archivo, RESPALDOS_DIR)
    add_capitulo({
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


def render_capitulos(obras, list_capitulos, get_obra, add_capitulo=None):
    st.subheader("📚 Capítulos, episodios y compilado")

    if not obras:
        st.info("Agrega una obra primero.")
        return

    opciones = {
        f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o['id']
        for o in obras
    }

    seleccion = st.selectbox(
        "Selecciona una obra",
        list(opciones.keys()),
        key="capitulos_obra"
    )

    obra_id = opciones[seleccion]
    obra = get_obra(obra_id)
    capitulos = list_capitulos(obra_id)

    st.markdown(f"### {obra.get('titulo')}")
    st.caption(f"Capítulos guardados: {len(capitulos)}")

    if add_capitulo is None:
        st.warning("La función para agregar capítulos no está conectada todavía.")
    else:
        with st.expander("➕ Agregar capítulo / episodio", expanded=True):
            modo = st.radio(
                "Modo de carga",
                ["Un capítulo", "Varios capítulos pegados"],
                horizontal=True,
                key=f"modo_cap_{obra_id}"
            )

            if modo == "Un capítulo":
                with st.form(f"form_capitulo_{obra_id}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        temporada = st.number_input("Temporada", min_value=1, value=1, step=1, key=f"temp_{obra_id}")
                    with col2:
                        numero = st.number_input("Número de capítulo / episodio", min_value=0, value=(len(capitulos) + 1), step=1, key=f"num_{obra_id}")
                    with col3:
                        fecha_lectura = st.date_input("Fecha leído/visto", value=date.today(), key=f"fecha_{obra_id}")

                    titulo = st.text_input("Título del capítulo", key=f"titulo_cap_{obra_id}")
                    resumen = st.text_area("Resumen / sinopsis del capítulo", key=f"resumen_cap_{obra_id}")
                    texto = st.text_area("Texto completo del capítulo", height=260, key=f"texto_cap_{obra_id}")
                    archivo = st.file_uploader("Archivo del capítulo", type=["txt", "md", "pdf", "docx", "epub", "zip"], key=f"archivo_cap_{obra_id}")
                    archivo_texto = st.file_uploader("O subir TXT/MD para llenar el texto automáticamente", type=["txt", "md"], key=f"archivo_texto_cap_{obra_id}")
                    texto_archivo = _leer_archivo_texto(archivo_texto)
                    if texto_archivo:
                        st.info("Se detectó texto en el archivo. Se guardará junto al texto pegado.")

                    col4, col5, col6 = st.columns(3)
                    with col4:
                        estrellas = st.slider("Estrellas", 0, 5, 0, key=f"estrellas_cap_{obra_id}")
                    with col5:
                        mood = st.text_input("Mood", placeholder="intenso, cozy, triste...", key=f"mood_cap_{obra_id}")
                    with col6:
                        etiquetas = st.text_input("Etiquetas", placeholder="plot twist, romance...", key=f"tags_cap_{obra_id}")

                    notas = st.text_area("Comentarios / notas / teorías", key=f"notas_cap_{obra_id}")

                    if st.form_submit_button("Guardar capítulo"):
                        texto_final = (texto or "")
                        if texto_archivo:
                            texto_final = (texto_final + "\n\n" + texto_archivo).strip()
                        _guardar_capitulo(add_capitulo, obra_id, temporada, numero, titulo, resumen, texto_final, notas, mood, etiquetas, estrellas, fecha_lectura, archivo)
                        st.success("Capítulo guardado. El compilado se actualizará automáticamente al recargar esta pestaña.")

            else:
                st.caption("Pega varios capítulos separados por una línea que empiece con ###. Ejemplo: ### Capítulo 1")
                with st.form(f"form_masivo_{obra_id}"):
                    temporada = st.number_input("Temporada", min_value=1, value=1, step=1, key=f"temp_masivo_{obra_id}")
                    inicio_num = st.number_input("Número inicial", min_value=1, value=len(capitulos) + 1, step=1, key=f"inicio_masivo_{obra_id}")
                    fecha_lectura = st.date_input("Fecha leído/visto", value=date.today(), key=f"fecha_masivo_{obra_id}")
                    texto_masivo = st.text_area("Capítulos pegados", height=360, key=f"texto_masivo_{obra_id}")
                    estrellas = st.slider("Estrellas por defecto", 0, 5, 0, key=f"estrellas_masivo_{obra_id}")
                    mood = st.text_input("Mood por defecto", key=f"mood_masivo_{obra_id}")
                    etiquetas = st.text_input("Etiquetas por defecto", key=f"tags_masivo_{obra_id}")

                    if st.form_submit_button("Guardar varios capítulos"):
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
                            titulo = lineas[0].replace("###", "").strip() if lineas else f"Capítulo {int(inicio_num) + idx}"
                            cuerpo = "\n".join(lineas[1:]).strip() if len(lineas) > 1 else bloque
                            _guardar_capitulo(add_capitulo, obra_id, temporada, int(inicio_num) + idx, titulo, "", cuerpo, "", mood, etiquetas, estrellas, fecha_lectura, None)
                            guardados += 1
                        st.success(f"Capítulos guardados: {guardados}. El compilado se actualizará automáticamente.")

    capitulos = list_capitulos(obra_id)
    if not capitulos:
        st.warning("Esta obra aún no tiene capítulos guardados.")
        return

    path, texto = guardar_compilado(obra, capitulos)

    st.success("Compilado actualizado automáticamente.")

    with st.expander("📖 Vista previa del compilado", expanded=True):
        st.text_area(
            "Contenido compilado",
            value=texto,
            height=500,
            key=f"preview_{obra_id}"
        )

    st.download_button(
        "⬇️ Descargar compilado .md",
        data=texto.encode("utf-8"),
        file_name=f"{obra.get('titulo','obra')}_compilado.md",
        mime="text/markdown"
    )

    st.caption(f"Archivo generado: {path}")

    st.markdown("### Capítulos guardados")
    for cap in capitulos:
        etiqueta = f"T{cap.get('temporada') or 1} · Cap. {cap.get('numero') or 0}"
        with st.expander(f"{etiqueta} — {cap.get('titulo') or 'Sin título'}"):
            if cap.get("sinopsis"):
                st.write(cap.get("sinopsis"))
            if cap.get("notas") or cap.get("comentario"):
                st.info(cap.get("notas") or cap.get("comentario"))
            if cap.get("texto_completo"):
                st.text_area("Texto guardado", value=cap.get("texto_completo"), height=220, disabled=True, key=f"cap_text_{cap.get('id')}")
