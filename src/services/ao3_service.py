from __future__ import annotations

from src.ao3_utils import es_link_ao3, extraer_ao3_info


def es_obra_ao3(obra: dict) -> bool:
    """
    Verificación segura y compatible para obras AO3.
    """

    link = obra.get("link_original") or obra.get("url_fuente") or ""

    return es_link_ao3(link)



def obtener_link_ao3(obra: dict) -> str:
    """
    Obtiene el link principal AO3 preservando compatibilidad.
    """

    return obra.get("link_original") or obra.get("url_fuente") or ""



def revisar_obra_ao3(link: str) -> dict:
    """
    Wrapper conservador para extracción AO3.
    No modifica comportamiento existente.
    """

    if not link:
        return {
            "ok": False,
            "error": "Link AO3 vacío.",
        }

    return extraer_ao3_info(link)
