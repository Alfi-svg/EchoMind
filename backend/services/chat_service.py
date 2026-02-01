from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.services.ollama_client import ollama_chat, OllamaReply
from backend.services.chat_memory import load_history, append_turn


@dataclass
class ChatResult:
    ok: bool
    model: str
    reply: str
    warning: str = ""


def _system_prompt(mood: str) -> str:
    mood = (mood or "default").strip().lower()

    base = (
        "You are EchoMind Chatbot. You are helpful, clear, and safe. "
        "Keep answers practical and structured. If user asks something unsafe, refuse politely. "
        "If user asks for code, give copy-paste-ready code."
    )

    if mood == "coach":
        return base + " Act like a strict but friendly coach. Give actionable steps and short checklists."
    if mood == "student":
        return base + " Explain like to a university student. Use simple English and examples."
    if mood == "bangla":
        return base + " If user writes Bangla, reply in Bangla. If user writes English, reply in English."
    return base


def chat_with_memory(
    *,
    session_file: Path,
    user_text: str,
    mood: str,
    model: str = "llama3.1:8b",
    max_history_turns: int = 16,
) -> ChatResult:
    user_text = (user_text or "").strip()
    if not user_text:
        return ChatResult(ok=True, model=model, reply="Type something first 🙂")

    # load memory
    hist = load_history(session_file)
    hist = hist[-max_history_turns:]  # last N turns

    messages: list[dict] = [{"role": "system", "content": _system_prompt(mood)}]
    for t in hist:
        messages.append({"role": t.role, "content": t.content})

    messages.append({"role": "user", "content": user_text})

    # call ollama
    r: OllamaReply = ollama_chat(model=model, messages=messages)

    # update memory
    append_turn(session_file, "user", user_text)
    if r.ok:
        append_turn(session_file, "assistant", r.text)

    return ChatResult(ok=r.ok, model=r.model, reply=r.text, warning=r.warning)
