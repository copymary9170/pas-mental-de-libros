from pathlib import Path
import re
import shutil
import uuid
from urllib.parse import urlparse, unquote
import requests

UPLOADS_DIR = Path("uploads")
PORTADAS_DIR = UPLOADS_DIR / "portadas"
RESPALDOS_DIR = UPLOADS_DIR / "respaldos"
PERSIST_DIR = Path("persist")
PERSIST_PORTADAS_DIR = PERSIST_DIR / "portadas"


def ensure_dirs():
    PORTADAS_DIR.mkdir(parents=True, exist_ok=True)
    RESPALDOS_DIR.mkdir(parents=True, exist_ok=True)
    PERSIST_PORTADAS_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file, folder: Path):
    if uploaded_file is None:
        return None
    ensure_dirs()
    suffix = Path(uploaded_file.name).suffix
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    target = folder / safe_name
    with target.open("wb") as f:
        shutil.copyfileobj(uploaded_file, f)
    if Path(folder) == PORTADAS_DIR:
        try:
            persistent_target = PERSIST_PORTADAS_DIR / safe_name
            shutil.copy2(target, persistent_target)
            try:
                import src.persistent_storage as persistent_storage
                persistent_storage.upload_file(persistent_target, f"persist/portadas/{safe_name}", message="Guardar portada persistente")
            except Exception:
                pass
        except Exception:
            pass
    return str(target)


def read_uploaded_text(uploaded_file):
    if uploaded_file is None:
        return ""
    data = uploaded_file.getvalue()
    for enc in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            return data.decode(enc)
        except Exception:
            pass
    return data.decode("utf-8", errors="ignore")


def dividir_capitulos(texto):
    if not texto or not texto.strip():
        return []
    pattern = re.compile(r"(?im)^\s*(?:#{1,3}\s*)?(?:cap[ií]tulo|chapter|chap|episodio|episode|ep\.?|cap\.?)[\s:#.-]*(\d+)(?:\s*[-:–—.]\s*(.*))?$")
    matches = list(pattern.finditer(texto))
    chapters = []
    if not matches:
        return [{"numero": 1, "titulo": "Capitulo 1", "texto": texto.strip()}]
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto)
        numero = int(match.group(1))
        titulo = (match.group(2) or f"Capitulo {numero}").strip()
        contenido = texto[start:end].strip()
        chapters.append({"numero": numero, "titulo": titulo, "texto": contenido})
    return chapters


def parse_tags(text):
    if not text:
        return ""
    return ", ".join(sorted({tag.strip().lower() for tag in text.split(",") if tag.strip()}))


def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def detectar_plataforma(url):
    host = urlparse(url).netloc.lower()
    if "kakao" in host:
        return "KakaoPage"
    if "naver" in host:
        return "Naver Series/Webtoon"
    if "munpia" in host:
        return "Munpia"
    if "ridibooks" in host or "ridi" in host:
        return "Ridi"
    if "novelupdates" in host:
        return "NovelUpdates"
    if "webnovel" in host:
        return "Webnovel"
    return host or "link externo"


def extraer_titulo_desde_url(url):
    try:
        path = unquote(urlparse(url).path)
        parts = [p for p in path.split("/") if p]
        if parts:
            raw = parts[-1]
            raw = re.sub(r"[-_]+", " ", raw)
            raw = re.sub(r"\d+", "", raw).strip()
            return raw[:80] if raw else "Obra importada por link"
    except Exception:
        pass
    return "Obra importada por link"


def importar_desde_link(url):
    plataforma = detectar_plataforma(url)
    titulo = extraer_titulo_desde_url(url)
    etiquetas = f"importado por link, webnovel, novela web, {plataforma.lower()}"
    if plataforma in ["KakaoPage", "Naver Series/Webtoon", "Munpia", "Ridi"]:
        etiquetas += ", coreana, hangul"
    return {"titulo": titulo, "autor": plataforma, "tipo": "Webnovel", "anio": "", "sinopsis": f"Importada desde enlace externo: {url}", "portada_path": "", "capitulo_total": 0, "temporada_total": 1, "etiquetas": etiquetas, "estado_publicacion": "No aplica", "link_original": url}


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
            results.append({"titulo": doc.get("title") or "Sin titulo", "autor": ", ".join(doc.get("author_name", [])[:3]), "tipo": "Libro", "anio": doc.get("first_publish_year"), "sinopsis": "", "portada_path": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else "", "capitulo_total": 0, "temporada_total": 1, "etiquetas": "openlibrary, importado"})
        return results
    except Exception:
        return []


def buscar_manga_jikan(query):
    if not query:
        return []
    try:
        r = requests.get("https://api.jikan.moe/v4/manga", params={"q": query, "limit": 15}, timeout=12)
        r.raise_for_status()
        results = []
        for item in r.json().get("data", []):
            title = item.get("title") or item.get("title_english") or "Sin titulo"
            images = item.get("images", {}).get("jpg", {})
            authors = item.get("authors") or []
            genres = item.get("genres") or []
            manga_type = item.get("type") or "Manga"
            tipo = "Novela ligera" if "Novel" in manga_type else "Manga"
            results.append({"titulo": title, "autor": ", ".join([a.get("name", "") for a in authors[:3] if a.get("name")]), "tipo": tipo, "anio": item.get("published", {}).get("from", "")[:4], "sinopsis": item.get("synopsis") or "", "portada_path": images.get("large_image_url") or images.get("image_url") or "", "capitulo_total": item.get("chapters") or 0, "temporada_total": 1, "etiquetas": ", ".join([g.get("name", "").lower() for g in genres if g.get("name")] + ["jikan", "manga", "importado"]), "estado_publicacion": "Terminada" if item.get("status") == "Finished" else "En emision"})
        return results
    except Exception:
        return []


def buscar_webnovel_openlibrary(query):
    results = buscar_libros_openlibrary(query)
    for item in results:
        item["tipo"] = "Webnovel"
        item["etiquetas"] = f"{item.get('etiquetas','')}, webnovel, novela web"
    return results


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
            results.append({"titulo": show.get("name") or "Sin titulo", "autor": show.get("network", {}).get("name") if show.get("network") else (show.get("webChannel", {}) or {}).get("name", ""), "tipo": "Serie", "anio": (show.get("premiered") or "")[:4], "sinopsis": clean_html(show.get("summary")), "portada_path": image.get("original") or image.get("medium") or "", "capitulo_total": 0, "temporada_total": 1, "etiquetas": ", ".join([g.lower() for g in genres] + ["tvmaze", "importado"]), "estado_publicacion": "Terminada" if show.get("status") == "Ended" else "En emision"})
        return results
    except Exception:
        return []


def _tmdb_search(query, media_type, api_key, korean=False):
    if not query or not api_key:
        return []
    try:
        endpoint = "movie" if media_type == "movie" else "tv"
        params = {"api_key": api_key, "query": query, "language": "es-ES", "include_adult": "false"}
        if korean and media_type == "tv":
            params["region"] = "KR"
        r = requests.get(f"https://api.themoviedb.org/3/search/{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        results = []
        for item in r.json().get("results", [])[:15]:
            title = item.get("title") or item.get("name") or "Sin titulo"
            date = item.get("release_date") or item.get("first_air_date") or ""
            poster = item.get("poster_path")
            original_lang = item.get("original_language") or ""
            tags = ["tmdb", "importado"]
            tags.append("pelicula" if media_type == "movie" else "serie")
            if korean or original_lang == "ko":
                tags.extend(["kdrama", "corea", "kakao referencia"])
            results.append({"titulo": title, "autor": "TMDB", "tipo": "Pelicula" if media_type == "movie" else "Serie", "anio": date[:4], "sinopsis": item.get("overview") or "", "portada_path": f"https://image.tmdb.org/t/p/w500{poster}" if poster else "", "capitulo_total": 1 if media_type == "movie" else 0, "temporada_total": 1, "etiquetas": ", ".join(tags), "estado_publicacion": "Terminada" if media_type == "movie" else "No aplica"})
        return results
    except Exception:
        return []


def buscar_peliculas_tmdb(query, api_key=""):
    return _tmdb_search(query, "movie", api_key)


def buscar_series_tmdb(query, api_key=""):
    return _tmdb_search(query, "tv", api_key)


def buscar_kdramas_tmdb(query, api_key=""):
    return _tmdb_search(query, "tv", api_key, korean=True)


def buscar_peliculas_itunes(query):
    if not query:
        return []
    try:
        r = requests.get("https://itunes.apple.com/search", params={"term": query, "media": "movie", "entity": "movie", "limit": 15, "country": "US"}, timeout=10)
        r.raise_for_status()
        results = []
        for item in r.json().get("results", []):
            artwork = item.get("artworkUrl100", "")
            if artwork:
                artwork = artwork.replace("100x100bb", "600x900bb")
            results.append({"titulo": item.get("trackName") or "Sin titulo", "autor": item.get("artistName") or item.get("primaryGenreName") or "", "tipo": "Pelicula", "anio": (item.get("releaseDate") or "")[:4], "sinopsis": item.get("longDescription") or item.get("shortDescription") or "", "portada_path": artwork, "capitulo_total": 1, "temporada_total": 1, "etiquetas": ", ".join(filter(None, [str(item.get("primaryGenreName") or "").lower(), "itunes", "pelicula", "importado"])), "estado_publicacion": "Terminada"})
        return results
    except Exception:
        return []
