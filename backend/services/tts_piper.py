from __future__ import annotations

import os
import subprocess
from pathlib import Path


class TTSError(Exception):
    pass


def tts_piper(reply_text: str, out_wav: Path) -> Path:
    """
    Offline TTS using Piper CLI.

    Requirements:
      - piper installed (brew install piper) OR binary available
      - Model path set via PIPER_MODEL (a .onnx file)
    Env:
      PIPER_BIN   : default 'piper'
      PIPER_MODEL : path to voice model .onnx
    """
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    piper_model = os.environ.get("PIPER_MODEL", "").strip()
    if not piper_model:
        raise TTSError("PIPER_MODEL env is not set. Example: export PIPER_MODEL=/path/to/voice.onnx")

    piper_bin = os.environ.get("PIPER_BIN", "piper").strip()

    cmd = [
        piper_bin,
        "--model", piper_model,
        "--output_file", str(out_wav),
    ]

    try:
        p = subprocess.run(cmd, input=reply_text, capture_output=True, text=True, check=False)
    except Exception as e:
        raise TTSError(f"Failed to run piper: {e}")

    if p.returncode != 0:
        raise TTSError(f"piper error:\n{p.stderr or p.stdout}")

    if not out_wav.exists():
        raise TTSError("TTS output file not created.")
    return out_wav
