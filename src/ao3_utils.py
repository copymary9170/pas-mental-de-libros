import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def es_link_ao3(url):
    return bool(url and "archiveofourown.org/works/" in str(url))


def extraer_ao3_info(url):
    """Lee datos publicos basicos de una obra de AO3.

    No descarga capitulos ni contenido completo. Solo intenta leer metadata visible:
    titulo, autor, capitulos publicados/totales, estado y fecha de actualizacion.
    """
    if not es_link_ao3(url):
        return {"ok": False, "error": "No parece un link de AO3."}

    headers = {
        "User-Agent": "PazMentalPersonalTracker/1.0 (+personal reading tracker; manual checks only)",
        "Accept-Language": "es,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code >= 400:
            return {"ok": False, "error": f"AO3 respondió HTTP {resp.status_code}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    soup = BeautifulSoup(resp.text, "html.parser")

    titulo = ""
    h2 = soup.select_one("h2.title")
    if h2:
        titulo = h2.get_text(" ", strip=True)

    autor = ""
    autor_el = soup.select_one("h3.byline")
    if autor_el:
        autor = autor_el.get_text(" ", strip=True)

    chapters_text = ""
    dd_chapters = soup.select_one("dd.chapters")
    if dd_chapters:
        chapters_text = dd_chapters.get_text(" ", strip=True)

    publicados = 0
    total = 0
    completo = False
    if chapters_text:
        match = re.search(r"(\d+)\s*/\s*(\d+|\?)", chapters_text)
        if match:
            publicados = int(match.group(1))
            total_raw = match.group(2)
            total = int(total_raw) if total_raw.isdigit() else 0
            completo = bool(total and publicados >= total)

    updated = ""
    dd_status = soup.select_one("dd.status")
    if dd_status:
        updated = dd_status.get_text(" ", strip=True)

    published = ""
    dd_published = soup.select_one("dd.published")
    if dd_published:
        published = dd_published.get_text(" ", strip=True)

    return {
        "ok": True,
        "url": url,
        "titulo": titulo,
        "autor": autor,
        "capitulos_publicados": publicados,
        "capitulos_totales": total,
        "completo": completo,
        "fecha_actualizacion": updated,
        "fecha_publicacion": published,
        "revisado_en": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
