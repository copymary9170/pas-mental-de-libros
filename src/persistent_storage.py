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
    covers_path = _secret("GITHUB_BACKUP_COVERS_PATH", "persist/portadas")
    return {"repo": repo, "token": token, "branch": branch, "path": path, "covers_path": covers_path}


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


def _content_url(cfg, path=None):
    return f"https://api.github.com/repos/{cfg['repo']}/contents/{path or cfg['path']}"


def _get_remote(cfg, path=None):
    url = _content_url(cfg, path)
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


def upload_file(local_path, remote_path, message="Actualizar archivo persistente"):
    """Sube un archivo individual a GitHub usando la misma persistencia."""
    if not is_enabled():
        return False, status_message()
    local_path = Path(local_path)
    if not local_path.exists() or local_path.stat().st_size == 0:
        return False, "No hay archivo local para subir."
    cfg = config()
    remote_path = str(remote_path).replace("\\", "/").lstrip("/")
    remote = _get_remote(cfg, remote_path)
    sha = remote.get("sha") if isinstance(remote, dict) else None
    payload = {
        "message": message,
        "content": base64.b64encode(local_path.read_bytes()).decode("utf-8"),
        "branch": cfg["branch"],
    }
    if sha:
        payload["sha"] = sha
    response = requests.put(_content_url(cfg, remote_path), headers=_headers(cfg["token"]), json=payload, timeout=30)
    response.raise_for_status()
    return True, f"Archivo sincronizado: {remote_path}"


def restore_cover_images(portadas_dir="uploads/portadas", persist_dir="persist/portadas"):
    """Restaura portadas respaldadas en GitHub hacia uploads/portadas.

    La app guarda las rutas de portada como uploads/portadas/<archivo>. Si Streamlit
    borra el disco local, esta función reconstruye esa carpeta desde persist/portadas
    del repositorio.
    """
    if not is_enabled():
        return False, status_message()
    cfg = config()
    covers_path = str(cfg.get("covers_path") or "persist/portadas").strip("/")
    remote_listing = _get_remote(cfg, covers_path)
    if not remote_listing:
        return False, "No hay portadas persistentes en GitHub todavía."
    if isinstance(remote_listing, dict):
        remote_listing = [remote_listing]
    portadas_dir = Path(portadas_dir)
    persist_dir = Path(persist_dir)
    portadas_dir.mkdir(parents=True, exist_ok=True)
    persist_dir.mkdir(parents=True, exist_ok=True)
    restored = 0
    skipped = 0
    for item in remote_listing:
        if item.get("type") != "file":
            continue
        name = item.get("name") or ""
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            continue
        target = portadas_dir / name
        persist_target = persist_dir / name
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            if not persist_target.exists():
                try:
                    persist_target.write_bytes(target.read_bytes())
                except Exception:
                    pass
            continue
        file_remote = _get_remote(cfg, f"{covers_path}/{name}")
        content = file_remote.get("content", "") if isinstance(file_remote, dict) else ""
        if not content:
            continue
        data = base64.b64decode(content)
        target.write_bytes(data)
        persist_target.write_bytes(data)
        restored += 1
    return True, f"Portadas restauradas: {restored}. Ya existentes: {skipped}."


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
