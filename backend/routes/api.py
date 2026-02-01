from __future__ import annotations

from fastapi import APIRouter, UploadFile, Form
from backend.services.storage import ensure_dirs
from backend.services.video_ingest import save_upload_to_disk, resolve_url_offline
from backend.services.pipeline import run_full_pipeline

router = APIRouter(prefix="/api")

@router.post("/run")
async def run_api(
    video_file: UploadFile | None = None,
    video_url: str | None = Form(default=None),
    text_hint: str | None = Form(default=None),
):
    ensure_dirs()

    if video_file and video_file.filename:
        data = await video_file.read()
        video_path = save_upload_to_disk(video_file.filename, data)
    elif video_url and video_url.strip():
        video_path = resolve_url_offline(video_url.strip())
    else:
        return {"error": "Provide video_file or video_url."}

    try:
        result = run_full_pipeline(video_path=video_path, text_hint=text_hint)
        return result
    except Exception as e:
        return {"error": str(e)}
