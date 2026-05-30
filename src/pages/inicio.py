import streamlit as st


def _count_by_estado(obras, estado):
    return len([o for o in obras or [] if str(o.get("estado_lectura", "")).lower() == estado.lower()])


def _last_active(obras):
    if not obras:
        return None
    return sorted(obras, key=lambda o: str(o.get("updated_at") or o.get("created_at") or ""), reverse=True)[0]


def _mini_card(title, subtitle, icon=""):
    st.markdown(
        f"""
        <div class="pm-mini-card">
            <div>
                <div class="pm-mini-title">{title}</div>
                <div class="pm-mini-subtitle">{subtitle}</div>
            </div>
            <div class="pm-mini-icon">{icon}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _wide_card(title, subtitle, icon=""):
    st.markdown(
        f"""
        <div class="pm-wide-card">
            <div>
                <div class="pm-mini-title">{title}</div>
                <div class="pm-mini-subtitle">{subtitle}</div>
            </div>
            <div class="pm-mini-icon">{icon}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(title, right=""):
    st.markdown(
        f"""
        <div class="pm-section-row">
            <div class="shelf-title">{title}</div>
            <div class="pm-section-more">{right}</div>
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
    pausadas = _count_by_estado(obras, "Pausado")
    abandonadas = _count_by_estado(obras, "Abandonado")
    favoritas = len([o for o in obras if int(o.get("favorito") or 0) == 1])
    total = len(obras)

    if actual:
        titulo = actual.get("titulo") or "Sin título"
        estado = actual.get("estado_lectura") or "Sin estado"
        cap = actual.get("capitulos_vistos") or actual.get("capitulo_actual") or 0
        cap_total = actual.get("capitulo_total") or actual.get("capitulos_publicados") or 0
        progreso = f"Pág. / Cap. {cap}" + (f" / {cap_total}" if int(cap_total or 0) else "")
        fecha = str(actual.get("fecha_inicio") or actual.get("updated_at") or "Sin fecha")[:10]
    else:
        titulo = "Agrega tu primera obra"
        estado = "Sin lectura activa"
        progreso = "Pág. / Cap. 0"
        fecha = "Hoy"

    st.markdown(
        f"""
        <div class="pm-phone-shell">
            <div class="pm-top-space"></div>
            <div class="pm-current-progress">
                <span>Día {max(1, total)}</span>
                <span>{progreso}</span>
            </div>
            <div class="pm-reading-card">
                <div class="pm-bookmark"></div>
                <div class="pm-reading-title">{titulo}</div>
                <div class="pm-reading-body">
                    <div class="pm-cover-placeholder">▧</div>
                    <div>
                        <div class="pm-reading-date">{fecha}</div>
                        <div class="pm-reading-status">{estado}</div>
                        <div class="pm-reading-notes">▢ 0 notas</div>
                    </div>
                </div>
                <div class="pm-floating-actions">⏱️ &nbsp; 📝</div>
            </div>
            <div class="pm-status-card">Estás leyendo un libro. <span>▧</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _section("Libros para leer más tarde")
    st.markdown(
        """
        <div class="pm-plus-row">
            <div class="pm-plus">+</div><div class="pm-plus">+</div><div class="pm-plus">+</div><div class="pm-plus">+</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        _mini_card("Lista de deseos", f"{pendientes} pendientes", "♡")
    with col2:
        _mini_card("Libros comprados", "Registra tus compras", "▧")

    _wide_card("Calendario de libros", "¿Cuánto has leído este mes?", "▦")

    st.markdown(
        f"""
        <div class="pm-streak-card">
            <div class="pm-streak-title">🔥 Racha</div>
            <div class="pm-streak-subtitle">1 día</div>
            <div class="pm-week-row"><span>lun</span><span>mar</span><span>mié</span><span>jue</span><span class="active">vie</span><span>sáb</span><span>dom</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _wide_card("Estadísticas diarias", f"{leyendo} en curso · {terminadas} terminadas", "0%")

    st.markdown(
        f"""
        <div class="pm-chart-card">
            <div class="pm-mini-title">Estadísticas anuales</div>
            <div class="pm-mini-subtitle">Has leído {total} obras</div>
            <div class="pm-bar-wrap"><div class="pm-bar" style="height:{min(78, max(10, total * 8))}px"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _section("Rebobinando")
    st.markdown('<div class="pm-year-chip">2026</div>', unsafe_allow_html=True)
    _wide_card("Estadísticas de etiquetas", f"{len(set(','.join([str(o.get('etiquetas') or '') for o in obras]).split(','))) if obras else 0} etiquetas", "#")

    _section("Colecciones", "Más")
    col3, col4 = st.columns(2)
    with col3:
        _mini_card("Favorito", f"{favoritas} obras", "★")
    with col4:
        _mini_card("Biblioteca", f"{total} obras", "▧")

    _section("Series y sagas", "Más")
    col5, col6 = st.columns(2)
    with col5:
        _mini_card("Libros pausados", f"{pausadas} obras", "Ⅱ")
    with col6:
        _mini_card("Los dejé de leer", f"{abandonadas} obras", "☁")
    _wide_card("Mi biblioteca", f"{total} obras", "▱")

    st.markdown(
        """
        <div class="pm-tool-strip">
            <div>⏱️ Cronómetro</div><div>🔎 Buscar</div><div>🔗 Links</div><div>🔔 AO3</div><div>📝 Capítulos</div><div>🏆 Wrapped</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
