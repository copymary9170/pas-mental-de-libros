from pathlib import Path
import re
import shutil
import uuid
import requests

UPLOADS_DIR = Path("uploads")
PORTADAS_DIR = UPLOADS_DIR / "portadas"
RESPALDOS_DIR = UPLOADS_DIR / "respaldos"


def ensure_dirs():
    PORTADAS_DIR.mkdir(parents=True, exist_ok=True)
    RESPALDOS_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file, folder: Path):
    if uploaded_file is None:
        return None
    ensure_dirs()
    suffix = Path(uploaded_file.name).suffix
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    target = folder / safe_name
    with target.open("wb") as f:
        shutil.copyfileobj(uploaded_file, f)
    return str(target)


def parse_tags(text):
    if not text:
        return ""
    return ", ".join(sorted({tag.strip().lower() for tag in text.split(",") if tag.strip()}))


def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def buscar_portada_openlibrary(titulo, autor=""):
    if not titulo:
        return None
    try:
        params = {"title": titulo, "limit": 1}
        if autor:
            params["author"] = autor
        r = requests.get("https://openlibrary.org/search.json", params=params, timeout=8)
        r.raise_for_status()
        docs = r.json().get("docs", [])
        if not docs:
            return None
        cover_id = docs[0].get("cover_i")
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except Exception:
        return None


def buscar_libros_openlibrary(query):
    if not query:
        return []
    try:
        r = requests.get("https://openlibrary.org/search.json", params={"q": query, "limit": 10}, timeout=10)
        r.raise_for_status()
        results = []
        for doc in r.json().get("docs", []):
            cover_id = doc.get("cover_i")
            results.append({
                "titulo": doc.get("title") or "Sin titulo",
                "autor": ", ".join(doc.get("author_name", [])[:3]),
                "tipo": "Libro",
                "anio": doc.get("first_publish_year"),
                "sinopsis": "",
                "portada_path": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else "",
                "capitulo_total": 0,
                "temporada_total": 1,
                "etiquetas": "openlibrary, importado",
            })
        return results
    except Exception:
        return []


def buscar_series_tvmaze(query):
    if not query:
        return []
    try:
        r = requests.get("https://api.tvmaze.com/search/shows", params={"q": query}, timeout=10)
        r.raise_for_status()
        results = []
        for item in r.json()[:10]:
            show = item.get("show", {})
            image = show.get("image") or {}
            genres = show.get("genres") or []
            results.append({
                "titulo": show.get("name") or "Sin titulo",
                "autor": show.get("network", {}).get("name") if show.get("network") else (show.get("webChannel", {}) or {}).get("name", ""),
                "tipo": "Serie",
                "anio": (show.get("premiered") or "")[:4],
                "sinopsis": clean_html(show.get("summary")),
                "portada_path": image.get("original") or image.get("medium") or "",
                "capitulo_total": 0,
                "temporada_total": 1,
                "etiquetas": ", ".join([g.lower() for g in genres] + ["tvmaze", "importado"]),
                "estado_publicacion": "Terminada" if show.get("status") == "Ended" else "En emision",
            })
        return results
    except Exception:
        return []


def _tmdb_search(query, media_type, api_key):
    if not query or not api_key:
        return []
    try:
        endpoint = "movie" if media_type == "movie" else "tv"
        r = requests.get(
            f"https://api.themoviedb.org/3/search/{endpoint}",
            params={"api_key": api_key, "query": query, "language": "es-ES", "include_adult": "false"},
            timeout=10,
        )
        r.raise_for_status()
        results = []
        for item in r.json().get("results", [])[:15]:
            title = item.get("title") or item.get("name") or "Sin titulo"
            date = item.get("release_date") or item.get("first_air_date") or ""
            poster = item.get("poster_path")
            results.append({
                "titulo": title,
                "autor": "TMDB",
                "tipo": "Pelicula" if media_type == "movie" else "Serie",
                "anio": date[:4],
                "sinopsis": item.get("overview") or "",
                "portada_path": f"https://image.tmdb.org/t/p/w500{poster}" if poster else "",
                "capitulo_total": 1 if media_type == "movie" else 0,
                "temporada_total": 1,
                "etiquetas": "tmdb, pelicula, importado" if media_type == "movie" else "tmdb, serie, importado",
                "estado_publicacion": "Terminada" if media_type == "movie" else "No aplica",
            })
        return results
    except Exception:
        return []


def buscar_peliculas_tmdb(query, api_key=""):
    return _tmdb_search(query, "movie", api_key)


def buscar_series_tmdb(query, api_key=""):
    return _tmdb_search(query, "tv", api_key)


def buscar_peliculas_itunes(query):
    if not query:
        return []
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "media": "movie", "entity": "movie", "limit": 15, "country": "US"},
            timeout=10,
        )
        r.raise_for_status()
        results = []
        for item in r.json().get("results", []):
            artwork = item.get("artworkUrl100", "")
            if artwork:
                artwork = artwork.replace("100x100bb", "600x900bb")
            results.append({
                "titulo": item.get("trackName") or "Sin titulo",
                "autor": item.get("artistName") or item.get("primaryGenreName") or "",
                "tipo": "Pelicula",
                "anio": (item.get("releaseDate") or "")[:4],
                "sinopsis": item.get("longDescription") or item.get("shortDescription") or "",
                "portada_path": artwork,
                "capitulo_total": 1,
                "temporada_total": 1,
                "etiquetas": ", ".join(filter(None, [str(item.get("primaryGenreName") or "").lower(), "itunes", "pelicula", "importado"])),
                "estado_publicacion": "Terminada",
            })
        return results
    except Exception:
        return []
