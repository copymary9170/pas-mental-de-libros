import streamlit as st

from src.ao3_utils import es_link_ao3, extraer_ao3_info


def _estado_visual(faltan, completo):
    if completo:
        return "🔵 Completo"
    if faltan <= 0:
        return "🟢 Al día"
    return f"🟡 {faltan} pendientes"



def render_ao3_updates(obras):
    st.subheader("🔔 Actualizaciones AO3")
    st.caption("Revisión manual de fanfics y obras conectadas con AO3.")

    obras_ao3 = []
    for obra in obras:
        link = obra.get("link_original") or obra.get("url_fuente") or ""
        if es_link_ao3(link):
            obras_ao3.append(obra)

    if not obras_ao3:
        st.info("No hay obras con links de AO3 todavía.")
        st.caption("Guarda un link de AO3 en la obra para habilitar seguimiento.")
        return

    st.success(f"Obras AO3 detectadas: {len(obras_ao3)}")

    revisar = st.button("🔄 Revisar AO3 ahora", key="ao3_refresh")

    resultados = []

    for obra in obras_ao3:
        link = obra.get("link_original") or obra.get("url_fuente") or ""

        if revisar:
            data = extraer_ao3_info(link)
        else:
            data = {"ok": False, "error": "Pulsa revisar para consultar AO3."}

        capitulos_leidos = int(obra.get("capitulos_vistos") or obra.get("capitulo_actual") or 0)

        if data.get("ok"):
            publicados = int(data.get("capitulos_publicados") or 0)
            faltan = max(0, publicados - capitulos_leidos)
            estado = _estado_visual(faltan, data.get("completo"))

            resultados.append({
                "obra": obra.get("titulo"),
                "autor": data.get("autor") or obra.get("autor") or "",
                "leidos": capitulos_leidos,
                "publicados": publicados,
                "faltan": faltan,
                "estado": estado,
                "actualizacion": data.get("fecha_actualizacion") or "",
                "revisado": data.get("revisado_en") or "",
            })
        else:
            resultados.append({
                "obra": obra.get("titulo"),
                "autor": obra.get("autor") or "",
                "leidos": capitulos_leidos,
                "publicados": "?",
                "faltan": "?",
                "estado": "🔴 Sin revisar",
                "actualizacion": data.get("error") or "",
                "revisado": "",
            })

    st.markdown("### 📋 Estado de tus obras")

    for r in resultados:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"### {r['obra']}")
                st.caption(r['autor'])
                st.write(r['estado'])
            with col2:
                st.metric("Leídos", r['leidos'])
                st.metric("Publicados", r['publicados'])
            with col3:
                st.metric("Pendientes", r['faltan'])
                st.caption(f"Última actualización: {r['actualizacion']}")

            if r['revisado']:
                st.caption(f"Revisado: {r['revisado']}")
