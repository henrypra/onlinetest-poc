"""Exportiert die von FastAPI generierte OpenAPI-Spec als openapi.yaml.

Aufruf aus dem Projektverzeichnis:  python scripts/export_openapi.py
Nach API-Änderungen erneut ausführen, damit der Snapshot im Repo aktuell bleibt.
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

target = Path(__file__).resolve().parent.parent / "openapi.yaml"
spec = app.openapi()
target.write_text(
    yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8"
)
print(f"OpenAPI-Snapshot geschrieben: {target}")
