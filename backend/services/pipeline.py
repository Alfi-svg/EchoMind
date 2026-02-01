from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.config import (
    BN_SAVEDMODEL_DIR, BN_VOCAB_PATH, BN_PREPROCESS_PATH,
    VOSK_MODEL_DIR, RESULTS_DIR,
)
from backend.services.audio_extract import extract_wav_16k
from backend.services.lang_detect import detect_language_from_text_hint
from backend.services.stt_bn_tf import BanglaASR
from backend.services.stt_en_vosk import EnglishASR, EnglishASRError
from backend.services.text_clean import clean_text
from backend.services.sentiment_bd import sentiment_bd
from backend.services.explain_phase1 import build_sentiment_explanation

from backend.services.motion_features import analyze_motion, timeline_to_csv, timeline_to_json
from backend.services.stats import summarize_timeline

# Phase-1 LLM (already added)
from backend.services.llm_social_context import generate_social_context_explanation

# ✅ Phase-2 LLM Coach (NEW)
from backend.services.llm_motion_coach import generate_motion_coach_feedback

logger = logging.getLogger(__name__)

_bn_asr_singleton: BanglaASR | None = None
_en_asr_singleton: EnglishASR | None = None


def get_bn_asr() -> BanglaASR:
    global _bn_asr_singleton
    if _bn_asr_singleton is None:
        _bn_asr_singleton = BanglaASR(
            savedmodel_dir=BN_SAVEDMODEL_DIR,
            vocab_path=BN_VOCAB_PATH,
            preprocess_path=BN_PREPROCESS_PATH,
        )
    return _bn_asr_singleton


def get_en_asr() -> EnglishASR:
    global _en_asr_singleton
    if _en_asr_singleton is None:
        _en_asr_singleton = EnglishASR(VOSK_MODEL_DIR)
    return _en_asr_singleton


def run_full_pipeline(video_path: Path, text_hint: str | None = None) -> dict:
    logger.info("Running pipeline for %s", video_path)

    # -----------------------------
    # Phase-1: audio + STT
    # -----------------------------
    wav_path = extract_wav_16k(video_path)

    lang_pref = detect_language_from_text_hint(text_hint)  # "bn" | "en" | "auto"
    transcript = ""
    language = "bn"

    if lang_pref == "bn":
        transcript = get_bn_asr().transcribe_wav(wav_path)
        language = "bn"
    elif lang_pref == "en":
        transcript = _transcribe_en_or_raise(wav_path)
        language = "en"
    else:
        bn_text = get_bn_asr().transcribe_wav(wav_path)
        bn_text = clean_text(bn_text)
        if _looks_bangla(bn_text) and len(bn_text) >= 6:
            transcript = bn_text
            language = "bn"
        else:
            transcript = _transcribe_en_or_raise(wav_path)
            language = "en"

    transcript = clean_text(transcript)

    # Rule-based sentiment (stable, explainable)
    sent = sentiment_bd(transcript)

    # Rule-based explanation
    explanation = build_sentiment_explanation(transcript, sent)

    # LLM Social Context (safe fallback)
    llm_ctx = generate_social_context_explanation(
        text=transcript,
        sentiment_label=sent.label,
        sentiment_score=sent.score,
        matched_positive=sent.matched_positive,
        matched_negative=sent.matched_negative,
        language=language,
    )

    phase1 = {
        "language": language,
        "transcript": transcript,
        "sentiment": sent.label,
        "sentiment_score": sent.score,
        "explanation": explanation,
        "social_context_ok": llm_ctx.ok,
        "social_context_model": llm_ctx.model,
        "social_context_explanation": llm_ctx.explanation,
        "social_context_flags": llm_ctx.flags,
        "social_context_warning": llm_ctx.warning,
    }

    # -----------------------------
    # Phase-2: motion analysis
    # -----------------------------
    timeline, phase2_expl = analyze_motion(video_path)
    stats = summarize_timeline(timeline)

    key = video_path.stem
    csv_path = RESULTS_DIR / f"{key}_timeline.csv"
    json_path = RESULTS_DIR / f"{key}_timeline.json"

    csv_path.write_text(timeline_to_csv(timeline), encoding="utf-8")
    json_path.write_text(timeline_to_json(timeline), encoding="utf-8")

    # Load timeline JSON into memory so frontend can draw graphs
    timeline_data = None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)
    except Exception:
        timeline_data = None

    # ✅ NEW: Phase-2 AI Coach (Ollama) — safe fallback
    coach = generate_motion_coach_feedback(
        stats=stats,
        motion_explanation=phase2_expl if isinstance(phase2_expl, dict) else None,
    )

    phase2 = {
        "timeline_csv_path": str(csv_path),
        "timeline_json_path": str(json_path),
        "timeline_data": timeline_data,
        "stats": stats,
        "explanation": phase2_expl,

        # ✅ NEW fields for UI
        "coach_ok": coach.ok,
        "coach_model": coach.model,
        "coach_feedback": coach.feedback,
        "coach_json": coach.json_data,
        "coach_warning": coach.warning,
    }

    return {"phase1": phase1, "phase2": phase2}


def _looks_bangla(text: str) -> bool:
    return any("\u0980" <= ch <= "\u09FF" for ch in text)


def _transcribe_en_or_raise(wav_path: Path) -> str:
    try:
        return get_en_asr().transcribe_wav(wav_path)
    except EnglishASRError as e:
        raise RuntimeError(
            "English transcription requested/needed but Vosk model is missing.\n"
            f"{e}\n\n"
            "Fix: place an offline Vosk English model inside backend/models/en_vosk/model/"
        )
