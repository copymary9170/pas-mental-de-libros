from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2
from typing import Any


def asegurar_archivo(path: str | Path, default_data: Any = None) -> Path:
    """
    Crea el archivo si no existe.
    Mantiene compatibilidad con la estructura actual.
    """

    archivo = Path(path)

    if not archivo.parent.exists():
        archivo.parent.mkdir(parents=True, exist_ok=True)

    if not archivo.exists():
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(default_data if default_data is not None else {}, f, ensure_ascii=False, indent=2)

    return archivo


def cargar_json(path: str | Path, default_data: Any = None) -> Any:
    """
    Carga JSON de forma segura.
    No modifica la lógica existente.
    """

    archivo = asegurar_archivo(path, default_data)

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_data if default_data is not None else {}


def guardar_json(path: str | Path, data: Any) -> None:
    """
    Guarda JSON preservando UTF-8.
    Compatible con el sistema actual.
    """

    archivo = asegurar_archivo(path)

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def backup_json(path: str | Path, backup_suffix: str = ".bak") -> Path | None:
    """
    Crea backup simple del archivo JSON.
    Operación no invasiva.
    """

    archivo = Path(path)

    if not archivo.exists():
        return None

    backup_path = archivo.with_suffix(archivo.suffix + backup_suffix)

    copy2(archivo, backup_path)

    return backup_path
