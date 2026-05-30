import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/biblioteca.db")

OBRAS_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "titulo": "TEXT NOT NULL",
    "autor": "TEXT",
    "tipo": "TEXT",
    "obra_original_tipo": "TEXT",
    "obra_original_nombre": "TEXT",
    "fandom": "TEXT",
    "ship": "TEXT",
    "universo_au": "TEXT",
    "fuente_fanfic": "TEXT",
    "es_crossover": "INTEGER DEFAULT 0",
    "crossover_obras": "TEXT",
    "crossover_fandoms": "TEXT",
    "crossover_tipo": "TEXT",
    "crossover_notas": "TEXT",
    "division_obra": "TEXT",
    "ao3_work_id": "TEXT",
    "ao3_tracking": "INTEGER DEFAULT 0",
    "fuente_confiabilidad": "INTEGER DEFAULT 0",
    "calidad_datos": "INTEGER DEFAULT 0",
    "ultima_importacion_fuente": "TEXT",
    "clasificacion": "REAL DEFAULT 0",
    "estrellas": "INTEGER DEFAULT 0",
    "comentario": "TEXT",
    "resena": "TEXT",
    "mood": "TEXT",
    "frases_favoritas": "TEXT",
    "escenas_favoritas": "TEXT",
    "momentos_marcantes": "TEXT",
    "spoilers": "TEXT",
    "lo_recomendaria": "TEXT",
    "estado_lectura": "TEXT",
    "estado_publicacion": "TEXT",
    "fecha_publicacion": "TEXT",
    "fecha_agregada_pendientes": "TEXT",
    "capitulo_actual": "INTEGER DEFAULT 0",
    "capitulo_total": "INTEGER DEFAULT 0",
    "capitulos_publicados": "INTEGER DEFAULT 0",
    "capitulos_vistos": "INTEGER DEFAULT 0",
    "ultimo_capitulo_publicado": "INTEGER DEFAULT 0",
    "fecha_ultimo_capitulo_publicado": "TEXT",
    "ultimo_capitulo_visto": "INTEGER DEFAULT 0",
    "fecha_ultimo_capitulo_visto": "TEXT",
    "tiempo_total_minutos": "INTEGER DEFAULT 0",
    "tiempo_ultima_sesion_minutos": "INTEGER DEFAULT 0",
    "fecha_ultima_sesion": "TEXT",
    "fecha_ultima_emision": "TEXT",
    "frecuencia_emision": "TEXT",
    "proximo_capitulo_fecha": "TEXT",
    "temporada_actual": "INTEGER DEFAULT 1",
    "temporada_total": "INTEGER DEFAULT 1",
    "sinopsis": "TEXT",
    "etiquetas": "TEXT",
    "link_original": "TEXT",
    "link_respaldo": "TEXT",
    "portada_path": "TEXT",
    "respaldo_path": "TEXT",
    "motivo_estado": "TEXT",
    "favorito": "INTEGER DEFAULT 0",
    "prioridad": "INTEGER DEFAULT 0",
    "fecha_inicio": "TEXT",
    "fecha_fin": "TEXT",
    "expectativa_inicial": "TEXT",
    "nivel_esperanza_inicial": "INTEGER DEFAULT 0",
    "le_tenia_esperanza": "INTEGER DEFAULT 0",
    "le_tenia_pocas_esperanzas": "INTEGER DEFAULT 0",
    "motivo_esperanza": "TEXT",
    "resultado_expectativa": "TEXT",
    "nivel_decepcion": "INTEGER DEFAULT 0",
    "nivel_satisfaccion_general": "INTEGER DEFAULT 0",
    "satisfaccion_final": "INTEGER DEFAULT 0",
    "final_salvo_obra": "INTEGER DEFAULT 0",
    "final_arruino_obra": "INTEGER DEFAULT 0",
    "autor_arruino_final": "INTEGER DEFAULT 0",
    "como_arruino_final": "TEXT",
    "comentario_final": "TEXT",
    "es_isekai": "INTEGER DEFAULT 0",
    "tipo_isekai": "TEXT",
    "epoca_ambientacion": "TEXT",
    "mundo_principal": "TEXT",
    "nivel_construccion_mundo": "INTEGER DEFAULT 0",
    "nivel_politica_intriga": "INTEGER DEFAULT 0",
    "nivel_magia_sistema": "INTEGER DEFAULT 0",
    "nivel_romance": "INTEGER DEFAULT 0",
    "nivel_accion": "INTEGER DEFAULT 0",
    "nivel_drama": "INTEGER DEFAULT 0",
    "sensor_lujuria": "INTEGER DEFAULT 0",
    "nivel_lujuria": "INTEGER DEFAULT 0",
    "sensor_llanto": "INTEGER DEFAULT 0",
    "nivel_llanto": "INTEGER DEFAULT 0",
    "veces_llore": "INTEGER DEFAULT 0",
    "sensor_risa": "INTEGER DEFAULT 0",
    "nivel_risa": "INTEGER DEFAULT 0",
    "sensor_aburrimiento": "INTEGER DEFAULT 0",
    "nivel_aburrimiento": "INTEGER DEFAULT 0",
    "sensor_cringe": "INTEGER DEFAULT 0",
    "nivel_cringe": "INTEGER DEFAULT 0",
    "tipo_cringe": "TEXT",
    "sensor_red_flag": "INTEGER DEFAULT 0",
    "nivel_red_flag": "INTEGER DEFAULT 0",
    "sensor_resaca_emocional": "INTEGER DEFAULT 0",
    "nivel_resaca_emocional": "INTEGER DEFAULT 0",
    "sensor_tema_oscuro": "INTEGER DEFAULT 0",
    "nivel_oscuridad": "INTEGER DEFAULT 0",
    "tipo_tema_oscuro": "TEXT",
    "sensor_obra_larga": "INTEGER DEFAULT 0",
    "nivel_cansancio_longitud": "INTEGER DEFAULT 0",
    "senales_wrapped_json": "TEXT",
    "sensores_wrapped_json": "TEXT",
    "ships_json": "TEXT",
    "ranking_personal_json": "TEXT",
    "momentos_json": "TEXT",
    "personajes_iniciales_json": "TEXT",
    "registro_diario_json": "TEXT",
    "personajes_capitulo_json": "TEXT",
    "momentos_personajes_json": "TEXT",
    "evolucion_personajes_json": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
}

CANONS_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "nombre": "TEXT NOT NULL",
    "autor_original": "TEXT",
    "tipo": "TEXT",
    "fandom": "TEXT",
    "universo": "TEXT",
    "sinopsis": "TEXT",
    "etiquetas": "TEXT",
    "portada_path": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
}

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def _ensure_columns(conn, table, columns):
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for column, definition in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS obras (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, autor TEXT, tipo TEXT, obra_original_tipo TEXT, obra_original_nombre TEXT, fandom TEXT, ship TEXT, universo_au TEXT, fuente_fanfic TEXT, es_crossover INTEGER DEFAULT 0, crossover_obras TEXT, crossover_fandoms TEXT, crossover_tipo TEXT, crossover_notas TEXT, clasificacion REAL DEFAULT 0, estrellas INTEGER DEFAULT 0, comentario TEXT, resena TEXT, mood TEXT, frases_favoritas TEXT, estado_lectura TEXT, estado_publicacion TEXT, fecha_publicacion TEXT, capitulo_actual INTEGER DEFAULT 0, capitulo_total INTEGER DEFAULT 0, capitulos_publicados INTEGER DEFAULT 0, capitulos_vistos INTEGER DEFAULT 0, ultimo_capitulo_publicado INTEGER DEFAULT 0, fecha_ultimo_capitulo_publicado TEXT, ultimo_capitulo_visto INTEGER DEFAULT 0, fecha_ultimo_capitulo_visto TEXT, tiempo_total_minutos INTEGER DEFAULT 0, tiempo_ultima_sesion_minutos INTEGER DEFAULT 0, fecha_ultima_sesion TEXT, fecha_ultima_emision TEXT, frecuencia_emision TEXT, proximo_capitulo_fecha TEXT, temporada_actual INTEGER DEFAULT 1, temporada_total INTEGER DEFAULT 1, sinopsis TEXT, etiquetas TEXT, link_original TEXT, link_respaldo TEXT, portada_path TEXT, respaldo_path TEXT, motivo_estado TEXT, favorito INTEGER DEFAULT 0, fecha_inicio TEXT, fecha_fin TEXT, created_at TEXT, updated_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS capitulos (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER NOT NULL, temporada INTEGER DEFAULT 1, numero INTEGER, titulo TEXT, sinopsis TEXT, notas TEXT, comentario TEXT, etiquetas TEXT, mood TEXT, frases_favoritas TEXT, estrellas INTEGER DEFAULT 0, personaje_favorito_id INTEGER, favorito INTEGER DEFAULT 0, estado TEXT DEFAULT 'Leido', texto_completo TEXT, archivo_path TEXT, rating REAL DEFAULT 0, visto_leido INTEGER DEFAULT 1, fecha_lectura TEXT, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS actividad (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER, capitulo_id INTEGER, fecha TEXT NOT NULL, tipo_actividad TEXT, cantidad INTEGER DEFAULT 1, minutos INTEGER DEFAULT 0, mood TEXT, comentario TEXT, premio TEXT, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS personajes (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER NOT NULL, nombre TEXT NOT NULL, alias TEXT, rol TEXT, descripcion TEXT, notas TEXT, imagen_path TEXT, favorito INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS votos_personaje (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER NOT NULL, capitulo_id INTEGER, personaje_id INTEGER NOT NULL, fecha TEXT, puntos INTEGER DEFAULT 1, comentario TEXT, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS canons (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, autor_original TEXT, tipo TEXT, fandom TEXT, universo TEXT, sinopsis TEXT, etiquetas TEXT, portada_path TEXT, created_at TEXT, updated_at TEXT)""")
        _ensure_columns(conn, "obras", OBRAS_COLUMNS)
        _ensure_columns(conn, "canons", CANONS_COLUMNS)
        conn.commit()

def _insert(table, data):
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with get_conn() as conn:
        conn.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(data.values()))
        conn.commit()

def _filter_columns(table, data):
    with get_conn() as conn:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    return {k: v for k, v in dict(data).items() if k in existing}

def add_obra(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now; data["updated_at"] = now
    data.setdefault("capitulos_publicados", data.get("capitulo_total") or 0)
    data.setdefault("capitulos_vistos", data.get("capitulo_actual") or 0)
    data.setdefault("ultimo_capitulo_publicado", data.get("capitulos_publicados") or data.get("capitulo_total") or 0)
    data.setdefault("ultimo_capitulo_visto", data.get("capitulos_vistos") or data.get("capitulo_actual") or 0)
    data.setdefault("tiempo_total_minutos", 0)
    data.setdefault("tiempo_ultima_sesion_minutos", 0)
    data.setdefault("es_crossover", 0)
    data = _filter_columns("obras", data)
    _insert("obras", data)

def update_obra(obra_id, data):
    now = datetime.now().isoformat(timespec="seconds")
    data = _filter_columns("obras", dict(data)); data["updated_at"] = now
    setters = ", ".join([f"{k}=?" for k in data.keys()])
    with get_conn() as conn:
        conn.execute(f"UPDATE obras SET {setters} WHERE id=?", list(data.values()) + [obra_id])
        conn.commit()

def merge_obra_metadata(obra_id, data, only_empty=True):
    actual = get_obra(obra_id)
    if not actual:
        return False
    data = _filter_columns("obras", data)
    merged = {}
    for key, value in data.items():
        if key in ["id", "created_at", "updated_at"]:
            continue
        if value is None or value == "":
            continue
        if only_empty:
            if actual.get(key) in [None, "", 0] or key in ["capitulos_publicados", "capitulo_total", "temporada_total"]:
                merged[key] = value
        else:
            merged[key] = value
    if merged:
        update_obra(obra_id, merged)
        return True
    return False

def add_tiempo_obra(obra_id, minutos, fecha=None):
    now = datetime.now().isoformat(timespec="seconds")
    fecha = fecha or now[:10]
    minutos = int(minutos or 0)
    with get_conn() as conn:
        conn.execute("UPDATE obras SET tiempo_total_minutos = COALESCE(tiempo_total_minutos, 0) + ?, tiempo_ultima_sesion_minutos = ?, fecha_ultima_sesion = ?, updated_at = ? WHERE id = ?", (minutos, minutos, fecha, now, obra_id))
        conn.commit()

def delete_obra(obra_id):
    with get_conn() as conn:
        for table in ["votos_personaje", "personajes", "actividad", "capitulos"]:
            conn.execute(f"DELETE FROM {table} WHERE obra_id=?", (obra_id,))
        conn.execute("DELETE FROM obras WHERE id=?", (obra_id,))
        conn.commit()

def list_obras():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM obras ORDER BY updated_at DESC").fetchall()
    return [dict(row) for row in rows]

def get_obra(obra_id):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM obras WHERE id=?", (obra_id,)).fetchone()
    return dict(row) if row else None

def add_capitulo(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now
    allowed = ["obra_id", "temporada", "numero", "titulo", "sinopsis", "notas", "comentario", "etiquetas", "mood", "frases_favoritas", "estrellas", "personaje_favorito_id", "favorito", "estado", "texto_completo", "archivo_path", "rating", "visto_leido", "fecha_lectura", "created_at"]
    clean = {k: data.get(k) for k in allowed}
    keys = ", ".join(clean.keys()); placeholders = ", ".join(["?"] * len(clean))
    with get_conn() as conn:
        cur = conn.execute(f"INSERT INTO capitulos ({keys}) VALUES ({placeholders})", list(clean.values()))
        cap_id = cur.lastrowid
        if clean.get("fecha_lectura"):
            conn.execute("INSERT INTO actividad (obra_id, capitulo_id, fecha, tipo_actividad, cantidad, mood, comentario, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (clean.get("obra_id"), cap_id, clean.get("fecha_lectura"), "capitulo", 1, clean.get("mood"), clean.get("comentario") or clean.get("notas"), now))
        if clean.get("obra_id") and clean.get("numero"):
            conn.execute("UPDATE obras SET capitulo_actual=?, capitulos_vistos=?, ultimo_capitulo_visto=?, fecha_ultimo_capitulo_visto=?, updated_at=? WHERE id=?", (int(clean.get("numero")), int(clean.get("numero")), int(clean.get("numero")), clean.get("fecha_lectura"), now, clean.get("obra_id")))
        conn.commit()
    return cap_id

def list_capitulos(obra_id):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM capitulos WHERE obra_id=? ORDER BY temporada DESC, numero DESC", (obra_id,)).fetchall()
    return [dict(row) for row in rows]

def add_personaje(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now; data["updated_at"] = now
    data.setdefault("favorito", 0)
    data = _filter_columns("personajes", data)
    _insert("personajes", data)

def list_personajes(obra_id):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM personajes WHERE obra_id=? ORDER BY favorito DESC, nombre ASC", (obra_id,)).fetchall()
    return [dict(row) for row in rows]

def add_voto_personaje(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now
    allowed = ["obra_id", "capitulo_id", "personaje_id", "fecha", "puntos", "comentario", "created_at"]
    clean = {k: data.get(k) for k in allowed}
    _insert("votos_personaje", clean)

def list_votos_personaje(obra_id):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT v.*, p.nombre, p.alias, p.rol, p.descripcion, p.imagen_path, c.temporada, c.numero, c.titulo AS capitulo_titulo
            FROM votos_personaje v
            LEFT JOIN personajes p ON p.id = v.personaje_id
            LEFT JOIN capitulos c ON c.id = v.capitulo_id
            WHERE v.obra_id=?
            ORDER BY v.created_at DESC
        """, (obra_id,)).fetchall()
    return [dict(row) for row in rows]

def add_actividad(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now
    allowed = ["obra_id", "capitulo_id", "fecha", "tipo_actividad", "cantidad", "minutos", "mood", "comentario", "premio", "created_at"]
    clean = {k: data.get(k) for k in allowed}
    _insert("actividad", clean)
    if clean.get("obra_id") and int(clean.get("minutos") or 0) > 0:
        add_tiempo_obra(clean.get("obra_id"), int(clean.get("minutos") or 0), clean.get("fecha"))

def list_actividad(fecha_inicio=None, fecha_fin=None):
    q = "SELECT a.*, o.titulo, o.tipo, o.etiquetas, o.estrellas, o.clasificacion, o.portada_path FROM actividad a LEFT JOIN obras o ON a.obra_id=o.id"
    params=[]; cond=[]
    if fecha_inicio: cond.append("a.fecha >= ?"); params.append(fecha_inicio)
    if fecha_fin: cond.append("a.fecha <= ?"); params.append(fecha_fin)
    if cond: q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY a.fecha DESC, a.id DESC"
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(q, params).fetchall()]

def list_canons():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM canons ORDER BY updated_at DESC").fetchall()
    return [dict(row) for row in rows]

def add_canon(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now; data["updated_at"] = now
    data = _filter_columns("canons", data)
    _insert("canons", data)
