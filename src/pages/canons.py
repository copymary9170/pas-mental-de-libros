import streamlit as st

CANON_TIPOS = [
    "Libro",
    "Pelicula",
    "Serie",
    "Anime",
    "Manga",
    "Manhwa",
    "Videojuego",
    "Comic",
    "Kdrama",
    "Otro",
]


def render_canons(add_canon, list_canons):
    st.subheader("🌌 Canons / obras originales reutilizables")
    st.caption("Guarda aquí obras originales que usas mucho para fanfics, así no tienes que repetirlas cada vez.")

    with st.form("canon_form"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre de la obra original / canon *", placeholder="Harry Potter, Marvel, Naruto...")
            autor_original = st.text_input("Autor / creador original", placeholder="J.K. Rowling, Marvel Studios, Masashi Kishimoto...")
            tipo = st.selectbox("Tipo de obra original", CANON_TIPOS)
        with col2:
            fandom = st.text_input("Fandom", placeholder="Wizarding World, MCU, Konoha...")
            universo = st.text_input("Universo / franquicia", placeholder="Wizarding World, Marvel Cinematic Universe...")
            etiquetas = st.text_input("Etiquetas", placeholder="magia, superhéroes, ninja...")
        sinopsis = st.text_area("Sinopsis / notas del canon")
        portada_url = st.text_input("URL de portada opcional")

        if st.form_submit_button("Guardar canon"):
            if not nombre.strip():
                st.error("El nombre del canon es obligatorio.")
            else:
                add_canon({
                    "nombre": nombre.strip(),
                    "autor_original": autor_original.strip(),
                    "tipo": tipo,
                    "fandom": fandom.strip(),
                    "universo": universo.strip(),
                    "sinopsis": sinopsis.strip(),
                    "etiquetas": etiquetas.strip(),
                    "portada_path": portada_url.strip(),
                })
                st.success("Canon guardado. Ya podrás reutilizarlo en fanfictions.")

    canons = list_canons()
    if not canons:
        st.info("Todavía no hay canons guardados.")
        return

    st.markdown("### Canons guardados")
    for canon in canons:
        with st.expander(f"{canon.get('nombre')} — {canon.get('fandom') or 'Sin fandom'}"):
            st.write(f"**Tipo:** {canon.get('tipo') or 'N/D'}")
            st.write(f"**Autor original:** {canon.get('autor_original') or 'N/D'}")
            st.write(f"**Universo:** {canon.get('universo') or 'N/D'}")
            if canon.get("sinopsis"):
                st.write(canon.get("sinopsis"))
            if canon.get("etiquetas"):
                st.caption(canon.get("etiquetas"))


def canon_selectbox(list_canons, key="canon_select"):
    canons = list_canons()
    if not canons:
        st.info("No tienes canons guardados todavía. Puedes escribir los datos manualmente o crear uno en la pestaña 🌌 Canons.")
        return None
    opciones = {f"{c.get('nombre')} ({c.get('fandom') or c.get('tipo')})": c for c in canons}
    selected = st.selectbox("Usar canon guardado", ["No usar"] + list(opciones.keys()), key=key)
    if selected == "No usar":
        return None
    return opciones[selected]
