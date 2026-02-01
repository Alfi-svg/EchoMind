from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, Form, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from backend.services.storage import ensure_dirs
from backend.services.pipeline import run_full_pipeline
from backend.services.video_ingest import save_upload_to_disk, resolve_url_offline, IngestError
from backend.services.url_downloader import download_video_from_url
from backend.services.chat_memory import load_history
from backend.services.chat_service import chat_with_memory

# Correct Imports
from backend.services.stt_whispercpp import stt_whispercpp, STTError
from backend.services.tts_piper import tts_piper, TTSError

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")
CHAT_DIR = Path("backend/storage/chat_sessions")
VOICE_DIR = Path("backend/storage/chat_voice")
TTS_DIR = Path("backend/storage/chat_tts")

def _get_or_make_session_id(request: Request, provided: str | None) -> str:
    sid = (provided or "").strip()
    if sid: return sid
    cookie_sid = request.cookies.get("echomind_chat_session")
    if cookie_sid: return cookie_sid.strip()
    return "s_" + uuid.uuid4().hex[:16]

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    ensure_dirs()
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/run", response_class=HTMLResponse)
async def run_from_web(request: Request, video_file: UploadFile|None=None, video_url: str|None=Form(default=None), text_hint: str|None=Form(default=None)):
    ensure_dirs()
    video_path = None
    try:
        if video_file and video_file.filename:
            data = await video_file.read()
            video_path = save_upload_to_disk(video_file.filename, data)
        elif video_url and video_url.strip():
            url = video_url.strip()
            try:
                video_path = resolve_url_offline(url)
            except IngestError:
                video_path = download_video_from_url(url)
        else:
            return templates.TemplateResponse("result.html", {"request": request, "error": "No input provided."})
        
        result = run_full_pipeline(video_path=video_path, text_hint=text_hint)
        return templates.TemplateResponse("result.html", {"request": request, "result": result, "error": None})
    except Exception as e:
        return templates.TemplateResponse("result.html", {"request": request, "error": str(e)})

@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, session_id: str|None=None, mood: str="default"):
    ensure_dirs()
    sid = _get_or_make_session_id(request, session_id)
    session_file = CHAT_DIR / f"{sid}.json"
    messages = load_history(session_file)
    resp = templates.TemplateResponse("chat.html", {"request": request, "session_id": sid, "mood": mood, "messages": messages})
    resp.set_cookie("echomind_chat_session", sid)
    return resp

@router.post("/chat", response_class=HTMLResponse)
async def chat_from_web(request: Request, message: str|None=Form(default=None), mood: str|None=Form(default="default"), session_id: str|None=Form(default=None)):
    sid = _get_or_make_session_id(request, session_id)
    session_file = CHAT_DIR / f"{sid}.json"
    r = chat_with_memory(session_file=session_file, user_text=(message or "").strip(), mood=mood or "default", model="llama3.1:8b")
    messages = load_history(session_file)
    return templates.TemplateResponse("chat.html", {"request": request, "session_id": sid, "mood": mood, "messages": messages, "reply": r.reply})
@router.post("/chat/reset", response_class=HTMLResponse)
async def chat_reset(request: Request, session_id: str | None = Form(default=None)):
    """
    Delete the session JSON file and reload the chat page.
    """
    ensure_dirs()
    sid = _get_or_make_session_id(request, session_id)
    session_file = CHAT_DIR / f"{sid}.json"

    # Delete the session file if it exists
    if session_file.exists():
        try:
            session_file.unlink()
        except Exception as e:
            print(f"Error deleting session file: {e}")

    # Redirect or Render clean chat page
    # Redirect kora bhalo jate URL-ta clean thake
    messages = []
    resp = templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": sid,
            "mood": "default",
            "messages": messages,
            "reply": "Chat history cleared!",
            "warning": ""
        },
    )
    return resp
@router.post("/chat/voice")
async def chat_voice(request: Request, audio: UploadFile=File(...), mood: str|None=Form(default="default"), session_id: str|None=Form(default=None), language: str|None=Form(default="auto")):
    ensure_dirs()
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    TTS_DIR.mkdir(parents=True, exist_ok=True)
    sid = _get_or_make_session_id(request, session_id)
    session_file = CHAT_DIR / f"{sid}.json"

    data = await audio.read()
    in_path = VOICE_DIR / f"{sid}_{uuid.uuid4().hex[:8]}.webm"
    in_path.write_bytes(data)

    try:
        transcript = stt_whispercpp(in_path, language=language)
        if not transcript:
            return JSONResponse({"ok": False, "error": "No speech detected."}, status_code=400)

        r = chat_with_memory(session_file=session_file, user_text=transcript, mood=mood or "default", model="llama3.1:8b")
        
        audio_url = None
        try:
            out_wav = tts_piper(r.reply, TTS_DIR / f"{sid}_{uuid.uuid4().hex[:8]}.wav")
            audio_url = f"/generated/chat_tts/{out_wav.name}"
        except Exception: pass 

        return {"ok": True, "transcript": transcript, "reply_text": r.reply, "reply_audio_url": audio_url}
    except STTError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    finally:
        if in_path.exists(): in_path.unlink()

    