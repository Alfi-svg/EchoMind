from __future__ import annotations

import json
from pathlib import Path

import soundfile as sf
from vosk import Model, KaldiRecognizer

class EnglishASRError(RuntimeError):
    pass

class EnglishASR:
    def __init__(self, vosk_model_dir: Path):
        if not vosk_model_dir.exists():
            raise EnglishASRError(
                "English ASR (Vosk) model folder not found.\n"
                f"Expected: {vosk_model_dir}\n"
                "Place an offline Vosk English model there."
            )
        self.model = Model(str(vosk_model_dir))

    def transcribe_wav(self, wav_path: Path) -> str:
        audio, sr = sf.read(str(wav_path), dtype="int16")
        if sr != 16000:
            raise EnglishASRError(f"Expected 16k wav. Got sr={sr}")
        if audio.ndim == 2:
            audio = audio.mean(axis=1).astype("int16")

        rec = KaldiRecognizer(self.model, 16000)
        rec.SetWords(True)

        # stream in chunks
        chunk_size = 4000
        buf = audio.tobytes()
        for i in range(0, len(buf), chunk_size * 2):
            rec.AcceptWaveform(buf[i : i + chunk_size * 2])

        final = json.loads(rec.FinalResult())
        return (final.get("text") or "").strip()
