from __future__ import annotations

import subprocess
from pathlib import Path

from backend.config import ALLOW_NET_DOWNLOAD, DOWNLOADS_DIR, YTDLP_BIN
from backend.services.video_ingest import IngestError


def download_video_from_url(url: str) -> Path:
    """
    Optional network download mode (DEV ONLY).
    Uses yt-dlp CLI (no API). Requires internet connection.
    """
    if not ALLOW_NET_DOWNLOAD:
        raise IngestError(
            "Network download disabled (offline mode). "
            "To enable: run with ALLOW_NET_DOWNLOAD=1"
        )

    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Output: downloads/<video_id>.mp4 (yt-dlp will fill %(id)s)
    outtmpl = str(DOWNLOADS_DIR / "%(id)s.%(ext)s")

    cmd = [
        YTDLP_BIN,
        "-f",
        "bv*+ba/best",
        "--merge-output-format",
        "mp4",
        "-o",
        outtmpl,
        url,
    ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip()
        raise IngestError(f"yt-dlp failed: {msg}")

    # Find newest file in downloads dir
    files = sorted(DOWNLOADS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise IngestError("Download succeeded but no output file found in downloads directory.")

    return files[0]
