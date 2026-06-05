"""Runtime safety patch for Paz Mental dates.

Streamlit Cloud can run in a server timezone ahead of Venezuela. Some UI pages still
use date.today(), so they may send tomorrow's date when the user is still in
America/Caracas. This patch keeps saved activity dates from drifting into the
future.
"""

from datetime import date as _date

try:
    import src.database as _db
    from src.local_time import today_local
except Exception:  # pragma: no cover - never break app startup because of patching
    _db = None
    today_local = None


def _as_date(value):
    if value in [None, ""]:
        return None
    if isinstance(value, _date):
        return value
    try:
        return _date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def _clamp_future_date(value):
    if today_local is None:
        return value
    today = today_local()
    parsed = _as_date(value)
    if parsed is None:
        return str(today)
    if parsed > today:
        return str(today)
    return str(parsed)


def _patch_database_dates():
    if _db is None or getattr(_db, "_paz_venezuela_date_patch", False):
        return

    original_add_actividad = getattr(_db, "add_actividad", None)
    if original_add_actividad:
        def add_actividad_venezuela(data):
            data = dict(data or {})
            data["fecha"] = _clamp_future_date(data.get("fecha"))
            return original_add_actividad(data)
        _db.add_actividad = add_actividad_venezuela

    original_add_capitulo = getattr(_db, "add_capitulo", None)
    if original_add_capitulo:
        def add_capitulo_venezuela(data):
            data = dict(data or {})
            if data.get("fecha_lectura"):
                data["fecha_lectura"] = _clamp_future_date(data.get("fecha_lectura"))
            return original_add_capitulo(data)
        _db.add_capitulo = add_capitulo_venezuela

    original_add_tiempo_obra = getattr(_db, "add_tiempo_obra", None)
    if original_add_tiempo_obra:
        def add_tiempo_obra_venezuela(obra_id, minutos, fecha=None):
            return original_add_tiempo_obra(obra_id, minutos, _clamp_future_date(fecha))
        _db.add_tiempo_obra = add_tiempo_obra_venezuela

    original_update_obra = getattr(_db, "update_obra", None)
    if original_update_obra:
        def update_obra_venezuela(obra_id, data):
            data = dict(data or {})
            for field in [
                "fecha_ultimo_capitulo_visto",
                "fecha_ultima_sesion",
                "fecha_inicio",
                "fecha_fin",
            ]:
                if data.get(field):
                    data[field] = _clamp_future_date(data.get(field))
            return original_update_obra(obra_id, data)
        _db.update_obra = update_obra_venezuela

    _db._paz_venezuela_date_patch = True


_patch_database_dates()
