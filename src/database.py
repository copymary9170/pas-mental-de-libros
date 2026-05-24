import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/biblioteca.db")

OBRAS_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "titulo": "TEXT NOT NULL",
    "autor": "TEXT",
    "tipo": "TEXT",
    "clasificacion": "REAL DEFAULT 0",
    "estado_lectura": "TEXT",
    "estado_publicacion": "TEXT",
    "capitulo_actual": "INTEGER DEFAULT 0",
    "capitulo_total": "INTEGER DEFAULT 0",
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

CAPITULOS_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "obra_id": "INTEGER NOT NULL",
    "temporada": "INTEGER DEFAULT 1",
    "numero": "INTEGER",
    "titulo": "TEXT",
    "sinopsis": "TEXT",
    "notas": "TEXT",
    "texto_completo": "TEXT",
    "archivo_path": "TEXT",
    "rating": "REAL DEFAULT 0",
    "visto_leido": "INTEGER DEFAULT 1",
    "fecha_lectura": "TEXT",
    "created_at": "TEXT",
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
        conn.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT,
            tipo TEXT,
            clasificacion REAL DEFAULT 0,
            estado_lectura TEXT,
            estado_publicacion TEXT,
            capitulo_actual INTEGER DEFAULT 0,
            capitulo_total INTEGER DEFAULT 0,
            temporada_actual INTEGER DEFAULT 1,
            temporada_total INTEGER DEFAULT 1,
            sinopsis TEXT,
            etiquetas TEXT,
            link_original TEXT,
            link_respaldo TEXT,
            portada_path TEXT,
            respaldo_path TEXT,
            motivo_estado TEXT,
            favorito INTEGER DEFAULT 0,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS capitulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obra_id INTEGER NOT NULL,
            temporada INTEGER DEFAULT 1,
            numero INTEGER,
            titulo TEXT,
            sinopsis TEXT,
            notas TEXT,
            texto_completo TEXT,
            archivo_path TEXT,
            rating REAL DEFAULT 0,
            visto_leido INTEGER DEFAULT 1,
            fecha_lectura TEXT,
            created_at TEXT,
            FOREIGN KEY (obra_id) REFERENCES obras(id)
        )
        """)
        _ensure_columns(conn, "obras", OBRAS_COLUMNS)
        _ensure_columns(conn, "capitulos", CAPITULOS_COLUMNS)
        conn.commit()


def add_obra(data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data)
    data["created_at"] = now
    data["updated_at"] = now
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with get_conn() as conn:
        conn.execute(f"INSERT INTO obras ({keys}) VALUES ({placeholders})", list(data.values()))
        conn.commit()


def update_obra(obra_id, data):
    now = datetime.now().isoformat(timespec="seconds")
    data = dict(data)
    data["updated_at"] = now
    setters = ", ".join([f"{k}=?" for k in data.keys()])
    with get_conn() as conn:
        conn.execute(f"UPDATE obras SET {setters} WHERE id=?", list(data.values()) + [obra_id])
        conn.commit()


def delete_obra(obra_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM capitulos WHERE obra_id=?", (obra_id,))
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
    data = dict(data)
    data["created_at"] = now
    allowed = ["obra_id", "temporada", "numero", "titulo", "sinopsis", "notas", "texto_completo", "archivo_path", "rating", "visto_leido", "fecha_lectura", "created_at"]
    clean = {k: data.get(k) for k in allowed}
    keys = ", ".join(clean.keys())
    placeholders = ", ".join(["?"] * len(clean))
    with get_conn() as conn:
        conn.execute(f"INSERT INTO capitulos ({keys}) VALUES ({placeholders})", list(clean.values()))
        conn.commit()


def list_capitulos(obra_id):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM capitulos WHERE obra_id=? ORDER BY temporada DESC, numero DESC",
            (obra_id,),
        ).fetchall()
    return [dict(row) for row in rows]
