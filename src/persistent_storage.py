import base64
import os
from pathlib import Path

import requests


def _secret(name, default=""):
    value = os.environ.get(name, default)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def config():
    repo = _secret("GITHUB_BACKUP_REPO", "copymary9170/pas-mental-de-libros")
    token = _secret("GITHUB_BACKUP_TOKEN", "")
    branch = _secret("GITHUB_BACKUP_BRANCH", "main")
    path = _secret("GITHUB_BACKUP_DB_PATH", "persist/biblioteca.db")
    return {"repo": repo, "token": token, "branch": branch, "path": path}


def is_enabled():
    cfg = config()
    return bool(cfg.get("repo") and cfg.get("token") and cfg.get("path"))


def status_message():
    cfg = config()
    if not cfg.get("token"):
        return "Persistencia GitHub desactivada: falta GITHUB_BACKUP_TOKEN en Streamlit Secrets."
    return f"Persistencia GitHub activa: {cfg['repo']} → {cfg['path']}"


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _content_url(cfg):
    return f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"


def _get_remote(cfg):
    url = _content_url(cfg)
    response = requests.get(url, headers=_headers(cfg["token"]), params={"ref": cfg["branch"]}, timeout=20)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def restore_db_if_needed(db_path):
    """Descarga la DB persistente si la DB local no existe o está vacía.

    No pisa una base local que ya tenga datos para evitar pérdidas accidentales.
    """
    if not is_enabled():
        return False, status_message()
    db_path = Path(db_path)
    if db_path.exists() and db_path.stat().st_size > 0:
        return False, "DB local existente; no se restauró para no sobrescribir datos locales."
    cfg = config()
    remote = _get_remote(cfg)
    if not remote:
        return False, "No existe respaldo remoto todavía. Se creará al guardar datos."
    content = remote.get("content", "")
    if not content:
        return False, "El respaldo remoto está vacío."
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(base64.b64decode(content))
    return True, "DB restaurada desde respaldo remoto de GitHub."


def upload_db(db_path, message="Actualizar respaldo persistente de biblioteca"):
    """Sube la DB local a GitHub. Si no está configurado, no hace nada."""
    if not is_enabled():
        return False, status_message()
    db_path = Path(db_path)
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False, "No hay DB local para subir."
    cfg = config()
    remote = _get_remote(cfg)
    sha = remote.get("sha") if remote else None
    payload = {
        "message": message,
        "content": base64.b64encode(db_path.read_bytes()).decode("utf-8"),
        "branch": cfg["branch"],
    }
    if sha:
        payload["sha"] = sha
    response = requests.put(_content_url(cfg), headers=_headers(cfg["token"]), json=payload, timeout=30)
    response.raise_for_status()
    return True, "DB sincronizada con GitHub."
