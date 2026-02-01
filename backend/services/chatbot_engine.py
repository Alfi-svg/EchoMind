from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from backend.services.chatbot_memory import load_memory, save_memory
from backend.services.chatbot_prompt import build_system_prompt

CHAT_STORAGE = Path("backend/storage/chat_memory")
CHAT_STORAGE.mkdir(parents=True, exist_ok=True)

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT_SEC", "30"))


def run_chatbot(session_id: str, user_message: str, mood: str) -> dict:
    """
    Offline Chatbot using Ollama.
    Safe, memory-based, ChatGPT-like.
    """

    history = load_memory(session_id)
    system_prompt = build_system_prompt(mood)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    prompt = json.dumps(messages, ensure_ascii=False)

    try:
        proc = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=OLLAMA_TIMEOUT,
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)

        reply = proc.stdout.strip()

        # Save memory
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        save_memory(session_id, history)

        return {
            "ok": True,
            "model": OLLAMA_MODEL,
            "reply": reply,
        }

    except Exception as e:
        return {
            "ok": False,
            "model": OLLAMA_MODEL,
            "reply": "Chatbot is unavailable right now.",
            "error": str(e),
        }
