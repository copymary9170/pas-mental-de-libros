from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import src.database as db

BACKUP_DIR = Path("data/backups")


def _table_count(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        return 0


def _columns(conn, table):
    try:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []


def _missing_columns(conn, table, expected):
    current = set(_columns(conn, table))
    return [col for col in expected.keys() if col not in current]


def _backup_db():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not db.DB_PATH.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"biblioteca_backup_{stamp}.db"
    shutil.copy2(db.DB_PATH, target)
    return target


def _backup_json():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"biblioteca_export_{stamp}.json"
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "obras": db.list_obras(),
    }
    with db.get_conn() as conn:
        for table in ["capitulos", "actividad", "personajes", "votos_personaje", "canons"]:
            conn.row_factory = sqlite3.Row
            try:
                payload[table] = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
            except Exception:
                payload[table] = []
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _backup_csv():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"obras_export_{stamp}.csv"
    rows = db.list_obras()
    if not rows:
        target.write_text("", encoding="utf-8")
        return target
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for row in rows for k in row.keys()}))
        writer.writeheader()
        writer.writerows(rows)
    return target


def _normalize_tags(value):
    tags = []
    for raw in str(value or "").replace(";", ",").split(","):
        tag = raw.strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return ", ".join(tags)


def _find_duplicates(obras):
    seen = {}
    dupes = []
    for obra in obras:
        title = str(obra.get("titulo") or "").strip().lower()
        author = str(obra.get("autor") or "").strip().lower()
        url = str(obra.get("link_original") or "").strip().lower()
        key = url or f"{title}|{author}"
        if not key.strip("|"):
            continue
        if key in seen:
            dupes.append((seen[key], obra))
        else:
            seen[key] = obra
    return dupes


def _repair_progress(obras):
    fixed = 0
    for obra in obras:
        updates = {}
        cap_actual = int(obra.get("capitulo_actual") or 0)
        vistos = int(obra.get("capitulos_vistos") or 0)
        cap_total = int(obra.get("capitulo_total") or 0)
        publicados = int(obra.get("capitulos_publicados") or 0)
        temporada_actual = max(1, int(obra.get("temporada_actual") or 1))
        temporada_total = max(temporada_actual, int(obra.get("temporada_total") or 1))
        if vistos < cap_actual:
            updates["capitulos_vistos"] = cap_actual
        if cap_actual < vistos:
            updates["capitulo_actual"] = vistos
        if publicados < cap_total:
            updates["capitulos_publicados"] = cap_total
        if temporada_actual != obra.get("temporada_actual"):
            updates["temporada_actual"] = temporada_actual
        if temporada_total != obra.get("temporada_total"):
            updates["temporada_total"] = temporada_total
        if updates:
            db.update_obra(obra["id"], updates)
            fixed += 1
    return fixed


def _normalize_all_tags(obras):
    fixed = 0
    for obra in obras:
        old = obra.get("etiquetas") or ""
        new = _normalize_tags(old)
        if new != old:
            db.update_obra(obra["id"], {"etiquetas": new})
            fixed += 1
    return fixed


def _diagnose_dependencies():
    deps = {
        "streamlit": importlib.util.find_spec("streamlit") is not None,
        "pandas": importlib.util.find_spec("pandas") is not None,
        "plotly": importlib.util.find_spec("plotly") is not None,
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "requests": importlib.util.find_spec("requests") is not None,
        "beautifulsoup4/bs4": importlib.util.find_spec("bs4") is not None,
    }
    return deps


def render_diagnostico():
    st.subheader("🧰 Diagnóstico y mantenimiento")
    st.caption("Panel seguro para revisar salud de datos, columnas, dependencias, backups y reparaciones básicas.")

    db.init_db()
    obras = db.list_obras()

    with db.get_conn() as conn:
        counts = {table: _table_count(conn, table) for table in ["obras", "capitulos", "actividad", "personajes", "votos_personaje", "canons"]}
        missing_obras = _missing_columns(conn, "obras", db.OBRAS_COLUMNS)
        missing_canons = _missing_columns(conn, "canons", db.CANONS_COLUMNS)
        cols_obras = _columns(conn, "obras")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Obras", counts.get("obras", 0))
    c2.metric("Capítulos", counts.get("capitulos", 0))
    c3.metric("Actividad", counts.get("actividad", 0))
    c4.metric("Canons", counts.get("canons", 0))

    st.markdown("### Estado técnico")
    if db.DB_PATH.exists():
        st.success(f"Base de datos encontrada: {db.DB_PATH}")
    else:
        st.warning("La base de datos todavía no existe.")

    deps = _diagnose_dependencies()
    dep_df = pd.DataFrame([{"dependencia": k, "ok": "✅" if v else "❌"} for k, v in deps.items()])
    st.dataframe(dep_df, use_container_width=True, hide_index=True)

    if missing_obras or missing_canons:
        st.warning("Hay columnas faltantes. Pulsa reparar esquema para ejecutar migración segura.")
        if missing_obras:
            st.write("Faltan en obras:", ", ".join(missing_obras))
        if missing_canons:
            st.write("Faltan en canons:", ", ".join(missing_canons))
    else:
        st.success("Columnas principales completas.")

    with st.expander("Ver columnas de obras", expanded=False):
        st.write(", ".join(cols_obras))

    st.markdown("### Backups")
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Crear backup .db", key="backup_db"):
            target = _backup_db()
            if target:
                st.success(f"Backup creado: {target}")
            else:
                st.error("No existe base de datos para respaldar.")
    with b2:
        if st.button("Exportar JSON", key="backup_json"):
            target = _backup_json()
            st.success(f"JSON creado: {target}")
    with b3:
        if st.button("Exportar CSV", key="backup_csv"):
            target = _backup_csv()
            st.success(f"CSV creado: {target}")

    if BACKUP_DIR.exists():
        backups = sorted(BACKUP_DIR.glob("*"), reverse=True)[:10]
        if backups:
            st.caption("Últimos backups/exportaciones")
            for path in backups:
                st.write(f"- {path.name}")

    st.markdown("### Reparaciones seguras")
    r1, r2, r3 = st.columns(3)
    with r1:
        if st.button("Reparar esquema", key="repair_schema"):
            db.init_db()
            st.success("Esquema revisado y migrado si hacía falta.")
    with r2:
        if st.button("Recalcular progreso básico", key="repair_progress"):
            count = _repair_progress(obras)
            st.success(f"Obras corregidas: {count}")
    with r3:
        if st.button("Normalizar etiquetas", key="normalize_tags"):
            count = _normalize_all_tags(obras)
            st.success(f"Obras normalizadas: {count}")

    st.markdown("### Duplicados detectados")
    dupes = _find_duplicates(obras)
    if not dupes:
        st.success("No se detectaron duplicados exactos por link o título+autor.")
    else:
        st.warning(f"Duplicados posibles: {len(dupes)}")
        for original, duplicate in dupes[:50]:
            with st.container(border=True):
                st.write(f"Original: **{original.get('titulo')}** — id {original.get('id')}")
                st.write(f"Duplicado: **{duplicate.get('titulo')}** — id {duplicate.get('id')}")
                st.caption("No se fusiona ni borra automáticamente desde aquí para evitar pérdida de datos.")

    st.markdown("### Resumen rápido de datos")
    if obras:
        df = pd.DataFrame(obras)
        cols = [c for c in ["id", "titulo", "tipo", "estado_lectura", "temporada_actual", "temporada_total", "capitulos_vistos", "capitulos_publicados", "calidad_datos", "ao3_tracking"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no hay obras para diagnosticar.")
