from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMCoachResult:
    ok: bool
    model: str
    feedback: str
    json_data: dict[str, Any]
    warning: str | None = None


def _pick_model_name() -> str:
    # You already use llama3.1:8b (keep it)
    return os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


def _pick_timeout_sec() -> int:
    # Phase-2 coach prompt can be a bit heavier; give more time
    try:
        return int(os.environ.get("OLLAMA_TIMEOUT_SEC", "60"))
    except Exception:
        return 60


def build_motion_coach_prompt(
    *,
    stats: dict[str, Any],
    motion_explanation: dict[str, Any] | None,
) -> str:
    """
    Bangladesh-context, explainable coaching feedback.
    Returns STRICT JSON only.
    Keeps it short so llama3.1:8b finishes faster.
    """

    # Keep only important fields to reduce tokens
    compact = {
        "averages": stats.get("averages", {}),
        "variability": stats.get("variability", {}),
        "levels": stats.get("levels", {}),
        "count": stats.get("count", None),
    }

    limitations = []
    if isinstance(motion_explanation, dict):
        lim = motion_explanation.get("limitations")
        if isinstance(lim, list):
            limitations = lim[:6]

    return f"""
You are an "AI Presentation Coach" for Bangladesh context.
You analyze motion features (NOT personal identity). You must be respectful, non-judgmental, and actionable.

Given:
- feature averages (0..1)
- feature variability (0..1)
- levels labels
- known limitations (camera angle, lighting, occlusion)

Your task:
1) Give a short overall rating (A/B/C) for presentation delivery based on motion stability + engagement.
2) Explain posture openness, gesture activity, pacing, and eye-contact approximation.
3) Give 3–6 actionable improvement tips (Bangladesh classroom/debate/presentation friendly).
4) Mention limitations clearly (approx eye-contact, camera angle, lighting).
5) Output STRICT JSON only.

Input JSON:
{json.dumps(compact, ensure_ascii=False)}

Known limitations:
{json.dumps(limitations, ensure_ascii=False)}

Return STRICT JSON ONLY:
{{
  "overall_rating": "A|B|C",
  "summary": "2-4 sentences",
  "insights": {{
    "posture_openness": "1-2 sentences",
    "hand_gesture_activity": "1-2 sentences",
    "movement_pacing": "1-2 sentences",
    "eye_contact_approx": "1-2 sentences (must say approximation)"
  }},
  "tips": ["tip1", "tip2", "tip3"],
  "limitations": ["lim1", "lim2"],
  "disclaimer": "This is an approximation and not a medical or legal judgment."
}}
""".strip()


def _ollama_run(prompt: str, model: str, timeout_sec: int) -> str:
    """
    IMPORTANT FIX:
    Your Ollama CLI version showed: unknown shorthand flag '-p'
    So we DO NOT use -p.
    We pass the prompt as a normal argument.
    """
    cmd = ["ollama", "run", model, prompt]

    logger.info("Ollama motion-coach call: model=%s timeout=%ss", model, timeout_sec)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        raise RuntimeError(f"Ollama failed (code={proc.returncode}). stderr={stderr} stdout={stdout}")

    return (proc.stdout or "").strip()


def _parse_json_strict(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # recover by finding first/last braces
        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last != -1 and last > first:
            return json.loads(raw[first : last + 1])
        raise RuntimeError(f"LLM output is not valid JSON. Raw:\n{raw}")


def generate_motion_coach_feedback(
    *,
    stats: dict[str, Any],
    motion_explanation: dict[str, Any] | None,
) -> LLMCoachResult:
    """
    Safe wrapper: NEVER throws.
    """
    model = _pick_model_name()
    timeout_sec = _pick_timeout_sec()

    # Guard
    if not isinstance(stats, dict) or not stats:
        return LLMCoachResult(
            ok=False,
            model=model,
            feedback="No Phase-2 stats provided. Showing rule-based metrics only.",
            json_data={},
            warning="Empty stats input.",
        )

    prompt = build_motion_coach_prompt(stats=stats, motion_explanation=motion_explanation)

    try:
        raw = _ollama_run(prompt, model=model, timeout_sec=timeout_sec)
        data = _parse_json_strict(raw)

        # Build readable feedback for UI
        rating = str(data.get("overall_rating", "")).strip()
        summary = str(data.get("summary", "")).strip()
        insights = data.get("insights", {}) if isinstance(data.get("insights", {}), dict) else {}
        tips = data.get("tips", []) if isinstance(data.get("tips", []), list) else []
        lims = data.get("limitations", []) if isinstance(data.get("limitations", []), list) else []
        disclaimer = str(data.get("disclaimer", "")).strip()

        parts: list[str] = []
        if rating:
            parts.append(f"Overall Rating: {rating}")
            parts.append("")
        if summary:
            parts.append("Summary:")
            parts.append(summary)
            parts.append("")

        if insights:
            parts.append("Key Insights:")
            for k in ("posture_openness", "hand_gesture_activity", "movement_pacing", "eye_contact_approx"):
                if k in insights:
                    parts.append(f"- {k.replace('_',' ').title()}: {str(insights[k]).strip()}")
            parts.append("")

        if tips:
            parts.append("Actionable Tips:")
            for t in tips[:8]:
                parts.append(f"- {str(t).strip()}")
            parts.append("")

        if lims:
            parts.append("Limitations:")
            for l in lims[:8]:
                parts.append(f"- {str(l).strip()}")
            parts.append("")

        if disclaimer:
            parts.append("Disclaimer:")
            parts.append(disclaimer)

        return LLMCoachResult(
            ok=True,
            model=model,
            feedback="\n".join(parts).strip(),
            json_data=data if isinstance(data, dict) else {},
            warning=None,
        )

    except subprocess.TimeoutExpired:
        return LLMCoachResult(
            ok=False,
            model=model,
            feedback="LLM coach timed out. Showing rule-based Phase-2 metrics only.",
            json_data={},
            warning=f"Ollama timeout after {timeout_sec}s.",
        )
    except Exception as e:
        return LLMCoachResult(
            ok=False,
            model=model,
            feedback="LLM coach unavailable. Showing rule-based Phase-2 metrics only.",
            json_data={},
            warning=str(e),
        )
