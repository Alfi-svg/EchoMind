from __future__ import annotations

from pathlib import Path
from backend.config import UPLOADS_DIR, URL_CACHE_DIR, AUDIO_DIR, RESULTS_DIR, TEMP_DIR

def ensure_dirs() -> None:
    for d in (UPLOADS_DIR, URL_CACHE_DIR, AUDIO_DIR, RESULTS_DIR, TEMP_DIR):
        d.mkdir(parents=True, exist_ok=True)

def safe_unlink(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        # best effort cleanup
        pass
