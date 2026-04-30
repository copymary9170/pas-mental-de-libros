from pathlib import Path
import shutil
import uuid

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
