import streamlit as st

ORIGEN_TIPOS = [
    "Libro",
    "Pelicula",
    "Serie",
    "Anime",
    "Manga",
    "Manhwa",
    "Videojuego",
    "Comic",
    "Kdrama",
    "Otro",
]

FUENTES_FANFIC = [
    "AO3",
    "Wattpad",
    "FanFiction.net",
    "Tumblr",
    "Quotev",
    "SpaceBattles",
    "Sufficient Velocity",
    "Webnovel",
    "Otro",
]

TIPOS_CROSSOVER = [
    "No aplica",
    "Mundos mezclados",
    "Viaje dimensional",
    "Personajes en otro universo",
    "Fusion AU",
    "Multiverso",
    "Encuentro entre universos",
    "Otro",
]


def render_fanfiction_fields(prefix="fanfic"):
    st.markdown("### 📝 Datos de fanfiction / canon")
    st.caption("Usa esta sección para recordar de qué obra original viene el fanfic, el fandom, ship, AU y si es crossover.")

    col1, col2 = st.columns(2)
    with col1:
        obra_original_tipo = st.selectbox(
            "Tipo de obra original",
            ORIGEN_TIPOS,
            key=f"{prefix}_obra_original_tipo",
        )
        obra_original_nombre = st.text_input(
            "Nombre de la obra original / canon",
            placeholder="Harry Potter, Marvel, Naruto, The Witcher...",
            key=f"{prefix}_obra_original_nombre",
        )
        fandom = st.text_input(
            "Fandom principal",
            placeholder="Wizarding World, MCU, One Piece...",
            key=f"{prefix}_fandom",
        )
    with col2:
        fuente_fanfic = st.selectbox(
            "Fuente / plataforma del fanfic",
            FUENTES_FANFIC,
            key=f"{prefix}_fuente_fanfic",
        )
        ship = st.text_input(
            "Ship / pareja / relación principal",
            placeholder="Dramione, Stucky, Gen, OC x Canon...",
            key=f"{prefix}_ship",
        )
        universo_au = st.text_input(
            "AU / universo alternativo",
            placeholder="Coffee Shop AU, Post-war, Reincarnation, Canon divergence...",
            key=f"{prefix}_universo_au",
        )

    es_crossover = st.checkbox("🔀 Es crossover", key=f"{prefix}_es_crossover")
    crossover_obras = ""
    crossover_fandoms = ""
    crossover_tipo = "No aplica"
    crossover_notas = ""

    if es_crossover:
        st.markdown("#### 🔀 Datos del crossover")
        crossover_obras = st.text_input(
            "Obras originales incluidas",
            placeholder="Harry Potter | Percy Jackson | Marvel",
            key=f"{prefix}_crossover_obras",
        )
        crossover_fandoms = st.text_input(
            "Fandoms incluidos",
            placeholder="Wizarding World | Camp Half-Blood | MCU",
            key=f"{prefix}_crossover_fandoms",
        )
        crossover_tipo = st.selectbox(
            "Tipo de crossover",
            TIPOS_CROSSOVER,
            index=1,
            key=f"{prefix}_crossover_tipo",
        )
        crossover_notas = st.text_area(
            "Notas del crossover",
            placeholder="Cómo se mezclan los universos, reglas del AU, qué canon sigue...",
            key=f"{prefix}_crossover_notas",
        )

    return {
        "obra_original_tipo": obra_original_tipo,
        "obra_original_nombre": obra_original_nombre,
        "fandom": fandom,
        "ship": ship,
        "universo_au": universo_au,
        "fuente_fanfic": fuente_fanfic,
        "es_crossover": 1 if es_crossover else 0,
        "crossover_obras": crossover_obras,
        "crossover_fandoms": crossover_fandoms,
        "crossover_tipo": crossover_tipo,
        "crossover_notas": crossover_notas,
    }


def fanfiction_badges(row):
    if row.get("tipo") != "Fanfiction":
        return ""
    badges = []
    if row.get("fandom"):
        badges.append(f"🌌 {row.get('fandom')}")
    if row.get("obra_original_nombre"):
        badges.append(f"📌 {row.get('obra_original_nombre')}")
    if row.get("ship"):
        badges.append(f"💞 {row.get('ship')}")
    if row.get("universo_au"):
        badges.append(f"🪐 {row.get('universo_au')}")
    if int(row.get("es_crossover") or 0) == 1:
        badges.append("🔀 Crossover")
    return " · ".join(badges)
