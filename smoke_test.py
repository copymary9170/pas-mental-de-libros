import importlib
import sys
from pathlib import Path

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "src/database.py",
    "src/ao3_utils.py",
    "src/pages/ao3_updates.py",
    "src/pages/buscador.py",
    "src/pages/importar_link.py",
    "src/pages/diagnostico.py",
    "src/pages/cronometro.py",
    "src/pages/capitulos.py",
    "src/pages/calendario.py",
    "src/pages/reportes.py",
    "src/pages/canons.py",
    "src/pages/fanfiction.py",
]

MODULES = [
    "src.database",
    "src.styles",
    "src.utils",
    "src.ao3_utils",
    "src.pages.ao3_updates",
    "src.pages.buscador",
    "src.pages.importar_link",
    "src.pages.diagnostico",
    "src.pages.cronometro",
    "src.pages.capitulos",
    "src.pages.calendario",
    "src.pages.reportes",
    "src.pages.canons",
    "src.pages.fanfiction",
]

REQUIRED_PACKAGES = ["streamlit", "pandas", "plotly", "PIL", "requests", "bs4"]


def check_files():
    missing = [path for path in REQUIRED_FILES if not Path(path).exists()]
    if missing:
        raise AssertionError("Missing files: " + ", ".join(missing))
    print("OK files")


def check_packages():
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except Exception:
            missing.append(package)
    if missing:
        raise AssertionError("Missing packages: " + ", ".join(missing))
    print("OK packages")


def check_modules():
    failed = []
    for module in MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:
            failed.append(f"{module}: {exc}")
    if failed:
        raise AssertionError("Import failures:\n" + "\n".join(failed))
    print("OK modules")


def check_database_schema():
    import src.database as db
    db.init_db()
    with db.get_conn() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(obras)").fetchall()}
    required = set(db.OBRAS_COLUMNS.keys())
    missing = sorted(required - columns)
    if missing:
        raise AssertionError("Missing DB columns: " + ", ".join(missing))
    print("OK database schema")


def main():
    check_files()
    check_packages()
    check_modules()
    check_database_schema()
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
