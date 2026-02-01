from __future__ import annotations

import hashlib
from pathlib import Path
from backend.config import ALLOWED_VIDEO_EXTS, UPLOADS_DIR, URL_CACHE_DIR

class IngestError(RuntimeError):
    pass

def validate_video_ext(path: Path) -> None:
    if path.suffix.lower() not in ALLOWED_VIDEO_EXTS:
        raise IngestError(f"Unsupported video format: {path.suffix}. Allowed: {sorted(ALLOWED_VIDEO_EXTS)}")

def save_upload_to_disk(filename: str, data: bytes) -> Path:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise IngestError(f"Unsupported upload extension: {ext}")

    out = UPLOADS_DIR / f"upload_{hashlib.sha256(data).hexdigest()[:16]}{ext}"
    out.write_bytes(data)
    return out

def url_to_cache_key(url: str) -> str:
    # deterministic, safe offline key
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:24]

def resolve_url_offline(url: str) -> Path:
    """
    Offline-safe URL support:
    - We DO NOT download anything.
    - We only map the URL -> cache filename and look in storage/url_cache.
    """
    key = url_to_cache_key(url)
    # user must place a file named like: <key>.mp4 (or mkv/avi/etc)
    candidates = list(URL_CACHE_DIR.glob(f"{key}.*"))
    if not candidates:
        raise IngestError(
            "Offline URL mode: video not found in local cache.\n"
            f"Put the video file into: backend/storage/url_cache/\n"
            f"Rename it to: {key}.mp4 (or .mkv/.avi etc)\n"
            f"URL key: {key}"
        )
    # pick the first valid ext
    for c in candidates:
        if c.suffix.lower() in ALLOWED_VIDEO_EXTS:
            return c
    raise IngestError("Cache file exists but extension is not supported.")
