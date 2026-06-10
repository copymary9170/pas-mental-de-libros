import html
from pathlib import Path

import streamlit as st


TIPOS_LECTURA = {"Libro", "Fanfiction", "Novela", "Novela ligera", "Manga", "Manhwa", "Manhua", "Webnovel", "Comic"}


def _safe_int(value, default=0):
    try:
        if value in [None, ""]:
            return default
        return int(value)
    except Exception:
        return default


def _progress(obra):
    vistos = _safe_int(obra.get("capitulos_vistos") or obra.get("capitulo_actual"), 0)
    total = _safe_int(obra.get("capitulos_publicados") or obra.get("capitulo_total"), 0)
    if total <= 0:
        return vistos, total, 0
    return vistos, total, min(100, int((vistos / total) * 100))


def _cover(obra):
    portada = obra.get("portada_path") or ""
    if portada.startswith("http"):
        return portada
    if portada and Path(portada).exists():
        return portada
    return None


def _set_view(view, obra_id=None, cap_id=None):
    st.session_state["lector_view"] = view
    if obra_id is not None:
        st.session_state["lector_obra_id"] = obra_id
    if cap_id is not None:
        st.session_state[f"lector_cap_id_{obra_id}"] = cap_id
    st.rerun()


def _reader(obra, caps):
    obra_id = obra.get("id")
    caps = sorted([c for c in caps if c.get("texto_completo")], key=lambda c: (int(c.get("temporada") or 1), int(c.get("numero") or 0)))
    if not caps:
        st.warning("Esta obra aún no tiene capítulos con texto guardado para leer.")
        if st.button("⬅️ Volver a la ficha"):
            _set_view("detalle", obra_id)
        return
    key = f"lector_cap_id_{obra_id}"
    ids = [c.get("id") for c in caps]
    if key not in st.session_state or st.session_state[key] not in ids:
        st.session_state[key] = ids[0]
    idx = ids.index(st.session_state[key])
    cap = caps[idx]
    st.session_state[f"lector_last_{obra_id}"] = cap.get("id")
    b1, b2, b3 = st.columns([1, 2, 1])
    with b1:
        if st.button("⬅️ Ficha"):
            _set_view("detalle", obra_id)
    with b2:
        labels = [f"Cap. {c.get('numero') or 0} — {c.get('titulo') or 'Sin título'}" for c in caps]
        sel = st.selectbox("Capítulo", labels, index=idx)
        new_idx = labels.index(sel)
        if new_idx != idx:
            st.session_state[key] = ids[new_idx]
            st.rerun()
    with b3:
        st.progress((idx + 1) / len(caps))
        st.caption(f"{idx + 1}/{len(caps)}")
    c0, c1, c2 = st.columns([1, 1, 2])
    font_size = c0.slider("Letra", 0.9, 1.7, 1.08, 0.05, key=f"lector_font_{obra_id}")
    line_height = c1.slider("Espaciado", 1.4, 2.2, 1.8, 0.05, key=f"lector_line_{obra_id}")
    theme = c2.radio("Tema", ["Claro", "Sepia", "Oscuro"], horizontal=True, key=f"lector_theme_{obra_id}")
    if theme == "Oscuro":
        bg, body, text, muted = "#020617", "#0f172a", "#e5e7eb", "#94a3b8"
    elif theme == "Sepia":
        bg, body, text, muted = "#eadfca", "#fff7e6", "#3f2f1f", "#8a6f47"
    else:
        bg, body, text, muted = "#f8fafc", "#ffffff", "#1f2937", "#64748b"
    titulo_obra = html.escape(obra.get("titulo") or "Obra")
    titulo_cap = html.escape(cap.get("titulo") or "Sin título")
    texto = html.escape(cap.get("texto_completo") or "")
    st.markdown(f"""
    <div style="background:{bg};padding:1.2rem;border-radius:24px;">
      <div style="max-width:860px;margin:auto;background:{body};color:{text};border-radius:22px;padding:1.5rem 1.8rem;box-shadow:0 16px 45px rgba(15,23,42,.10);">
        <div style="color:{muted};font-weight:800;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;">{titulo_obra}</div>
        <h1 style="margin:.25rem 0;color:{text};">Capítulo {cap.get('numero') or 0}</h1>
        <h2 style="margin:.1rem 0 1.2rem;color:{text};font-weight:600;">{titulo_cap}</h2>
        <div style="font-size:{font_size}rem;line-height:{line_height};white-space:pre-wrap;">{texto}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    if n1.button("⬅️ Anterior", disabled=idx == 0):
        st.session_state[key] = ids[idx - 1]
        st.rerun()
    if n2.button("📚 Lista de capítulos"):
        _set_view("detalle", obra_id)
    if n3.button("Siguiente ➡️", disabled=idx >= len(caps) - 1):
        st.session_state[key] = ids[idx + 1]
        st.rerun()


def _detail(obra, capitulos):
    obra_id = obra.get("id")
    vistos, total, pct = _progress(obra)
    cover = _cover(obra)
    if st.button("⬅️ Volver a obras"):
        _set_view("galeria")
    left, right = st.columns([1, 2.2])
    with left:
        if cover:
            st.image(cover, use_container_width=True)
        else:
            st.markdown("### 📕 Sin portada")
        if st.button("▶️ Leer ahora", use_container_width=True):
            last = st.session_state.get(f"lector_last_{obra_id}")
            if last:
                st.session_state[f"lector_cap_id_{obra_id}"] = last
            _set_view("leer", obra_id)
    with right:
        st.title(obra.get("titulo") or "Sin título")
        st.caption(f"{obra.get('autor') or 'Autor desconocido'} · {obra.get('tipo') or 'Obra'} · {obra.get('estado_lectura') or 'Sin estado'}")
        st.progress(pct / 100 if pct else 0)
        st.write(f"Progreso: **{vistos}/{total or '?'}** · {pct}%")
        if obra.get("sinopsis"):
            st.markdown("### Sinopsis")
            st.write(obra.get("sinopsis"))
        if obra.get("etiquetas"):
            st.caption(f"Etiquetas: {obra.get('etiquetas')}")
    st.markdown("### Capítulos")
    caps = sorted(capitulos, key=lambda c: (int(c.get("temporada") or 1), int(c.get("numero") or 0)))
    if not caps:
        st.info("Todavía no hay capítulos cargados para esta obra.")
        return
    for cap in caps:
        has_text = bool(cap.get("texto_completo"))
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**Capítulo {cap.get('numero') or 0}: {cap.get('titulo') or 'Sin título'}**")
            c1.caption(f"T{cap.get('temporada') or 1} · ★ {cap.get('estrellas') or cap.get('rating') or 0} · {cap.get('fecha_lectura') or 'Sin fecha'}")
            if cap.get("sinopsis"):
                c1.write(cap.get("sinopsis"))
            if c2.button("Leer", disabled=not has_text, key=f"lector_open_{cap.get('id')}"):
                _set_view("leer", obra_id, cap.get("id"))


def _gallery(obras):
    st.markdown("### Elige qué quieres leer")
    q = st.text_input("Buscar por título, autor o etiqueta", key="lector_search")
    lectura = [o for o in obras if (o.get("tipo") in TIPOS_LECTURA or True)]
    if q.strip():
        t = q.lower().strip()
        lectura = [o for o in lectura if t in str(o.get("titulo") or "").lower() or t in str(o.get("autor") or "").lower() or t in str(o.get("etiquetas") or "").lower()]
    cols = st.columns(3)
    for idx, obra in enumerate(lectura):
        with cols[idx % 3]:
            with st.container(border=True):
                cover = _cover(obra)
                if cover:
                    st.image(cover, use_container_width=True)
                else:
                    st.markdown("#### 📕 Sin portada")
                st.markdown(f"**{obra.get('titulo') or 'Sin título'}**")
                st.caption(f"{obra.get('autor') or 'Autor desconocido'} · {obra.get('tipo') or 'Obra'}")
                vistos, total, pct = _progress(obra)
                st.progress(pct / 100 if pct else 0)
                st.caption(f"{vistos}/{total or '?'} · {obra.get('estado_lectura') or 'Sin estado'}")
                if st.button("Ver ficha", key=f"lector_detail_{obra.get('id')}", use_container_width=True):
                    _set_view("detalle", obra.get("id"))


def render_lector(obras, list_capitulos, get_obra):
    st.subheader("📖 Leer")
    st.caption("Vista tipo Wattpad/Kindle: portada, ficha, sinopsis, capítulos y lectura limpia.")
    if not obras:
        st.info("Agrega una obra primero.")
        return
    if "lector_view" not in st.session_state:
        st.session_state["lector_view"] = "galeria"
    view = st.session_state.get("lector_view", "galeria")
    obra_id = st.session_state.get("lector_obra_id")
    if view == "galeria" or not obra_id:
        _gallery(obras)
        return
    obra = get_obra(obra_id)
    if not obra:
        st.session_state["lector_view"] = "galeria"
        st.warning("No encontré esa obra.")
        return
    capitulos = list_capitulos(obra_id)
    if view == "leer":
        _reader(obra, capitulos)
    else:
        _detail(obra, capitulos)
