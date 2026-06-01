import json
from datetime import datetime

import pandas as pd
import streamlit as st

import src.database as db
import src.persistent_storage as persistent_storage

TABLES = ["obras", "capitulos", "personajes", "votos_personaje", "actividad", "canons"]


def _fetch_table(table):
    with db.get_conn() as conn:
        conn.row_factory = db.sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    return [dict(row) for row in rows]


def _table_columns(table):
    with db.get_conn() as conn:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def exportar_todo():
    db.init_db()
    data = {
        "app": "Paz Mental",
        "tipo": "respaldo_completo",
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "tables": {table: _fetch_table(table) for table in TABLES},
    }
    data["resumen"] = {table: len(data["tables"].get(table, [])) for table in TABLES}
    return data


def restaurar_todo(payload, modo="reemplazar"):
    db.init_db()
    if not isinstance(payload, dict) or "tables" not in payload:
        raise ValueError("El archivo no parece ser un respaldo válido de Paz Mental.")

    tables = payload.get("tables") or {}
    with db.get_conn() as conn:
        if modo == "reemplazar":
            for table in reversed(TABLES):
                conn.execute(f"DELETE FROM {table}")

        for table in TABLES:
            rows = tables.get(table, []) or []
            columns = set(_table_columns(table))
            for row in rows:
                clean = {k: v for k, v in dict(row).items() if k in columns}
                if not clean:
                    continue
                keys = list(clean.keys())
                placeholders = ", ".join(["?"] * len(keys))
                quoted = ", ".join(keys)
                conn.execute(
                    f"INSERT OR REPLACE INTO {table} ({quoted}) VALUES ({placeholders})",
                    [clean[k] for k in keys],
                )
        conn.commit()


def _render_persistencia():
    st.markdown("### 🔒 Persistencia automática en GitHub")
    st.caption("Esto es lo que hace que tus obras se queden aunque Streamlit reinicie la app.")
    if persistent_storage.is_enabled():
        st.success(persistent_storage.status_message())
        if st.button("🧪 Probar sincronización ahora", use_container_width=True):
            try:
                ok, msg = persistent_storage.upload_db(db.DB_PATH, message="Probar persistencia desde módulo respaldo")
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)
            except Exception as exc:
                st.error(f"La prueba falló: {exc}")
    else:
        st.error("La persistencia automática todavía NO está activa. Falta configurar el secret privado en Streamlit.")
        st.code('''GITHUB_BACKUP_TOKEN = "PEGA_AQUI_TU_TOKEN"
GITHUB_BACKUP_REPO = "copymary9170/pas-mental-de-libros"
GITHUB_BACKUP_BRANCH = "main"
GITHUB_BACKUP_DB_PATH = "persist/biblioteca.db"''', language="toml")
        st.info("No puedo crear ni pegar ese token por ti porque es una contraseña privada de tu cuenta. Cuando lo pegues en Streamlit Secrets y reinicies, esta sección debe ponerse en verde.")


def render_respaldo():
    st.subheader("🛟 Respaldo / Restaurar")
    st.error("Streamlit puede borrar la base local cuando se reinicia o se redeploya. La persistencia GitHub evita eso cuando el token está configurado.")

    _render_persistencia()

    data = exportar_todo()
    resumen = data.get("resumen", {})
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Obras", resumen.get("obras", 0))
    c2.metric("Capítulos", resumen.get("capitulos", 0))
    c3.metric("Personajes", resumen.get("personajes", 0))
    c4.metric("Votos", resumen.get("votos_personaje", 0))
    c5.metric("Actividad", resumen.get("actividad", 0))
    c6.metric("Canons", resumen.get("canons", 0))

    st.markdown("### Descargar respaldo completo")
    st.caption("Descarga este archivo cada vez que agregues varias obras o capítulos. Guárdalo en tu PC, Drive o Telegram.")
    backup_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"paz_mental_respaldo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button("⬇️ Descargar respaldo completo JSON", backup_bytes, filename, "application/json", use_container_width=True)

    with st.expander("Ver datos incluidos en el respaldo", expanded=False):
        for table in TABLES:
            rows = data["tables"].get(table, [])
            st.markdown(f"#### {table} ({len(rows)})")
            if rows:
                st.dataframe(pd.DataFrame(rows).head(50), use_container_width=True)
            else:
                st.info("Sin datos.")

    st.markdown("---")
    st.markdown("### Restaurar desde respaldo")
    st.warning("Restaurar en modo reemplazar borra la base actual y la sustituye por el archivo. Usa esto cuando Streamlit te haya dejado la biblioteca vacía.")
    uploaded = st.file_uploader("Sube tu respaldo JSON", type=["json"])
    modo = st.radio("Modo de restauración", ["reemplazar", "mezclar"], horizontal=True, help="Reemplazar borra lo actual. Mezclar intenta insertar lo del respaldo sin borrar primero.")
    confirmar = st.checkbox("Entiendo que restaurar puede cambiar mi biblioteca actual")

    if uploaded is not None:
        try:
            payload = json.loads(uploaded.read().decode("utf-8"))
            resumen_archivo = {table: len((payload.get("tables") or {}).get(table, []) or []) for table in TABLES}
            st.success("Archivo leído correctamente.")
            st.json(resumen_archivo)
            if st.button("♻️ Restaurar respaldo", disabled=not confirmar, use_container_width=True):
                restaurar_todo(payload, modo=modo)
                try:
                    persistent_storage.upload_db(db.DB_PATH, message="Restaurar respaldo y sincronizar DB")
                except Exception:
                    pass
                st.success("Respaldo restaurado. Vuelve a Biblioteca o recarga la app.")
                st.rerun()
        except Exception as exc:
            st.error(f"No pude leer/restaurar ese archivo: {exc}")

    st.markdown("---")
    st.markdown("### Qué pasó con la obra perdida")
    st.info("Si no existe un respaldo JSON/CSV anterior, no puedo recuperar una obra que desapareció tras un reinicio del servidor. La persistencia automática evita que vuelva a pasar después de configurar el token.")
