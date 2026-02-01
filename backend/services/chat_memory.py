from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ChatTurn:
    role: str   # "user" | "assistant"
    content: str


def _safe_json_load(path: Path) -> Any:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_history(session_file: Path) -> list[ChatTurn]:
    obj = _safe_json_load(session_file)
    if not isinstance(obj, dict):
        return []
    items = obj.get("messages")
    if not isinstance(items, list):
        return []
    out: list[ChatTurn] = []
    for it in items:
        if isinstance(it, dict):
            role = str(it.get("role") or "")
            content = str(it.get("content") or "")
            if role in ("user", "assistant") and content.strip():
                out.append(ChatTurn(role=role, content=content.strip()))
    return out


def save_history(session_file: Path, history: list[ChatTurn]) -> None:
    session_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "messages": [{"role": t.role, "content": t.content} for t in history][-80:]  # limit
    }
    session_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_turn(session_file: Path, role: str, content: str) -> None:
    hist = load_history(session_file)
    hist.append(ChatTurn(role=role, content=content.strip()))
    save_history(session_file, hist)
