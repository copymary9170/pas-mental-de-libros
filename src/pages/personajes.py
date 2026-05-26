import streamlit as st


def render_personajes(obras, list_personajes, add_personaje, ranking_personajes):
    st.subheader("👥 Personajes y ranking")

    if not obras:
        st.info("Agrega una obra primero.")
        return

    opciones = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o["id"] for o in obras}
    seleccion = st.selectbox("Selecciona una obra", list(opciones.keys()), key="personajes_obra")
    obra_id = opciones[seleccion]

    with st.expander("➕ Agregar personaje", expanded=True):
        with st.form(f"form_personaje_{obra_id}"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del personaje *")
                alias = st.text_input("Alias / apodo")
                rol = st.text_input("Rol", placeholder="protagonista, villano, interés amoroso...")
            with col2:
                imagen_path = st.text_input("URL de imagen opcional")
                favorito = st.checkbox("Personaje favorito general")
            descripcion = st.text_area("Descripción corta")
            notas = st.text_area("Notas / teorías / relaciones")
            if st.form_submit_button("Guardar personaje"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    add_personaje({
                        "obra_id": obra_id,
                        "nombre": nombre.strip(),
                        "alias": alias.strip(),
                        "rol": rol.strip(),
                        "descripcion": descripcion.strip(),
                        "notas": notas.strip(),
                        "imagen_path": imagen_path.strip(),
                        "favorito": 1 if favorito else 0,
                    })
                    st.success("Personaje guardado.")

    ranking = ranking_personajes(obra_id)
    personajes = list_personajes(obra_id)

    st.markdown("### 🏆 Ranking de personajes")
    if ranking:
        for idx, p in enumerate(ranking, start=1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    if p.get("imagen_path"):
                        st.image(p.get("imagen_path"), use_container_width=True)
                    else:
                        st.markdown(f"### {medal}")
                with col2:
                    st.markdown(f"**{medal} {p.get('nombre')}**")
                    st.caption(f"Puntos: {p.get('puntos',0)} · Veces favorito: {p.get('veces_favorito',0)} · Rol: {p.get('rol') or 'N/D'}")
                    if p.get("alias"):
                        st.write(f"Alias: {p.get('alias')}")
                    if p.get("descripcion"):
                        st.write(p.get("descripcion"))
                st.divider()
    else:
        st.info("Todavía no hay ranking. Marca personajes favoritos por capítulo para sumar puntos.")

    st.markdown("### 📚 Personajes guardados")
    if not personajes:
        st.info("No hay personajes guardados para esta obra.")
    else:
        for p in personajes:
            with st.expander(f"{p.get('nombre')} — {p.get('rol') or 'Sin rol'}"):
                if p.get("imagen_path"):
                    st.image(p.get("imagen_path"), width=150)
                if p.get("alias"):
                    st.write(f"**Alias:** {p.get('alias')}")
                if p.get("descripcion"):
                    st.write(p.get("descripcion"))
                if p.get("notas"):
                    st.info(p.get("notas"))
