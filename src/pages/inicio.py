import base64
import mimetypes
from pathlib import Path

import streamlit as st


def _count_by_estado(obras, estado):
    return len([o for o in obras or [] if str(o.get("estado_lectura", "")).lower() == estado.lower()])


def _last_active(obras):
    if not obras:
        return None
    return sorted(obras, key=lambda o: str(o.get("updated_at") or o.get("created_at") or ""), reverse=True)[0]


def _tipo_counts(obras):
    counts = {}
    for obra in obras or []:
        tipo = obra.get("tipo") or "Sin tipo"
        counts[tipo] = counts.get(tipo, 0) + 1
    return counts


def _image_src(path_or_url):
    raw = str(path_or_url or "").strip()
    if not raw:
        return ""
    if raw.startswith(("http://", "https://", "data:")):
        return raw
    path = Path(raw)
    if not path.exists():
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def _cover_html(path_or_url):
    src = _image_src(path_or_url)
    if src:
        return f'<img class="pm-cover-placeholder" src="{src}" style="object-fit:cover;" />'
    return '<div class="pm-cover-placeholder">▧</div>'


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
    viendo_o_leyendo = _count_by_estado(obras, "Leyendo") + _count_by_estado(obras, "Viendo") + _count_by_estado(obras, "Releyendo") + _count_by_estado(obras, "Rewatch")
    pendientes = _count_by_estado(obras, "Pendiente")
    terminadas = _count_by_estado(obras, "Terminado")
    pausadas = _count_by_estado(obras, "Pausado")
    abandonadas = _count_by_estado(obras, "Abandonado")
    favoritas = len([o for o in obras if int(o.get("favorito") or 0) == 1])
    total = len(obras)
    tipos = _tipo_counts(obras)
    libros = sum(tipos.get(t, 0) for t in ["Libro", "Novela", "Novela ligera", "Webnovel"])
    visuales = sum(tipos.get(t, 0) for t in ["Pelicula", "Serie", "Kdrama", "Anime", "Documental"])
    comics = sum(tipos.get(t, 0) for t in ["Manga", "Manhwa", "Manhua", "Comic"])
    fanfics = tipos.get("Fanfiction", 0)

    if actual:
        titulo = actual.get("titulo") or "Sin título"
        estado = actual.get("estado_lectura") or "Sin estado"
        tipo_actual = actual.get("tipo") or "Obra"
        cap = actual.get("capitulos_vistos") or actual.get("capitulo_actual") or 0
        cap_total = actual.get("capitulo_total") or actual.get("capitulos_publicados") or 0
        progreso = f"Avance {cap}" + (f" / {cap_total}" if int(cap_total or 0) else "")
        fecha = str(actual.get("fecha_inicio") or actual.get("updated_at") or "Sin fecha")[:10]
        portada_html = _cover_html(actual.get("portada_path"))
    else:
        titulo = "Agrega tu primera obra"
        estado = "Sin obra activa"
        tipo_actual = "Historia"
        progreso = "Avance 0"
        fecha = "Hoy"
        portada_html = _cover_html("")

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
                    {portada_html}
                    <div>
                        <div class="pm-reading-date">{fecha}</div>
                        <div class="pm-reading-status">{tipo_actual} · {estado}</div>
                        <div class="pm-reading-notes">▢ 0 notas</div>
                    </div>
                </div>
                <div class="pm-floating-actions">⏱️ &nbsp; 📝</div>
            </div>
            <div class="pm-status-card">Estás disfrutando una historia. <span>▧</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _section("Historias para más tarde")
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
        _mini_card("Obras guardadas", "Links, compras y pendientes", "▧")

    _wide_card("Calendario de consumo", "¿Qué has leído o visto este mes?", "▦")

    st.markdown(
        f"""
        <div class="pm-streak-card">
            <div class="pm-streak-title">🔥 Racha</div>
            <div class="pm-streak-subtitle">1 día consumiendo historias</div>
            <div class="pm-week-row"><span>lun</span><span>mar</span><span>mié</span><span>jue</span><span class="active">vie</span><span>sáb</span><span>dom</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _wide_card("Estadísticas diarias", f"{viendo_o_leyendo} en curso · {terminadas} terminadas", "0%")

    st.markdown(
        f"""
        <div class="pm-chart-card">
            <div class="pm-mini-title">Estadísticas anuales</div>
            <div class="pm-mini-subtitle">Has registrado {total} obras</div>
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
        _mini_card("Favoritas", f"{favoritas} obras", "★")
    with col4:
        _mini_card("Biblioteca", f"{total} obras", "▧")

    _section("Tipos de obras", "Más")
    col5, col6 = st.columns(2)
    with col5:
        _mini_card("Lectura", f"{libros + fanfics + comics} obras", "📖")
    with col6:
        _mini_card("Pantalla", f"{visuales} obras", "🎬")
    col7, col8 = st.columns(2)
    with col7:
        _mini_card("Fanfics", f"{fanfics} obras", "✍️")
    with col8:
        _mini_card("Manga / cómic", f"{comics} obras", "▤")

    _section("Estado de obras", "Más")
    col9, col10 = st.columns(2)
    with col9:
        _mini_card("Pausadas", f"{pausadas} obras", "Ⅱ")
    with col10:
        _mini_card("Abandonadas", f"{abandonadas} obras", "☁")
    _wide_card("Mi universo de historias", f"{total} obras registradas", "▱")

    st.markdown(
        """
        <div class="pm-tool-strip">
            <div>⏱️ Cronómetro</div><div>🔎 Buscar</div><div>🔗 Links</div><div>🔔 AO3</div><div>📝 Capítulos</div><div>🏆 Wrapped</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
