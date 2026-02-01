from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

MODELS_DIR = BASE_DIR / "models"
STORAGE_DIR = BASE_DIR / "storage"

UPLOADS_DIR = STORAGE_DIR / "uploads"
URL_CACHE_DIR = STORAGE_DIR / "url_cache"
AUDIO_DIR = STORAGE_DIR / "audio"
RESULTS_DIR = STORAGE_DIR / "results"
TEMP_DIR = STORAGE_DIR / "temp"

# NEW: downloads dir for optional URL download mode (yt-dlp output)
DOWNLOADS_DIR = STORAGE_DIR / "downloads"

# -----------------------------
# Bangla TF ASR (SavedModel)
# -----------------------------
BN_SAVEDMODEL_DIR = MODELS_DIR / "bn_asr_savedmodel"
BN_VOCAB_PATH = MODELS_DIR / "bn_vocab" / "vocab.json"
BN_PREPROCESS_PATH = MODELS_DIR / "bn_preprocess" / "preprocess.json"

# -----------------------------
# English ASR (Vosk)
# -----------------------------
VOSK_ROOT_DIR = MODELS_DIR / "en_vosk"
VOSK_MODEL_DIR = VOSK_ROOT_DIR / "model"

# -----------------------------
# Ingest rules
# -----------------------------
ALLOWED_VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
MAX_UPLOAD_MB = 500

# -----------------------------
# URL mode (IMPORTANT)
# -----------------------------
# Default STRICT OFFLINE:
# - URL input will be resolved ONLY from URL_CACHE_DIR
# Optional DEV mode:
# - Set environment variable ALLOW_NET_DOWNLOAD=1
# - Then system may download from URL using yt-dlp (requires internet)
ALLOW_NET_DOWNLOAD = os.environ.get("ALLOW_NET_DOWNLOAD", "0") == "1"

# yt-dlp executable name (in case you want to override)
YTDLP_BIN = os.environ.get("YTDLP_BIN", "yt-dlp")

# ffmpeg executable name (override if needed)
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")

# -----------------------------
# Motion analysis (Phase-2)
# -----------------------------
FRAME_SAMPLE_FPS = 5  # sample frames per second for Phase-2
