import pandas as pd
import streamlit as st


def _safe_unique(df, col):
    if col not in df.columns or df.empty:
        return []
    return sorted([x for x in df[col].dropna().astype(str).unique().tolist() if x.strip()])


def _num(df, col):
    if col not in df.columns:
        return pd.Series([0] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


def _text(df, col):
    if col not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[col].fillna("").astype(str)


def _top_row(df, col, minimo=1):
    if df.empty or col not in df.columns:
        return None
    vals = _num(df, col)
    if vals.max() < minimo:
        return None
    return df.loc[vals.idxmax()].to_dict()


def _top_text_row(df, col):
    if df.empty or col not in df.columns:
        return None
    mask = _text(df, col).str.strip().ne("")
    if not mask.any():
        return None
    return df[mask].iloc[0].to_dict()


def _award(title, row, reason="", value=None, empty="Sin datos suficientes todavía"):
    with st.container(border=True):
        st.markdown(f"### {title}")
        if not row:
            st.caption(empty)
            return
        st.markdown(f"**{row.get('titulo') or row.get('obra_titulo') or row.get('nombre') or 'Sin título'}**")
        meta = []
        for key in ["autor", "tipo", "fandom", "ship"]:
            if row.get(key):
                meta.append(str(row.get(key)))
        if meta:
            st.caption(" · ".join(meta))
        if value is not None:
            st.metric("Valor", value)
        if reason:
            st.write(reason)


def _award_cap(title, row, value=None):
    with st.container(border=True):
        st.markdown(f"### {title}")
        if not row:
            st.caption("Sin capítulos registrados con ese dato todavía.")
            return
        st.markdown(f"**{row.get('obra_titulo') or 'Obra'}**")
        st.write(f"Capítulo {row.get('numero') or 0}: **{row.get('titulo') or 'Sin título'}**")
        if value is not None:
            st.metric("Valor", value)
        if row.get("momento_clave"):
            st.success(row.get("momento_clave"))
        if row.get("escena_favorita"):
            st.info(row.get("escena_favorita"))
        if row.get("frase_favorita"):
            st.caption(f"Frase: {row.get('frase_favorita')}")


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
    if crossover == "Solo crossovers" and "es_crossover" in resultado.columns:
        resultado = resultado[_num(resultado, "es_crossover").astype(int).eq(1)]
    if crossover == "Sin crossovers" and "es_crossover" in resultado.columns:
        resultado = resultado[~_num(resultado, "es_crossover").astype(int).eq(1)]
    return resultado


def _load_capitulos(list_capitulos, obras):
    if not list_capitulos:
        return pd.DataFrame()
    rows = []
    for obra in obras:
        try:
            for cap in list_capitulos(obra.get("id")) or []:
                cap = dict(cap)
                cap["obra_titulo"] = obra.get("titulo")
                cap["obra_tipo"] = obra.get("tipo")
                rows.append(cap)
        except Exception:
            pass
    return pd.DataFrame(rows)


def _render_awards_obras(df):
    st.markdown("## 🏆 Premios de obras")
    c1, c2, c3 = st.columns(3)
    with c1:
        row = _top_row(df, "estrellas", 1)
        _award("⭐ Mejor calificada", row, value=row.get("estrellas") if row else None)
        row = _top_row(df, "capitulos_vistos", 1)
        _award("📚 Más leída / más avanzada", row, value=row.get("capitulos_vistos") if row else None)
        row = _top_row(df, "tiempo_total_minutos", 1)
        _award("⏳ La que más tiempo me robó", row, value=f"{int(row.get('tiempo_total_minutos') or 0)} min" if row else None)
    with c2:
        row = _top_row(df, "nivel_satisfaccion_general", 1)
        _award("👑 Mayor satisfacción", row, value=row.get("nivel_satisfaccion_general") if row else None)
        row = _top_row(df, "nivel_decepcion", 1)
        _award("💔 Mayor decepción", row, value=row.get("nivel_decepcion") if row else None)
        row = _top_row(df, "nivel_resaca_emocional", 1)
        _award("🫠 Mayor resaca emocional", row, value=row.get("nivel_resaca_emocional") if row else None)
    with c3:
        row = _top_row(df, "nivel_llanto", 1)
        _award("😭 La que más me hizo llorar", row, value=row.get("nivel_llanto") if row else None)
        row = _top_row(df, "nivel_risa", 1)
        _award("😂 La más divertida", row, value=row.get("nivel_risa") if row else None)
        row = _top_row(df, "nivel_cringe", 1)
        _award("🙈 Más cringe", row, value=row.get("nivel_cringe") if row else None)
    c4, c5, c6 = st.columns(3)
    with c4:
        row = _top_row(df, "nivel_red_flag", 1)
        _award("🚩 Más red flag", row, value=row.get("nivel_red_flag") if row else None)
        row = _top_row(df, "nivel_romance", 1)
        _award("💘 Mejor romance", row, value=row.get("nivel_romance") if row else None)
    with c5:
        row = _top_row(df, "nivel_drama", 1)
        _award("🎭 Más drama", row, value=row.get("nivel_drama") if row else None)
        row = _top_row(df, "nivel_construccion_mundo", 1)
        _award("🌌 Mejor mundo", row, value=row.get("nivel_construccion_mundo") if row else None)
    with c6:
        row = _top_row(df, "nivel_politica_intriga", 1)
        _award("🧠 Más política / intriga", row, value=row.get("nivel_politica_intriga") if row else None)
        row = _top_row(df, "nivel_magia_sistema", 1)
        _award("✨ Mejor sistema de magia", row, value=row.get("nivel_magia_sistema") if row else None)


def _render_spicy_awards(df):
    st.markdown("## 🔥 Premios de lujuria")
    st.caption("Para registrar deseo, tensión, escenas spicy, BDSM/kink y romances que subieron la temperatura.")
    c1, c2, c3 = st.columns(3)
    with c1:
        row = _top_row(df, "nivel_lujuria", 1)
        _award("💦 El que más me mojó", row, value=row.get("nivel_lujuria") if row else None)
        row = _top_row(df, "sensor_lujuria", 1)
        _award("🔥 Mayor tensión sexual", row, value=row.get("sensor_lujuria") if row else None)
    with c2:
        tags = _text(df, "etiquetas").str.lower()
        bdsm = df[tags.str.contains("bdsm|kink|domin|sumis|bondage|spicy|sadomaso", regex=True, na=False)] if not df.empty else pd.DataFrame()
        row = bdsm.iloc[0].to_dict() if not bdsm.empty else None
        _award("⛓️ Mejor BDSM / kink", row, reason="Detectado por etiquetas como BDSM, kink, dominante, sumisión, bondage o spicy.")
        row = _top_row(df, "nivel_romance", 1)
        _award("🥵 Romance más caliente", row, value=row.get("nivel_romance") if row else None)
    with c3:
        row = _top_row(df, "sensor_lujuria", 1)
        _award("🫦 Tensión que se podía cortar con cuchillo", row, value=row.get("sensor_lujuria") if row else None)
        row = _top_text_row(df, "tipo_cringe")
        _award("😳 Vergonzosamente adictiva", row, reason=row.get("tipo_cringe") if row else "")


def _render_oscar_awards(df):
    st.markdown("## 🎬 Oscar / Globo de Oro personal")
    c1, c2, c3 = st.columns(3)
    with c1:
        row = _top_row(df, "nivel_satisfaccion_general", 1) or _top_row(df, "estrellas", 1)
        _award("🏆 Mejor historia", row, value=(row.get("nivel_satisfaccion_general") or row.get("estrellas")) if row else None)
        row = _top_row(df, "nivel_decepcion", 1)
        _award("🥀 Peor historia / mayor desperdicio", row, value=row.get("nivel_decepcion") if row else None)
        row = _top_row(df, "final_salvo_obra", 1)
        _award("🎞️ Mejor final", row, value=row.get("final_salvo_obra") if row else None)
    with c2:
        row = _top_row(df, "final_arruino_obra", 1)
        _award("🗑️ Peor final", row, value=row.get("final_arruino_obra") if row else None)
        row = _top_row(df, "nivel_politica_intriga", 1)
        _award("✍️ Mejor guion / intriga", row, value=row.get("nivel_politica_intriga") if row else None)
        row = _top_row(df, "nivel_construccion_mundo", 1)
        _award("🏰 Mejor dirección de mundo", row, value=row.get("nivel_construccion_mundo") if row else None)
    with c3:
        row = _top_text_row(df, "personajes_iniciales_json") or _top_text_row(df, "personajes_capitulo_json")
        _award("🌟 Mejor personaje principal", row, reason="Se alimenta de personajes guardados cuando estén registrados.")
        row = _top_row(df, "nivel_red_flag", 1)
        _award("😈 Mejor villano / amenaza", row, value=row.get("nivel_red_flag") if row else None)
        row = _top_row(df, "nivel_drama", 1)
        _award("📺 Mejor drama estilo Globo de Oro", row, value=row.get("nivel_drama") if row else None)
    c4, c5, c6 = st.columns(3)
    with c4:
        row = _top_row(df, "nivel_accion", 1)
        _award("⚔️ Mejor acción", row, value=row.get("nivel_accion") if row else None)
    with c5:
        tags = _text(df, "etiquetas").str.lower()
        humor_negro = df[tags.str.contains("humor negro|dark comedy|comedia negra|sarcasmo|satira|sátira", regex=True, na=False)] if not df.empty else pd.DataFrame()
        row = humor_negro.iloc[0].to_dict() if not humor_negro.empty else _top_row(df, "nivel_risa", 1)
        _award("🖤 Mejor humor negro", row, reason="Detectado por etiquetas o por nivel de risa.", value=row.get("nivel_risa") if row and row.get("nivel_risa") else None)
    with c6:
        row = _top_row(df, "nivel_oscuridad", 1)
        _award("🌑 Mejor historia oscura", row, value=row.get("nivel_oscuridad") if row else None)


def _render_awards_capitulos(caps):
    st.markdown("## 📖 Premios por capítulo")
    if caps.empty:
        st.info("Todavía no hay capítulos guardados para premiar.")
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        vals = _num(caps, "estrellas")
        row = caps.loc[vals.idxmax()].to_dict() if vals.max() > 0 else None
        _award_cap("👑 Mejor capítulo", row, value=row.get("estrellas") if row else None)
        vals = _num(caps, "intensidad_emocional")
        row = caps.loc[vals.idxmax()].to_dict() if vals.max() > 0 else None
        _award_cap("⚡ Más intenso", row, value=row.get("intensidad_emocional") if row else None)
    with c2:
        vals = _num(caps, "impacto_final")
        row = caps.loc[vals.idxmax()].to_dict() if vals.max() > 0 else None
        _award_cap("💥 Mejor cierre", row, value=row.get("impacto_final") if row else None)
        cliff = caps[_num(caps, "cliffhanger").astype(int).eq(1)] if "cliffhanger" in caps.columns else pd.DataFrame()
        row = cliff.iloc[0].to_dict() if not cliff.empty else None
        _award_cap("🪝 Cliffhanger del año", row)
    with c3:
        twist = caps[_num(caps, "plot_twist").astype(int).eq(1)] if "plot_twist" in caps.columns else pd.DataFrame()
        row = twist.iloc[0].to_dict() if not twist.empty else None
        _award_cap("🧨 Plot twist del año", row)
        fav = caps[_num(caps, "favorito").astype(int).eq(1)] if "favorito" in caps.columns else pd.DataFrame()
        row = fav.iloc[0].to_dict() if not fav.empty else None
        _award_cap("❤️ Capítulo favorito marcado", row)
    if "emocion_principal" in caps.columns:
        emos = _text(caps, "emocion_principal")
        emos = emos[emos.str.strip().ne("")]
        if not emos.empty:
            st.markdown("### 🎭 Emociones más repetidas")
            emo_df = emos.value_counts().reset_index()
            emo_df.columns = ["emoción", "cantidad"]
            st.dataframe(emo_df, use_container_width=True, hide_index=True)


def _render_awards_actividad(list_actividad):
    st.markdown("## 📅 Premios de actividad")
    try:
        actividad = pd.DataFrame(list_actividad())
    except Exception:
        actividad = pd.DataFrame()
    if actividad.empty:
        st.info("Todavía no hay actividad registrada.")
        return actividad
    c1, c2, c3 = st.columns(3)
    c1.metric("Capítulos/eventos registrados", int(_num(actividad, "cantidad").sum()))
    c2.metric("Minutos registrados", int(_num(actividad, "minutos").sum()))
    if "fecha" in actividad.columns:
        by_day = actividad.groupby("fecha", dropna=True).agg(cantidad=("cantidad", "sum"), minutos=("minutos", "sum")).reset_index()
        if not by_day.empty:
            best = by_day.sort_values(["cantidad", "minutos"], ascending=False).iloc[0]
            c3.metric("Día más activo", str(best["fecha"]), f"{int(best['cantidad'])} caps · {int(best['minutos'])} min")
            st.markdown("### 🔥 Top días de lectura")
            st.dataframe(by_day.sort_values(["cantidad", "minutos"], ascending=False).head(10), use_container_width=True, hide_index=True)
    return actividad


def render_reportes(obras, list_actividad, list_capitulos=None, list_votos_personaje=None):
    st.subheader("🏆 Wrapped y reportes")
    df = pd.DataFrame(obras)
    if df.empty:
        st.info("Agrega obras para ver filtros, premios y reportes.")
        return
    filtrado = aplicar_filtros(df)
    st.markdown("### 📊 Resumen filtrado")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Obras", len(filtrado))
    c2.metric("Fanfics", int((_text(filtrado, "tipo") == "Fanfiction").sum()))
    c3.metric("Crossovers", int(_num(filtrado, "es_crossover").sum()))
    c4.metric("Tiempo total", int(_num(filtrado, "tiempo_total_minutos").sum()))
    _render_awards_obras(filtrado)
    _render_spicy_awards(filtrado)
    _render_oscar_awards(filtrado)
    caps = _load_capitulos(list_capitulos, obras)
    _render_awards_capitulos(caps)
    actividad = _render_awards_actividad(list_actividad)
    st.markdown("## 🌌 Top fandoms / canons / ships")
    col1, col2, col3 = st.columns(3)
    with col1:
        if "fandom" in filtrado.columns:
            top = _text(filtrado, "fandom")
            top = top[top.str.strip().ne("")].value_counts().reset_index()
            top.columns = ["fandom", "cantidad"]
            st.dataframe(top, use_container_width=True, hide_index=True)
    with col2:
        if "obra_original_nombre" in filtrado.columns:
            top = _text(filtrado, "obra_original_nombre")
            top = top[top.str.strip().ne("")].value_counts().reset_index()
            top.columns = ["canon", "cantidad"]
            st.dataframe(top, use_container_width=True, hide_index=True)
    with col3:
        if "ship" in filtrado.columns:
            top = _text(filtrado, "ship")
            top = top[top.str.strip().ne("")].value_counts().reset_index()
            top.columns = ["ship", "cantidad"]
            st.dataframe(top, use_container_width=True, hide_index=True)
    st.markdown("## 📚 Obras filtradas")
    cols = [c for c in ["titulo", "tipo", "estado_lectura", "fandom", "ship", "universo_au", "capitulos_vistos", "capitulos_publicados", "estrellas", "tiempo_total_minutos", "nivel_lujuria", "nivel_romance", "nivel_risa", "nivel_red_flag", "nivel_resaca_emocional"] if c in filtrado.columns]
    st.dataframe(filtrado[cols], use_container_width=True, hide_index=True)
    with st.expander("📅 Ver actividad reciente", expanded=False):
        if actividad.empty:
            st.info("Todavía no hay actividad registrada.")
        else:
            st.dataframe(actividad.head(100), use_container_width=True, hide_index=True)
