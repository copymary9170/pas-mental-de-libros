import random

import streamlit as st


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _progress(row):
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    if publicados <= 0:
        return 0
    return min(100, int((vistos / publicados) * 100))


def _pending(row):
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados") or row.get("capitulo_total"), 0)
    return max(0, publicados - vistos)


def _fmt_unknown(value):
    value = _safe_int(value, 0)
    return "?" if value <= 0 else str(value)


def _card(row):
    titulo = row.get("titulo") or "Sin título"
    autor = row.get("autor") or "Autor no indicado"
    tipo = row.get("tipo") or "Tipo N/D"
    estado = row.get("estado_lectura") or "Estado N/D"
    vistos = _safe_int(row.get("capitulos_vistos") or row.get("capitulo_actual"), 0)
    publicados = _safe_int(row.get("capitulos_publicados"), 0)
    total = _safe_int(row.get("capitulo_total"), 0)
    pct = _progress(row)
    link = row.get("link_original") or ""

    st.markdown(f"### 🎲 {titulo}")
    st.write(f"**Autor/creador:** {autor}")
    st.write(f"**Tipo:** {tipo} · **Estado:** {estado}")
    st.progress(pct / 100 if pct else 0)
    st.caption(f"Vistos/leídos: {vistos} · Publicados: {_fmt_unknown(publicados)} · Total esperado: {_fmt_unknown(total)} · Pendientes: {_pending(row)}")
    if row.get("sinopsis"):
        st.write(row.get("sinopsis"))
    if row.get("mood"):
        st.info(f"Mood: {row.get('mood')}")
    if str(link).startswith("http"):
        st.link_button("Abrir link original", link)


def render_ruleta(obras):
    st.subheader("🎲 Ruleta / Aleatorio")
    st.caption("Para cuando no sabes qué leer o ver: filtra tu biblioteca y deja que la app escoja por ti.")

    obras = obras or []
    if not obras:
        st.info("Todavía no hay obras para sortear.")
        return

    tipos = sorted({str(o.get("tipo") or "Sin tipo") for o in obras if str(o.get("tipo") or "").strip()})
    estados = sorted({str(o.get("estado_lectura") or "Sin estado") for o in obras if str(o.get("estado_lectura") or "").strip()})

    st.markdown("### Filtros de la ruleta")
    c1, c2, c3 = st.columns(3)
    tipo_sel = c1.multiselect("Tipo de obra", tipos, default=tipos)
    estado_base = c2.selectbox(
        "Estado rápido",
        [
            "Cualquiera",
            "Sin terminar",
            "Pendiente",
            "En curso",
            "Terminada",
            "Pausada",
            "Abandonada",
            "Releer / rewatch",
            "Con capítulos pendientes",
            "Al día / sin pendientes",
        ],
    )
    solo_fav = c3.checkbox("Solo favoritos")
    evitar_abandonadas = c3.checkbox("Evitar abandonadas", value=True)
    solo_con_link = c3.checkbox("Solo con link")

    with st.expander("Filtros avanzados", expanded=False):
        estados_sel = st.multiselect("Estados exactos", estados, default=[])
        texto = st.text_input("Buscar por texto, etiqueta, fandom, ship, mood o autor")
        min_estrellas = st.slider("Mínimo de estrellas", 0, 5, 0)
        incluir_sin_portada = st.checkbox("Incluir obras sin portada", value=True)

    candidatos = list(obras)
    if tipo_sel:
        candidatos = [o for o in candidatos if (o.get("tipo") or "Sin tipo") in tipo_sel]
    if estados_sel:
        candidatos = [o for o in candidatos if (o.get("estado_lectura") or "Sin estado") in estados_sel]
    if solo_fav:
        candidatos = [o for o in candidatos if _safe_int(o.get("favorito"), 0) == 1]
    if evitar_abandonadas:
        candidatos = [o for o in candidatos if o.get("estado_lectura") != "Abandonado"]
    if solo_con_link:
        candidatos = [o for o in candidatos if str(o.get("link_original") or "").startswith("http")]
    if min_estrellas:
        candidatos = [o for o in candidatos if _safe_int(o.get("estrellas"), 0) >= min_estrellas]
    if not incluir_sin_portada:
        candidatos = [o for o in candidatos if str(o.get("portada_path") or "").strip()]

    if estado_base == "Sin terminar":
        candidatos = [o for o in candidatos if o.get("estado_lectura") not in ["Terminado", "Abandonado"]]
    elif estado_base == "Pendiente":
        candidatos = [o for o in candidatos if o.get("estado_lectura") == "Pendiente"]
    elif estado_base == "En curso":
        candidatos = [o for o in candidatos if o.get("estado_lectura") in ["Leyendo", "Viendo"]]
    elif estado_base == "Terminada":
        candidatos = [o for o in candidatos if o.get("estado_lectura") == "Terminado"]
    elif estado_base == "Pausada":
        candidatos = [o for o in candidatos if o.get("estado_lectura") == "Pausado"]
    elif estado_base == "Abandonada":
        candidatos = [o for o in candidatos if o.get("estado_lectura") == "Abandonado"]
    elif estado_base == "Releer / rewatch":
        candidatos = [o for o in candidatos if o.get("estado_lectura") in ["Releyendo", "Rewatch", "Terminado"]]
    elif estado_base == "Con capítulos pendientes":
        candidatos = [o for o in candidatos if _pending(o) > 0]
    elif estado_base == "Al día / sin pendientes":
        candidatos = [o for o in candidatos if _pending(o) == 0]

    if texto.strip():
        q = texto.lower().strip()
        campos = ["titulo", "autor", "etiquetas", "fandom", "ship", "mood", "sinopsis", "obra_original_nombre"]
        candidatos = [
            o for o in candidatos
            if q in " ".join(str(o.get(c, "")) for c in campos).lower()
        ]

    st.metric("Opciones en la ruleta", len(candidatos))

    if not candidatos:
        st.warning("No hay obras con esos filtros. Afloja un filtro o cambia el estado rápido.")
        return

    col_a, col_b = st.columns(2)
    if col_a.button("🎲 Girar ruleta", use_container_width=True):
        st.session_state["ruleta_resultado"] = random.choice(candidatos)
    if col_b.button("🧹 Limpiar resultado", use_container_width=True):
        st.session_state.pop("ruleta_resultado", None)

    resultado = st.session_state.get("ruleta_resultado")
    if resultado:
        st.success("La ruleta eligió:")
        _card(resultado)
    else:
        st.info("Toca **Girar ruleta** para elegir una obra al azar.")

    with st.expander("Ver candidatos de esta ruleta", expanded=False):
        for obra in candidatos[:100]:
            st.write(f"• {obra.get('titulo') or 'Sin título'} · {obra.get('tipo') or 'N/D'} · {obra.get('estado_lectura') or 'N/D'} · pendientes {_pending(obra)}")
