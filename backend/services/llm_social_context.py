from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMContextResult:
    ok: bool
    model: str
    explanation: str
    flags: dict[str, Any]
    warning: str | None = None


def _pick_model_name() -> str:
    """
    Choose model from env, fallback to llama3.1:8b (your choice).
    You can set:
      export OLLAMA_MODEL=llama3.1:8b
    """
    return os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


def _pick_timeout_sec() -> int:
    """
    Timeout for LLM call so your pipeline never hangs.
    """
    try:
        return int(os.environ.get("OLLAMA_TIMEOUT_SEC", "90"))
    except Exception:
        return 90


def _interpret_score_bucket(score: float) -> str:
    """
    Convert score (-1..+1) to a user-facing bucket that you can show in UI.
    """
    if score >= 0.25:
        return "high (positive)"
    if score <= -0.25:
        return "high (negative)"
    return "neutral/mixed"


def build_social_context_prompt(
    *,
    text: str,
    sentiment_label: str,
    sentiment_score: float,
    matched_positive: list[str],
    matched_negative: list[str],
    language: str,
) -> str:
    """
    Prompt focuses on Bangladesh social/cultural acceptability and slang awareness.
    It must NOT change label/score; only justify and add context.
    Output is strict JSON to avoid frontend parsing issues.
    """

    score_bucket = _interpret_score_bucket(sentiment_score)
    return f"""
You analyze Bangladesh social context and International Context.You are an AI "Social Context & Responsible Language" analyst for Bangladesh and out world country.
You MUST be neutral, professional, and educational.
Return STRICT JSON only.
Your job:
1) Explain WHY the given sentiment score looks {score_bucket}.
2) Identify slang/offensive/inappropriate wording (if any).
3) Explain using Bangladesh social norms and acceptable public discourse.
4) Provide a safe, non-legal disclaimer: "This is NOT legal advice."
5) DO NOT change the sentiment label or score.
6) Do NOT claim exact law section numbers; use general references only.

Text: \"\"\"{text}\"\"\"
Sentiment: {sentiment_label}  Score: {sentiment_score:.2f}

JSON schema:
{{
 "score_interpretation":"1 sentence",
 "social_context_analysis":"2-4 sentences",
 "flags":{{"has_slang_or_offensive":true/false,"example_terms":[],"risk_level":"low|medium|high"}},
 
}}
""".strip()


def ollama_generate_json(prompt: str, model: str, timeout_sec: int) -> dict[str, Any]:
    """
    Calls Ollama locally via CLI (no network, no API key).
    IMPORTANT FIX:
      - DO NOT use '-p' flag (your ollama version doesn't support it)
      - Send prompt via STDIN instead.
    """

    cmd = ["ollama", "run", model]

    logger.info("Ollama call: model=%s timeout=%ss", model, timeout_sec)

    try:
      proc = subprocess.run(
    cmd,
    input=prompt,
    capture_output=True,
    text=True,
    timeout=timeout_sec,
    env={**os.environ, "OLLAMA_NUM_CTX": "1024"}  # ✅ smaller context = faster
)

    except FileNotFoundError as e:
        raise RuntimeError("Ollama CLI not found. Install Ollama and ensure 'ollama' is in PATH.") from e

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        raise RuntimeError(f"Ollama failed (code={proc.returncode}). stderr={stderr} stdout={stdout}")

    raw = (proc.stdout or "").strip()

    # Try JSON parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Recover by finding first/last braces
        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last != -1 and last > first:
            try:
                return json.loads(raw[first:last + 1])
            except Exception:
                pass
        raise RuntimeError(f"Ollama output is not valid JSON. Raw output:\n{raw}")


def generate_social_context_explanation(
    *,
    text: str,
    sentiment_label: str,
    sentiment_score: float,
    matched_positive: list[str],
    matched_negative: list[str],
    language: str,
) -> LLMContextResult:
    """
    Safe wrapper: NEVER throws.
    If Ollama is unavailable -> returns ok=False with fallback warning.
    """
    model = _pick_model_name()
    timeout_sec = _pick_timeout_sec()

    text = (text or "").strip()
    if not text:
        return LLMContextResult(
            ok=False,
            model=model,
            explanation="No text provided for social context analysis.",
            flags={"has_slang_or_offensive": False, "example_terms": [], "tone": "mixed", "risk_level": "low"},
            warning="Empty text. Skipping LLM social context analysis.",
        )

    prompt = build_social_context_prompt(
        text=text,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        matched_positive=matched_positive,
        matched_negative=matched_negative,
        language=language,
    )

    try:
        data = ollama_generate_json(prompt, model=model, timeout_sec=timeout_sec)

        score_interp = str(data.get("score_interpretation", "")).strip()
        social_ctx = str(data.get("social_context_analysis", "")).strip()
        bd_ref = str(data.get("bangladesh_context_reference", "")).strip()
        limitation = str(data.get("limitation_note", "")).strip()
        disclaimer = str(data.get("disclaimer", "This is NOT legal advice.")).strip()
        flags = data.get("flags", {}) if isinstance(data.get("flags", {}), dict) else {}

        explanation_parts: list[str] = []

        if score_interp:
            explanation_parts += ["Score Interpretation:", score_interp, ""]
        if social_ctx:
            explanation_parts += ["Social Context Analysis:", social_ctx, ""]
        if bd_ref:
            explanation_parts += ["Bangladesh Context Reference:", bd_ref, ""]
        if limitation:
            explanation_parts += ["Limitation Note:", limitation, ""]

        explanation_parts += ["Disclaimer:", disclaimer]

        return LLMContextResult(
            ok=True,
            model=model,
            explanation="\n".join(explanation_parts).strip(),
            flags=flags,
            warning=None,
        )

    except subprocess.TimeoutExpired:
        return LLMContextResult(
            ok=False,
            model=model,
            explanation="LLM social-context analysis timed out. Showing rule-based explanation only.",
            flags={"has_slang_or_offensive": False, "example_terms": [], "tone": "mixed", "risk_level": "medium"},
            warning=f"Ollama timeout after {timeout_sec}s.",
        )
    except Exception as e:
        return LLMContextResult(
            ok=False,
            model=model,
            explanation="LLM social-context analysis unavailable. Showing rule-based explanation only.",
            flags={"has_slang_or_offensive": False, "example_terms": [], "tone": "mixed", "risk_level": "medium"},
            warning=str(e),
        )
