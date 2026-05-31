import json

import pandas as pd
import streamlit as st


def _safe_int(value, default=0):
    try:
        if value in [None, ""]:
            return default
        return int(value)
    except Exception:
        return default


def _safe_num(value, default=0.0):
    try:
        if value in [None, ""]:
            return default
        return float(value)
    except Exception:
        return default


def _parse_json(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {}


def _sensor_counter(capitulos):
    conteo = {}
    for cap in capitulos:
        sensores = _parse_json(cap.get("sensores_capitulo_json"))
        for nombre, valor in sensores.items():
            activo = False
            nivel = 1
            if isinstance(valor, dict):
                activo = bool(valor.get("activo", True))
                nivel = _safe_num(valor.get("nivel") or valor.get("veces") or 1, 1)
            else:
                activo = bool(valor)
            if activo:
                if nombre not in conteo:
                    conteo[nombre] = {"veces": 0, "nivel_total": 0}
                conteo[nombre]["veces"] += 1
                conteo[nombre]["nivel_total"] += nivel
    return conteo


def _tendencia(valores):
    valores = [v for v in valores if v is not None]
    if len(valores) < 2:
        return "sin evolución suficiente"
    mitad = max(1, len(valores) // 2)
    inicio = sum(valores[:mitad]) / len(valores[:mitad])
    final = sum(valores[mitad:]) / len(valores[mitad:]) if valores[mitad:] else inicio
    diff = final - inicio
    if diff >= 0.75:
        return "subiendo"
    if diff <= -0.75:
        return "bajando"
    return "estable"


def _resumen_capitulos(capitulos):
    caps = sorted(
        [dict(c) for c in capitulos or []],
        key=lambda c: (_safe_int(c.get("temporada"), 1), _safe_int(c.get("numero"), 0), str(c.get("created_at") or "")),
    )
    if not caps:
        return None

    intensidades = [_safe_num(c.get("intensidad_emocional"), 0) for c in caps]
    impactos = [_safe_num(c.get("impacto_final"), 0) for c in caps]
    estrellas = [_safe_num(c.get("estrellas") or c.get("rating"), 0) for c in caps]
    minutos = [_safe_int(c.get("duracion_minutos"), 0) for c in caps]
    paginas = [_safe_int(c.get("paginas"), 0) for c in caps]

    top_intenso = max(caps, key=lambda c: _safe_num(c.get("intensidad_emocional"), 0))
    top_impacto = max(caps, key=lambda c: _safe_num(c.get("impacto_final"), 0))
    sensores = _sensor_counter(caps)
    sensores_top = sorted(sensores.items(), key=lambda x: (x[1]["veces"], x[1]["nivel_total"]), reverse=True)

    emociones = [str(c.get("emocion_principal") or "").strip() for c in caps if str(c.get("emocion_principal") or "").strip()]
    emocion_top = pd.Series(emociones).value_counts().index[0] if emociones else ""

    return {
        "cantidad": len(caps),
        "intensidad_prom": round(sum(intensidades) / len(intensidades), 2) if intensidades else 0,
        "impacto_prom": round(sum(impactos) / len(impactos), 2) if impactos else 0,
        "estrellas_prom": round(sum(estrellas) / len(estrellas), 2) if estrellas else 0,
        "minutos": sum(minutos),
        "paginas": sum(paginas),
        "plot_twists": sum(_safe_int(c.get("plot_twist"), 0) for c in caps),
        "cliffhangers": sum(_safe_int(c.get("cliffhanger"), 0) for c in caps),
        "tendencia_intensidad": _tendencia(intensidades),
        "tendencia_impacto": _tendencia(impactos),
        "emocion_top": emocion_top,
        "sensor_top": sensores_top[0][0] if sensores_top else "",
        "sensor_top_veces": sensores_top[0][1]["veces"] if sensores_top else 0,
        "top_intenso": top_intenso,
        "top_impacto": top_impacto,
        "caps": caps,
        "sensores": sensores_top,
    }


def _cap_label(cap):
    return f"T{cap.get('temporada') or 1} · Cap {cap.get('numero') or '?'} — {cap.get('titulo') or 'Sin título'}"


def _render_resumen(resumen):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capítulos", resumen["cantidad"])
    c2.metric("Intensidad", resumen["intensidad_prom"], resumen["tendencia_intensidad"])
    c3.metric("Impacto", resumen["impacto_prom"], resumen["tendencia_impacto"])
    c4.metric("Estrellas", resumen["estrellas_prom"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Minutos", resumen["minutos"])
    c6.metric("Páginas/avance", resumen["paginas"])
    c7.metric("Plot twists", resumen["plot_twists"])
    c8.metric("Cliffhangers", resumen["cliffhangers"])

    lectura = []
    if resumen["emocion_top"]:
        lectura.append(f"Emoción más repetida: **{resumen['emocion_top']}**.")
    if resumen["sensor_top"]:
        lectura.append(f"Sensor dominante: **{resumen['sensor_top']}** ({resumen['sensor_top_veces']} veces).")
    lectura.append(f"La intensidad va **{resumen['tendencia_intensidad']}** y el impacto va **{resumen['tendencia_impacto']}**.")
    st.write(" ".join(lectura))

    m1, m2 = st.columns(2)
    with m1:
        st.info(f"Más intenso: {_cap_label(resumen['top_intenso'])}\n\nIntensidad: {resumen['top_intenso'].get('intensidad_emocional') or 0}/5")
        if resumen["top_intenso"].get("momento_clave"):
            st.write(resumen["top_intenso"].get("momento_clave"))
    with m2:
        st.info(f"Mayor impacto: {_cap_label(resumen['top_impacto'])}\n\nImpacto: {resumen['top_impacto'].get('impacto_final') or 0}/5")
        if resumen["top_impacto"].get("escena_favorita"):
            st.write(resumen["top_impacto"].get("escena_favorita"))

    df = pd.DataFrame(resumen["caps"])
    for col in ["numero", "intensidad_emocional", "impacto_final", "estrellas", "rating"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    st.markdown("#### 📊 Evolución")
    st.line_chart(df[["numero", "intensidad_emocional", "impacto_final", "estrellas"]].set_index("numero"))

    st.markdown("#### 🚨 Sensores por capítulos")
    if resumen["sensores"]:
        sensor_df = pd.DataFrame([
            {"sensor": nombre, "veces": data["veces"], "nivel_total": data["nivel_total"]}
            for nombre, data in resumen["sensores"]
        ])
        st.dataframe(sensor_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay sensores por capítulo en esta obra.")

    with st.expander("Ver capítulos usados para estos cálculos", expanded=False):
        cols = ["temporada", "numero", "titulo", "emocion_principal", "intensidad_emocional", "impacto_final", "ritmo", "categoria_wrapped", "momento_clave", "escena_favorita"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)


def render_obra_insights(obra, list_capitulos):
    if list_capitulos is None:
        st.info("La lectura de capítulos no está conectada todavía.")
        return
    try:
        capitulos = list_capitulos(obra.get("id")) or []
    except Exception as exc:
        st.warning(f"No pude leer capítulos de esta obra: {exc}")
        return
    resumen = _resumen_capitulos(capitulos)
    if not resumen:
        st.info("Esta obra aún no tiene capítulos/episodios con datos guardados.")
        return
    _render_resumen(resumen)


def render_biblioteca_insights(obras, list_capitulos):
    selected_id = st.session_state.get("biblioteca_graph_id")
    if not selected_id:
        return
    obra = next((o for o in obras or [] if str(o.get("id")) == str(selected_id)), None)
    if not obra:
        return
    with st.expander(f"📊 Gráfica de {obra.get('titulo') or 'esta obra'}", expanded=True):
        if st.button("Cerrar gráfica", key="cerrar_grafica_biblioteca_global"):
            st.session_state.pop("biblioteca_graph_id", None)
            st.rerun()
        render_obra_insights(obra, list_capitulos)
