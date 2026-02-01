from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class Phase2CoachResult:
    ok: bool
    model: str
    feedback: dict[str, Any]
    warning: str | None = None


def _model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


def _timeout() -> int:
    try:
        return int(os.environ.get("OLLAMA_TIMEOUT_SEC", "120"))
    except Exception:
        return 120


def _build_prompt(stats: dict[str, Any], sampling_fps: int) -> str:
    # Keep prompt short to avoid slow generation
    return f"""
You are an offline Presentation Coach AI.
You will analyze motion features and give feedback with evidence.

Rules:
- Output STRICT JSON only. No markdown.
- Use evidence from the provided averages/variability/levels.
- Mention limitations: camera angle, lighting, occlusion, fps={sampling_fps}.
- Do NOT claim medical/psychological diagnosis.
- Emotion: only "engagement indicator" based on movement/eye/gesture (approx).

Input stats JSON:
{json.dumps(stats, ensure_ascii=False)}

Return JSON schema:
{{
  "summary": "2-4 lines overall coaching summary",
  "scores": {{
    "eye_contact": 0-100,
    "gesture_use": 0-100,
    "posture_openness": 0-100,
    "pacing_stability": 0-100,
    "overall_delivery": 0-100
  }},
  "evidence": [
    "Evidence line referencing exact metric values (e.g., averages.eye_contact_approx=0.53 => medium eye-contact)"
  ],
  "strengths": ["...","..."],
  "improvements": ["...","..."],
  "engagement_indicator": {{
    "label": "low|medium|high",
    "reason": "short reason"
  }},
  "limitations": ["...","..."]
}}
""".strip()


def generate_phase2_coach_feedback(stats: dict[str, Any], sampling_fps: int) -> Phase2CoachResult:
    model = _model()
    timeout_s = _timeout()

    prompt = _build_prompt(stats=stats, sampling_fps=sampling_fps)

    try:
        proc = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            env={**os.environ, "OLLAMA_NUM_CTX": os.environ.get("OLLAMA_NUM_CTX", "1024")},
        )
    except subprocess.TimeoutExpired:
        return Phase2CoachResult(ok=False, model=model, feedback={}, warning=f"Ollama timeout after {timeout_s}s")
    except Exception as e:
        return Phase2CoachResult(ok=False, model=model, feedback={}, warning=str(e))

    if proc.returncode != 0:
        return Phase2CoachResult(ok=False, model=model, feedback={}, warning=(proc.stderr or "").strip())

    raw = (proc.stdout or "").strip()

    # extract JSON
    first = raw.find("{")
    last = raw.rfind("}")
    if first == -1 or last == -1:
        return Phase2CoachResult(ok=False, model=model, feedback={}, warning="LLM returned non-JSON output")

    try:
        obj = json.loads(raw[first:last + 1])
        return Phase2CoachResult(ok=True, model=model, feedback=obj, warning=None)
    except Exception:
        return Phase2CoachResult(ok=False, model=model, feedback={}, warning="JSON parse failed")
