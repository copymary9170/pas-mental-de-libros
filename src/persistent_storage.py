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
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


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
    if not is_enabled():
        return False, status_message()
    local_path = Path(local_path)
    if not local_path.exists() or local_path.stat().st_size == 0:
        return False, "No hay archivo local para subir."
    cfg = config()
    remote_path = str(remote_path).replace("\\", "/").lstrip("/")
    remote = _get_remote(cfg, remote_path)
    sha = remote.get("sha") if isinstance(remote, dict) else None
    payload = {"message": message, "content": base64.b64encode(local_path.read_bytes()).decode("utf-8"), "branch": cfg["branch"]}
    if sha:
        payload["sha"] = sha
    response = requests.put(_content_url(cfg, remote_path), headers=_headers(cfg["token"]), json=payload, timeout=30)
    response.raise_for_status()
    return True, f"Archivo sincronizado: {remote_path}"


def _decode_remote_file(cfg, remote_path):
    file_remote = _get_remote(cfg, remote_path)
    if isinstance(file_remote, dict):
        content = file_remote.get("content", "")
        if content:
            return base64.b64decode(content)
        download_url = file_remote.get("download_url")
        if download_url:
            response = requests.get(download_url, headers=_headers(cfg["token"]), timeout=30)
            response.raise_for_status()
            return response.content
    return None


def _remote_cover_items(cfg):
    covers_path = str(cfg.get("covers_path") or "persist/portadas").strip("/")
    remote_listing = _get_remote(cfg, covers_path)
    if not remote_listing:
        return covers_path, []
    if isinstance(remote_listing, dict):
        remote_listing = [remote_listing]
    items = []
    for item in remote_listing:
        if item.get("type") != "file":
            continue
        name = item.get("name") or ""
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            items.append(item)
    return covers_path, items


def _decode_cover_item(cfg, item):
    content = item.get("content", "") if isinstance(item, dict) else ""
    if content:
        return base64.b64decode(content)
    download_url = item.get("download_url") if isinstance(item, dict) else None
    if download_url:
        response = requests.get(download_url, headers=_headers(cfg["token"]), timeout=30)
        response.raise_for_status()
        return response.content
    covers_path = str(cfg.get("covers_path") or "persist/portadas").strip("/")
    name = item.get("name") or ""
    return _decode_remote_file(cfg, f"{covers_path}/{name}")


def restore_cover_images(portadas_dir="uploads/portadas", persist_dir="persist/portadas"):
    if not is_enabled():
        return False, status_message()
    cfg = config()
    covers_path, remote_listing = _remote_cover_items(cfg)
    if not remote_listing:
        return False, "No hay portadas persistentes en GitHub todavía."
    portadas_dir = Path(portadas_dir)
    persist_dir = Path(persist_dir)
    portadas_dir.mkdir(parents=True, exist_ok=True)
    persist_dir.mkdir(parents=True, exist_ok=True)
    restored = 0
    skipped = 0
    for item in remote_listing:
        name = item.get("name") or ""
        target = portadas_dir / name
        persist_target = persist_dir / name
        if target.exists() and target.stat().st_size > 0 and persist_target.exists() and persist_target.stat().st_size > 0:
            skipped += 1
            continue
        data = _decode_cover_item(cfg, item)
        if not data:
            continue
        target.write_bytes(data)
        persist_target.write_bytes(data)
        restored += 1
    return True, f"Portadas restauradas: {restored}. Ya existentes: {skipped}."


def restore_missing_cover_paths(obras, portadas_dir="uploads/portadas", persist_dir="persist/portadas"):
    if not is_enabled():
        return False, status_message()
    cfg = config()
    covers_path = str(cfg.get("covers_path") or "persist/portadas").strip("/")
    portadas_dir = Path(portadas_dir)
    persist_dir = Path(persist_dir)
    portadas_dir.mkdir(parents=True, exist_ok=True)
    persist_dir.mkdir(parents=True, exist_ok=True)
    remote_names = {}
    _, items = _remote_cover_items(cfg)
    for item in items:
        remote_names[item.get("name") or ""] = item
    needed = []
    for obra in obras or []:
        raw = str(obra.get("portada_path") or "")
        if not raw or raw.startswith(("http://", "https://")):
            continue
        local_path = Path(raw)
        if local_path.exists() and local_path.stat().st_size > 0:
            continue
        name = local_path.name
        if name and name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            needed.append((name, local_path))
    restored = 0
    missing = []
    for name, local_path in needed:
        item = remote_names.get(name)
        data = _decode_cover_item(cfg, item) if item else _decode_remote_file(cfg, f"{covers_path}/{name}")
        if not data:
            missing.append(name)
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        (persist_dir / name).write_bytes(data)
        restored += 1
    if missing:
        return False, f"Portadas restauradas: {restored}. No encontradas en GitHub: {', '.join(missing[:5])}"
    return True, f"Portadas faltantes restauradas desde GitHub: {restored}."


def reassign_missing_covers(db_module, portadas_dir="uploads/portadas", persist_dir="persist/portadas"):
    if not is_enabled():
        return False, status_message()

    cfg = config()
    covers_path, items = _remote_cover_items(cfg)

    if not items:
        return False, "No hay portadas en GitHub para reasignar."

    obras = db_module.list_obras()
    broken = []

    for obra in obras:
        raw = str(obra.get("portada_path") or "")
        if raw and not raw.startswith(("http://", "https://")) and not Path(raw).exists():
            broken.append(obra)

    if not broken:
        return True, "No hay rutas rotas para reasignar."

    portadas_dir = Path(portadas_dir)
    persist_dir = Path(persist_dir)
    portadas_dir.mkdir(parents=True, exist_ok=True)
    persist_dir.mkdir(parents=True, exist_ok=True)

    changes = []

    for idx, obra in enumerate(broken):
        item = items[idx % len(items)]
        name = item.get("name") or ""
        data = _decode_cover_item(cfg, item)

        if not data:
            continue

        local_path = portadas_dir / name
        persist_path = persist_dir / name

        local_path.write_bytes(data)
        persist_path.write_bytes(data)

        db_module.update_obra(obra["id"], {"portada_path": str(local_path)})
        changes.append(f"{obra.get('titulo') or obra.get('id')} -> {name}")

    if not changes:
        sample = ", ".join([item.get("name", "?") for item in items[:8]])
        return False, f"No pude reasignar ninguna portada. Portadas disponibles: {sample}"

    try:
        upload_db(db_module.DB_PATH, message="Reasignar portadas rotas")
    except Exception as exc:
        return True, "Portadas reasignadas, pero no pude sincronizar DB: " + str(exc) + ". Cambios: " + "; ".join(changes)

    return True, "Portadas reasignadas: " + "; ".join(changes)


def upload_db(db_path, message="Actualizar respaldo persistente de biblioteca"):
    if not is_enabled():
        return False, status_message()
    db_path = Path(db_path)
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False, "No hay DB local para subir."
    cfg = config()
    remote = _get_remote(cfg)
    sha = remote.get("sha") if remote else None
    payload = {"message": message, "content": base64.b64encode(db_path.read_bytes()).decode("utf-8"), "branch": cfg["branch"]}
    if sha:
        payload["sha"] = sha
    response = requests.put(_content_url(cfg), headers=_headers(cfg["token"]), json=payload, timeout=30)
    response.raise_for_status()
    return True, "DB sincronizada con GitHub."
