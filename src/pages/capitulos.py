import streamlit as st
from src.compilador import guardar_compilado


def render_capitulos(obras, list_capitulos, get_obra):
    st.subheader("📚 Capitulos y compilado")

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
    st.caption(f"Capitulos guardados: {len(capitulos)}")

    if not capitulos:
        st.warning("Esta obra aun no tiene capitulos guardados.")
        return

    path, texto = guardar_compilado(obra, capitulos)

    st.success("Compilado actualizado automaticamente.")

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
