from __future__ import annotations

import numpy as np
from backend.services.motion_features import FrameFeature

def summarize_timeline(timeline: list[FrameFeature]) -> dict:
    if not timeline:
        return {
            "count": 0,
            "averages": {},
            "variability": {},
            "notes": ["No frames were analyzed. Video may be unreadable or too short."]
        }

    def arr(name: str) -> np.ndarray:
        return np.array([getattr(f, name) for f in timeline], dtype=np.float32)

    feats = ["posture_openness", "hand_gesture_activity", "eye_contact_approx", "movement_pacing"]

    averages = {k: float(arr(k).mean()) for k in feats}
    variability = {k: float(arr(k).std()) for k in feats}

    # Human-friendly levels
    def level(x: float) -> str:
        if x >= 0.70:
            return "high"
        if x >= 0.40:
            return "medium"
        return "low"

    levels = {k: level(averages[k]) for k in feats}

    return {
        "count": len(timeline),
        "averages": averages,
        "variability": variability,
        "levels": levels
    }
