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

LAST_UPLOAD_STATUS = {"ok": None, "message": ""}


def ensure_dirs():
    PORTADAS_DIR.mkdir(parents=True, exist_ok=True)
    RESPALDOS_DIR.mkdir(parents=True, exist_ok=True)
    PERSIST_PORTADAS_DIR.mkdir(parents=True, exist_ok=True)


def get_last_upload_status():
    return dict(LAST_UPLOAD_STATUS)


def save_uploaded_file(uploaded_file, folder: Path):
    if uploaded_file is None:
        return None
    ensure_dirs()
    suffix = Path(uploaded_file.name).suffix
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    target = folder / safe_name
    with target.open("wb") as f:
        shutil.copyfileobj(uploaded_file, f)
    LAST_UPLOAD_STATUS.update({"ok": None, "message": f"Archivo guardado localmente: {target}"})
    if Path(folder) == PORTADAS_DIR:
        persistent_target = PERSIST_PORTADAS_DIR / safe_name
        try:
            shutil.copy2(target, persistent_target)
        except Exception as exc:
            LAST_UPLOAD_STATUS.update({"ok": False, "message": f"❌ Portada local guardada, pero no pude copiarla a persist/portadas: {exc}"})
            return str(target)
        try:
            import src.persistent_storage as persistent_storage
            ok, msg = persistent_storage.upload_file(persistent_target, f"persist/portadas/{safe_name}", message="Guardar portada persistente")
            LAST_UPLOAD_STATUS.update({"ok": bool(ok), "message": ("✅ Portada respaldada en GitHub." if ok else "❌ Portada guardada localmente, pero NO respaldada en GitHub. ") + str(msg)})
        except Exception as exc:
            LAST_UPLOAD_STATUS.update({"ok": False, "message": f"❌ Portada guardada localmente, pero NO respaldada en GitHub: {exc}"})
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
