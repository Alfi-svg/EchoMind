from __future__ import annotations

from pathlib import Path
from backend.config import AUDIO_DIR
from backend.services.ffmpeg_utils import ffmpeg_extract_audio_to_wav_16k_mono

def extract_wav_16k(video_path: Path) -> Path:
    wav_out = AUDIO_DIR / (video_path.stem + "_16k_mono.wav")
    ffmpeg_extract_audio_to_wav_16k_mono(video_path, wav_out)
    return wav_out
