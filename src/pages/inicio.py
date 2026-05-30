import streamlit as st


def _count_by_estado(obras, estado):
    return len([o for o in obras or [] if str(o.get("estado_lectura", "")).lower() == estado.lower()])


def _last_active(obras):
    if not obras:
        return None
    return sorted(obras, key=lambda o: str(o.get("updated_at") or o.get("created_at") or ""), reverse=True)[0]


def _card(icon, title, subtitle, accent=""):
    st.markdown(
        f"""
        <div class="pm-home-card {accent}">
            <div class="pm-home-icon">{icon}</div>
            <div class="pm-home-title">{title}</div>
            <div class="pm-home-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_inicio(obras):
    obras = obras or []
    actual = _last_active(obras)
    leyendo = _count_by_estado(obras, "Leyendo") + _count_by_estado(obras, "Viendo") + _count_by_estado(obras, "Releyendo") + _count_by_estado(obras, "Rewatch")
    pendientes = _count_by_estado(obras, "Pendiente")
    terminadas = _count_by_estado(obras, "Terminado")
    favoritas = len([o for o in obras if int(o.get("favorito") or 0) == 1])

    st.markdown(
        """
        <div class="pm-welcome">
            <div class="pm-welcome-kicker">Paz Mental</div>
            <h2>¿Qué historia acompañó tu día?</h2>
            <p>Tu biblioteca, tus avances, tus personajes y tu Wrapped en un solo lugar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if actual:
        titulo = actual.get("titulo") or "Sin título"
        estado = actual.get("estado_lectura") or "Sin estado"
        cap = actual.get("capitulos_vistos") or actual.get("capitulo_actual") or 0
        total = actual.get("capitulo_total") or actual.get("capitulos_publicados") or 0
        progreso = f"Cap. {cap}" + (f" / {total}" if int(total or 0) else "")
        st.markdown(
            f"""
            <div class="pm-current-card">
                <div class="pm-current-label">Lectura actual</div>
                <div class="pm-current-title">{titulo}</div>
                <div class="pm-current-meta">{estado} · {progreso}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="pm-current-card">
                <div class="pm-current-label">Tu estantería está lista</div>
                <div class="pm-current-title">Agrega tu primera obra</div>
                <div class="pm-current-meta">Puedes buscar, importar por link o agregar manualmente.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("En curso", leyendo)
    m2.metric("Pendientes", pendientes)
    m3.metric("Terminadas", terminadas)
    m4.metric("Favoritas", favoritas)

    st.markdown('<div class="shelf-title">Accesos rápidos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        _card("⏱️", "Cronómetro", "Inicia una sesión y alimenta tu Wrapped.", "accent-blue")
        _card("🔎", "Buscar e importar", "Busca libros, series, manga, kdramas y más.", "accent-green")
        _card("🔗", "Importar link", "Guarda obras desde enlaces y fuentes externas.", "accent-turquoise")
    with c2:
        _card("➕", "Agregar manual", "Formulario completo con datos para Wrapped.", "accent-green")
        _card("🔔", "AO3", "Actualizaciones, tracking y fanfics.", "accent-blue")
        _card("📝", "Capítulos", "Registra episodios, progreso y notas.", "accent-turquoise")
    with c3:
        _card("🏆", "Wrapped", "Reportes, premios y estadísticas emocionales.", "accent-blue")
        _card("📅", "Calendario", "Actividad, rachas y ritmo de consumo.", "accent-green")
        _card("🌌", "Canons y personajes", "Canon, AU, versiones, ships y personajes.", "accent-turquoise")

    st.info("Usa la barra de pestañas de abajo para abrir cada sección. No se eliminó nada: cronómetro, AO3, links, capítulos, calendario, canons, diagnóstico y exportar siguen disponibles.")
