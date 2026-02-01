from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass


@dataclass
class OllamaReply:
    ok: bool
    model: str
    text: str
    warning: str = ""


def ollama_chat(
    *,
    model: str,
    messages: list[dict],
    host: str = "http://127.0.0.1:11434",
    timeout_s: int = 120,
) -> OllamaReply:
    """
    Calls Ollama HTTP API (offline local).
    messages format:
      [{"role":"system|user|assistant","content":"..."}]
    """
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.6,
            "num_predict": 450,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            # Ollama returns: {"message":{"role":"assistant","content":"..."} , ...}
            content = ""
            if isinstance(data, dict):
                msg = data.get("message") or {}
                content = (msg.get("content") or "").strip()
            return OllamaReply(ok=True, model=model, text=content or "(no response)")
    except urllib.error.URLError as e:
        return OllamaReply(
            ok=False,
            model=model,
            text="(fallback) Ollama is unavailable.",
            warning=f"Ollama HTTP error: {e}",
        )
    except Exception as e:
        return OllamaReply(
            ok=False,
            model=model,
            text="(fallback) Ollama call failed.",
            warning=str(e),
        )
