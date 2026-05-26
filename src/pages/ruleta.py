import random

import pandas as pd
import streamlit as st


def render_ruleta(obras):
    st.subheader("🎲 Ruleta inteligente anti aburrimiento")

    if not obras:
        st.info("Agrega obras primero.")
        return

    df = pd.DataFrame(obras)

    col1, col2, col3 = st.columns(3)
    with col1:
        tipos = st.multiselect("Tipos", sorted(df["tipo"].dropna().astype(str).unique().tolist()) if "tipo" in df.columns else [])
    with col2:
        estados = st.multiselect("Estados", sorted(df["estado_lectura"].dropna().astype(str).unique().tolist()) if "estado_lectura" in df.columns else [])
    with col3:
        fandoms = st.multiselect("Fandoms", sorted(df["fandom"].dropna().astype(str).unique().tolist()) if "fandom" in df.columns else [])

    pendientes = st.checkbox("Solo obras no terminadas", value=True)
    con_caps = st.checkbox("Solo obras con capítulos pendientes")

    filtrado = df.copy()

    if tipos:
        filtrado = filtrado[filtrado["tipo"].astype(str).isin(tipos)]
    if estados and "estado_lectura" in filtrado.columns:
        filtrado = filtrado[filtrado["estado_lectura"].astype(str).isin(estados)]
    if fandoms and "fandom" in filtrado.columns:
        filtrado = filtrado[filtrado["fandom"].astype(str).isin(fandoms)]

    if pendientes and "estado_lectura" in filtrado.columns:
        filtrado = filtrado[~filtrado["estado_lectura"].astype(str).isin(["Terminado"])]

    if con_caps:
        filtrado = filtrado[
            pd.to_numeric(filtrado.get("capitulos_publicados", 0), errors="coerce").fillna(0)
            > pd.to_numeric(filtrado.get("capitulos_vistos", 0), errors="coerce").fillna(0)
        ]

    st.caption(f"Obras disponibles para la ruleta: {len(filtrado)}")

    if st.button("🎲 Girar ruleta"):
        if filtrado.empty:
            st.warning("No hay obras que coincidan con esos filtros.")
        else:
            elegido = filtrado.sample(1).iloc[0]
            st.markdown("## ✨ Tu elección del día ✨")
            if elegido.get("portada_path"):
                st.image(elegido.get("portada_path"), width=220)
            st.markdown(f"### {elegido.get('titulo')}")
            st.write(f"**Tipo:** {elegido.get('tipo')}")
            st.write(f"**Estado:** {elegido.get('estado_lectura')}")
            if elegido.get("fandom"):
                st.write(f"**Fandom:** {elegido.get('fandom')}")
            if elegido.get("ship"):
                st.write(f"**Ship:** {elegido.get('ship')}")
            if elegido.get("sinopsis"):
                st.info(str(elegido.get("sinopsis"))[:500])
            st.success("La ruleta eligió algo para evitar el aburrimiento ✨")
