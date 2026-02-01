from __future__ import annotations

import re

# Simple, explainable heuristic: if Bangla Unicode block dominates => bn else en
BN_RE = re.compile(r"[\u0980-\u09FF]")

def detect_language_from_text_hint(text_hint: str | None) -> str:
    if not text_hint:
        return "auto"
    s = text_hint.strip()
    if not s:
        return "auto"
    bn_chars = len(BN_RE.findall(s))
    return "bn" if bn_chars >= max(3, len(s) // 10) else "en"
