from datetime import date, datetime

import pandas as pd
import streamlit as st

CRONOMETRO_VERSION = "Cronómetro avanzado v2 - redeploy forzado"

TIPOS_SESION = [
    "Lectura",
    "Relectura",
    "Ver episodio",
    "Ver pelicula",
    "Audiolibro",
    "Notas / investigacion",
    "Respaldo / organizacion",
]


def fmt_time(minutes):
    minutes = int(minutes or 0)
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if h else f"{m}m"


def elapsed_minutes():
    total = st.session_state.get("timer_elapsed", 0)
    if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
        total += (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
    return max(0, int(total // 60))


def _obra_actual(obras, obra_id):
    return next((o for o in obras if o["id"] == obra_id), {})


def _historial_obra(list_actividad, obra_id):
    actividad = pd.DataFrame(list_actividad())
    if actividad.empty or "obra_id" not in actividad.columns:
        return pd.DataFrame()
    actividad = actividad[pd.to_numeric(actividad["obra_id"], errors="coerce").fillna(-1).astype(int).eq(int(obra_id))]
    return actividad


def render_cronometro(obras, add_actividad, update_obra, list_actividad):
    st.subheader("⏱️ Cronómetro de lectura / visionado")
    st.caption(CRONOMETRO_VERSION)

    if not obras:
        st.info("Agrega una obra primero para usar el cronómetro.")
        return

    opciones = {f"{o['id']} - {o['titulo']} ({o.get('tipo')})": o["id"] for o in obras}
    seleccion = st.selectbox("Obra", list(opciones.keys()), key="timer_obra")
    obra_id = opciones[seleccion]
    obra = _obra_actual(obras, obra_id)

    historial = _historial_obra(list_actividad, obra_id)
    sesiones = len(historial) if not historial.empty else 0
    minutos_hist = int(pd.to_numeric(historial.get("minutos", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not historial.empty else 0
    promedio = int(minutos_hist / sesiones) if sesiones else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tiempo total obra", fmt_time(obra.get("tiempo_total_minutos") or minutos_hist))
    c2.metric("Última sesión", fmt_time(obra.get("tiempo_ultima_sesion_minutos")))
    c3.metric("Sesiones", sesiones)
    c4.metric("Promedio", fmt_time(promedio))

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        tipo_sesion = st.selectbox("Tipo de sesión", TIPOS_SESION, key="timer_tipo_sesion")
    with col_b:
        cap_actual = st.number_input("Capítulo / episodio actual", min_value=0, value=int(obra.get("capitulos_vistos") or obra.get("capitulo_actual") or 0), step=1, key="timer_cap_actual")
    with col_c:
        fecha = st.date_input("Fecha", value=date.today(), key="timer_fecha")

    col_d, col_e = st.columns(2)
    with col_d:
        mood = st.text_input("Mood", placeholder="cozy, intenso, lloré, fangirl...", key="timer_mood")
    with col_e:
        meta = st.text_input("Meta de sesión", placeholder="30 min, 2 capítulos, terminar episodio...", key="timer_meta")

    comentario = st.text_area("Comentario / notas rápidas", placeholder="Qué leíste o viste, teorías, frases, reacciones...", key="timer_comment")

    minutos = elapsed_minutes()
    st.metric("Tiempo acumulado ahora", f"{minutos} min")

    b1, b2, b3, b4, b5 = st.columns(5)
    with b1:
        if st.button("▶️ Iniciar / continuar"):
            if not st.session_state.get("timer_running"):
                st.session_state["timer_running"] = True
                st.session_state["timer_started_at"] = datetime.now()
            st.rerun()
    with b2:
        if st.button("⏸️ Pausar"):
            if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
                st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed", 0) + (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
            st.session_state["timer_running"] = False
            st.session_state["timer_started_at"] = None
            st.rerun()
    with b3:
        guardar = st.button("💾 Guardar")
    with b4:
        guardar_avanzar = st.button("💾 + avanzar cap")
    with b5:
        if st.button("🔄 Reiniciar"):
            st.session_state["timer_elapsed"] = 0
            st.session_state["timer_running"] = False
            st.session_state["timer_started_at"] = None
            st.rerun()

    if guardar or guardar_avanzar:
        if st.session_state.get("timer_running") and st.session_state.get("timer_started_at"):
            st.session_state["timer_elapsed"] = st.session_state.get("timer_elapsed", 0) + (datetime.now() - st.session_state["timer_started_at"]).total_seconds()
        final_min = max(1, int(st.session_state.get("timer_elapsed", 0) // 60))
        cap_final = int(cap_actual) + 1 if guardar_avanzar else int(cap_actual)
        comentario_final = comentario
        if meta:
            comentario_final = f"Meta: {meta}\n" + comentario_final
        add_actividad({
            "obra_id": obra_id,
            "capitulo_id": None,
            "fecha": str(fecha),
            "tipo_actividad": tipo_sesion,
            "cantidad": 1 if guardar_avanzar else 0,
            "minutos": final_min,
            "mood": mood,
            "comentario": comentario_final,
            "premio": "sesion de cronometro",
        })
        updates = {
            "capitulo_actual": cap_final,
            "capitulos_vistos": cap_final,
            "ultimo_capitulo_visto": cap_final,
            "fecha_ultimo_capitulo_visto": str(fecha),
        }
        if tipo_sesion in ["Lectura", "Relectura", "Audiolibro"]:
            updates["estado_lectura"] = "Leyendo"
        elif tipo_sesion in ["Ver episodio", "Ver pelicula"]:
            updates["estado_lectura"] = "Viendo"
        update_obra(obra_id, updates)
        st.session_state["timer_elapsed"] = 0
        st.session_state["timer_running"] = False
        st.session_state["timer_started_at"] = None
        st.success(f"Sesión guardada: {final_min} minutos. Capítulo actual: {cap_final}.")

    st.markdown("### 🕘 Historial de esta obra")
    historial = _historial_obra(list_actividad, obra_id)
    if historial.empty:
        st.info("Todavía no hay sesiones guardadas para esta obra.")
    else:
        cols = [c for c in ["fecha", "tipo_actividad", "cantidad", "minutos", "mood", "comentario"] if c in historial.columns]
        st.dataframe(historial[cols].head(30), use_container_width=True, hide_index=True)
