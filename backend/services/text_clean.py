from __future__ import annotations

import re

SPACE_RE = re.compile(r"\s+")
PUNCT_FIX_RE = re.compile(r"\s+([,.;:!?])")

def clean_text(s: str) -> str:
    s = s.strip()
    s = SPACE_RE.sub(" ", s)
    s = PUNCT_FIX_RE.sub(r"\1", s)
    return s
