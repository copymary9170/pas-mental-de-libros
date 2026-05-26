import pandas as pd
import streamlit as st


def _safe_unique(df, col):
    if col not in df.columns or df.empty:
        return []
    return sorted([x for x in df[col].dropna().astype(str).unique().tolist() if x.strip()])


def aplicar_filtros(df):
    if df.empty:
        return df
    st.markdown("### 🔎 Filtros avanzados")
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo = st.multiselect("Tipo", _safe_unique(df, "tipo"))
        estado = st.multiselect("Estado personal", _safe_unique(df, "estado_lectura"))
    with col2:
        fandom = st.multiselect("Fandom", _safe_unique(df, "fandom"))
        canon = st.multiselect("Canon / obra original", _safe_unique(df, "obra_original_nombre"))
    with col3:
        ship = st.multiselect("Ship", _safe_unique(df, "ship"))
        crossover = st.selectbox("Crossover", ["Todos", "Solo crossovers", "Sin crossovers"])

    col4, col5 = st.columns(2)
    with col4:
        origen_tipo = st.multiselect("Tipo de obra base usada", _safe_unique(df, "obra_original_tipo"))
    with col5:
        universo = st.multiselect("Universo / AU", _safe_unique(df, "universo_au"))

    resultado = df.copy()
    if tipo:
        resultado = resultado[resultado["tipo"].astype(str).isin(tipo)]
    if estado and "estado_lectura" in resultado.columns:
        resultado = resultado[resultado["estado_lectura"].astype(str).isin(estado)]
    if fandom and "fandom" in resultado.columns:
        resultado = resultado[resultado["fandom"].astype(str).isin(fandom)]
    if canon and "obra_original_nombre" in resultado.columns:
        resultado = resultado[resultado["obra_original_nombre"].astype(str).isin(canon)]
    if ship and "ship" in resultado.columns:
        resultado = resultado[resultado["ship"].astype(str).isin(ship)]
    if origen_tipo and "obra_original_tipo" in resultado.columns:
        resultado = resultado[resultado["obra_original_tipo"].astype(str).isin(origen_tipo)]
    if universo and "universo_au" in resultado.columns:
        resultado = resultado[resultado["universo_au"].astype(str).isin(universo)]
    if crossover == "Solo crossovers" and "es_crossover" in resultado.columns:
        resultado = resultado[pd.to_numeric(resultado["es_crossover"], errors="coerce").fillna(0).astype(int).eq(1)]
    if crossover == "Sin crossovers" and "es_crossover" in resultado.columns:
        resultado = resultado[~pd.to_numeric(resultado["es_crossover"], errors="coerce").fillna(0).astype(int).eq(1)]
    return resultado


def render_reportes(obras, list_actividad):
    st.subheader("🏆 Wrapped y reportes")
    df = pd.DataFrame(obras)
    if df.empty:
        st.info("Agrega obras para ver filtros y reportes.")
        return

    filtrado = aplicar_filtros(df)

    st.markdown("### 📊 Resumen filtrado")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Obras", len(filtrado))
    c2.metric("Fanfics", int((filtrado.get("tipo", pd.Series(dtype=str)).astype(str) == "Fanfiction").sum()))
    if "es_crossover" in filtrado.columns:
        c3.metric("Crossovers", int(pd.to_numeric(filtrado["es_crossover"], errors="coerce").fillna(0).sum()))
    else:
        c3.metric("Crossovers", 0)
    if "tiempo_total_minutos" in filtrado.columns:
        c4.metric("Tiempo total", int(pd.to_numeric(filtrado["tiempo_total_minutos"], errors="coerce").fillna(0).sum()))
    else:
        c4.metric("Tiempo total", 0)

    st.markdown("### 🌌 Top fandoms / canons")
    col1, col2 = st.columns(2)
    with col1:
        if "fandom" in filtrado.columns:
            top_fandom = filtrado["fandom"].dropna().astype(str)
            top_fandom = top_fandom[top_fandom.str.strip() != ""].value_counts().reset_index()
            top_fandom.columns = ["fandom", "cantidad"]
            st.dataframe(top_fandom, use_container_width=True, hide_index=True)
    with col2:
        if "obra_original_nombre" in filtrado.columns:
            top_canon = filtrado["obra_original_nombre"].dropna().astype(str)
            top_canon = top_canon[top_canon.str.strip() != ""].value_counts().reset_index()
            top_canon.columns = ["canon", "cantidad"]
            st.dataframe(top_canon, use_container_width=True, hide_index=True)

    st.markdown("### 💞 Ships y universos")
    col3, col4 = st.columns(2)
    with col3:
        if "ship" in filtrado.columns:
            top_ship = filtrado["ship"].dropna().astype(str)
            top_ship = top_ship[top_ship.str.strip() != ""].value_counts().reset_index()
            top_ship.columns = ["ship", "cantidad"]
            st.dataframe(top_ship, use_container_width=True, hide_index=True)
    with col4:
        if "universo_au" in filtrado.columns:
            top_universo = filtrado["universo_au"].dropna().astype(str)
            top_universo = top_universo[top_universo.str.strip() != ""].value_counts().reset_index()
            top_universo.columns = ["universo/AU", "cantidad"]
            st.dataframe(top_universo, use_container_width=True, hide_index=True)

    st.markdown("### 📚 Obras filtradas")
    cols = [c for c in ["titulo", "tipo", "estado_lectura", "fandom", "obra_original_nombre", "obra_original_tipo", "universo_au", "ship", "es_crossover", "capitulos_vistos", "capitulos_publicados", "tiempo_total_minutos"] if c in filtrado.columns]
    st.dataframe(filtrado[cols], use_container_width=True, hide_index=True)

    st.markdown("### 📅 Actividad reciente")
    actividad = pd.DataFrame(list_actividad())
    if actividad.empty:
        st.info("Todavía no hay actividad registrada.")
    else:
        st.dataframe(actividad.head(100), use_container_width=True)
