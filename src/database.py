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
    "clasificacion": "REAL DEFAULT 0",
    "estrellas": "INTEGER DEFAULT 0",
    "comentario": "TEXT",
    "resena": "TEXT",
    "mood": "TEXT",
    "frases_favoritas": "TEXT",
    "estado_lectura": "TEXT",
    "estado_publicacion": "TEXT",
    "fecha_publicacion": "TEXT",
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
    "fecha_inicio": "TEXT",
    "fecha_fin": "TEXT",
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
        conn.execute("""CREATE TABLE IF NOT EXISTS obras (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, autor TEXT, tipo TEXT, obra_original_tipo TEXT, obra_original_nombre TEXT, fandom TEXT, ship TEXT, universo_au TEXT, fuente_fanfic TEXT, clasificacion REAL DEFAULT 0, estrellas INTEGER DEFAULT 0, comentario TEXT, resena TEXT, mood TEXT, frases_favoritas TEXT, estado_lectura TEXT, estado_publicacion TEXT, fecha_publicacion TEXT, capitulo_actual INTEGER DEFAULT 0, capitulo_total INTEGER DEFAULT 0, capitulos_publicados INTEGER DEFAULT 0, capitulos_vistos INTEGER DEFAULT 0, ultimo_capitulo_publicado INTEGER DEFAULT 0, fecha_ultimo_capitulo_publicado TEXT, ultimo_capitulo_visto INTEGER DEFAULT 0, fecha_ultimo_capitulo_visto TEXT, tiempo_total_minutos INTEGER DEFAULT 0, tiempo_ultima_sesion_minutos INTEGER DEFAULT 0, fecha_ultima_sesion TEXT, fecha_ultima_emision TEXT, frecuencia_emision TEXT, proximo_capitulo_fecha TEXT, temporada_actual INTEGER DEFAULT 1, temporada_total INTEGER DEFAULT 1, sinopsis TEXT, etiquetas TEXT, link_original TEXT, link_respaldo TEXT, portada_path TEXT, respaldo_path TEXT, motivo_estado TEXT, favorito INTEGER DEFAULT 0, fecha_inicio TEXT, fecha_fin TEXT, created_at TEXT, updated_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS capitulos (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER NOT NULL, temporada INTEGER DEFAULT 1, numero INTEGER, titulo TEXT, sinopsis TEXT, notas TEXT, comentario TEXT, etiquetas TEXT, mood TEXT, frases_favoritas TEXT, estrellas INTEGER DEFAULT 0, personaje_favorito_id INTEGER, favorito INTEGER DEFAULT 0, estado TEXT DEFAULT 'Leido', texto_completo TEXT, archivo_path TEXT, rating REAL DEFAULT 0, visto_leido INTEGER DEFAULT 1, fecha_lectura TEXT, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS actividad (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER, capitulo_id INTEGER, fecha TEXT NOT NULL, tipo_actividad TEXT, cantidad INTEGER DEFAULT 1, minutos INTEGER DEFAULT 0, mood TEXT, comentario TEXT, premio TEXT, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS personajes (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER NOT NULL, nombre TEXT NOT NULL, alias TEXT, rol TEXT, descripcion TEXT, notas TEXT, imagen_path TEXT, favorito INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS votos_personaje (id INTEGER PRIMARY KEY AUTOINCREMENT, obra_id INTEGER NOT NULL, capitulo_id INTEGER, personaje_id INTEGER NOT NULL, fecha TEXT, puntos INTEGER DEFAULT 1, comentario TEXT, created_at TEXT)""")
        _ensure_columns(conn, "obras", OBRAS_COLUMNS)
        conn.commit()

def _insert(table, data):
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with get_conn() as conn:
        conn.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", list(data.values()))
        conn.commit()

def add_obra(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now; data["updated_at"] = now
    data.setdefault("capitulos_publicados", data.get("capitulo_total") or 0)
    data.setdefault("capitulos_vistos", data.get("capitulo_actual") or 0)
    data.setdefault("ultimo_capitulo_publicado", data.get("capitulos_publicados") or data.get("capitulo_total") or 0)
    data.setdefault("ultimo_capitulo_visto", data.get("capitulos_vistos") or data.get("capitulo_actual") or 0)
    data.setdefault("tiempo_total_minutos", 0)
    data.setdefault("tiempo_ultima_sesion_minutos", 0)
    _insert("obras", data)

def update_obra(obra_id, data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["updated_at"] = now
    setters = ", ".join([f"{k}=?" for k in data.keys()])
    with get_conn() as conn:
        conn.execute(f"UPDATE obras SET {setters} WHERE id=?", list(data.values()) + [obra_id])
        conn.commit()

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
    q += " ORDER BY a.fecha DESC, a.created_at DESC"
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(q, params).fetchall()
    return [dict(row) for row in rows]

def add_personaje(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now; data["updated_at"] = now
    allowed = ["obra_id", "nombre", "alias", "rol", "descripcion", "notas", "imagen_path", "favorito", "created_at", "updated_at"]
    _insert("personajes", {k: data.get(k) for k in allowed})

def list_personajes(obra_id):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM personajes WHERE obra_id=? ORDER BY favorito DESC, nombre ASC", (obra_id,)).fetchall()
    return [dict(row) for row in rows]

def add_voto_personaje(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data); data["created_at"] = now
    allowed = ["obra_id", "capitulo_id", "personaje_id", "fecha", "puntos", "comentario", "created_at"]
    _insert("votos_personaje", {k: data.get(k) for k in allowed})

def ranking_personajes(obra_id):
    q = "SELECT p.id, p.nombre, p.alias, p.rol, p.descripcion, p.favorito, COALESCE(SUM(v.puntos),0) AS puntos, COUNT(v.id) AS veces_favorito FROM personajes p LEFT JOIN votos_personaje v ON p.id=v.personaje_id WHERE p.obra_id=? GROUP BY p.id ORDER BY puntos DESC, veces_favorito DESC, p.favorito DESC, p.nombre ASC"
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(q, (obra_id,)).fetchall()
    return [dict(row) for row in rows]
