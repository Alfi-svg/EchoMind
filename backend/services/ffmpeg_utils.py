from __future__ import annotations

import subprocess
from pathlib import Path

class FFmpegError(RuntimeError):
    pass

def run_cmd(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise FFmpegError(
            f"Command failed: {' '.join(cmd)}\n\nSTDERR:\n{proc.stderr.strip()}"
        )

def ffmpeg_extract_audio_to_wav_16k_mono(video_path: Path, wav_out: Path) -> None:
    # -vn: no video, mono, 16k
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        str(wav_out),
    ]
    run_cmd(cmd)

def ffprobe_duration_seconds(video_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise FFmpegError(proc.stderr.strip())
    try:
        return float(proc.stdout.strip())
    except Exception as e:
        raise FFmpegError(f"Could not parse duration: {proc.stdout!r}") from e
