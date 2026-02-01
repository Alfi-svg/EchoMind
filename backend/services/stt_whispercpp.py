import os
import subprocess
import tempfile
import logging

class STTError(Exception):
    pass

def stt_whispercpp(input_path: str, language: str = "auto") -> str:
    """
    Converts audio to 16k wav and runs whisper-cli.
    """
    WHISPER_BIN = os.getenv("WHISPER_BIN", "/opt/homebrew/bin/whisper-cli")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", os.path.expanduser("~/models/whisper/ggml-small.bin"))

    if not os.path.exists(WHISPER_BIN):
        raise STTError(f"Whisper binary not found at {WHISPER_BIN}")

    # 1. Prepare temporary WAV file (Whisper requirement: 16kHz mono)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_path = tmp_wav.name

    try:
        # Convert input to 16kHz Mono WAV using ffmpeg
        conversion_cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path
        ]
        subprocess.run(conversion_cmd, check=True, capture_output=True)

        # 2. Run Whisper CLI
        whisper_cmd = [
            WHISPER_BIN,
            "-m", WHISPER_MODEL,
            "-f", wav_path,
            "-nt", # no timestamps
            "-l", language if language != "auto" else "en" 
        ]
        
        result = subprocess.run(whisper_cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        logging.error(f"STT Subprocess Error: {e.stderr}")
        raise STTError(f"STT process failed: {e.stderr}")
    except Exception as e:
        raise STTError(f"Unexpected STT error: {str(e)}")
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)