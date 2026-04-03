from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


FALLBACK_MESSAGE = "Your companion can't be reached right now."
DEFAULT_MODEL = "gpt-5"
MAX_HISTORY = 10


def companion_available() -> bool:
    return codex_available() or bool(get_config_value("OPENAI_API_KEY"))


def codex_available() -> bool:
    return shutil.which("codex") is not None


def read_dotenv_value(key: str, path: str = ".env") -> str | None:
    dotenv_path = Path(path)
    if not dotenv_path.exists():
        return None
    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    prefix = f"{key}="
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        return value or None
    return None


def get_config_value(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key) or read_dotenv_value(key) or default


def build_companion_context(*, room_name: str, room_text: str, inventory: list[str], notes: list[str], map_text: str, recent_history: list[dict[str, str]]) -> str:
    history_lines = []
    for turn in recent_history[-MAX_HISTORY:]:
        history_lines.append(f"Player: {turn['command']}")
        history_lines.append(f"Game: {turn['response']}")
    history_block = "\n".join(history_lines) if history_lines else "None."
    inventory_text = ", ".join(inventory) if inventory else "Nothing."
    notes_lines = [f"{index}. {note}" for index, note in enumerate(notes, start=1)]
    notes_text = "\n".join(notes_lines) if notes_lines else "None."

    return (
        "Premise: You are a constrained companion to a player exploring Asterfall Observatory, a storm-dark coastal signal station.\n"
        "Role: Speak like a restrained companion in a classic parser adventure: practical, slightly in-world, and never omniscient.\n"
        "Knowledge rule: Help the player interpret only what is already visible or recorded. Do not invent or assume hidden game state.\n"
        "Available commands: look, examine <thing>, go <direction>, take <item>, drop <item>, use <item>, use <item> on <target>, open <thing>, unlock <thing>, enter <code>, ask <question>, note <text>, notes, inventory, map, talk <character>, help, save, load, quit.\n"
        f"Current room: {room_name}\n"
        "Visible room description:\n"
        f"{room_text}\n"
        f"Inventory: {inventory_text}\n"
        "Recorded notes:\n"
        f"{notes_text}\n"
        "Visible map:\n"
        f"{map_text}\n"
        "Recent turns:\n"
        f"{history_block}\n"
    )


def build_companion_prompt(context: str, question: str | None) -> str:
    player_request = question or "Briefly identify the most evidenced unresolved thread in the current context."
    return (
        "You only know what appears in the supplied context. Do not assume or invent hidden game state.\n"
        "Sound like a companion from a 1980s-style parser adventure: restrained, atmospheric, practical, and slightly human or uncanny.\n"
        "Do not sound like an analyst, expert observer, or modern assistant.\n"
        "Do not invent rooms, items, commands, or puzzle facts.\n"
        "Keep your answer to one sentence, at most two.\n"
        "Prefer hints, clues, or gentle nudges over direct answers or instructions.\n"
        "Offer perspective or encouragement rather than solutioning.\n"
        "First synthesize what is already accomplished from the context.\n"
        "Then identify what remains incomplete.\n"
        "Distinguish between solved systems, unresolved but evidenced systems, and weak or speculative possibilities.\n"
        "Answer from the strongest incomplete thread only, or the top two only if they are closely matched.\n"
        "Avoid mentioning speculative leads unless there is concrete support in the visible room text, map, notes, inventory, or recent turns.\n"
        "For general questions such as what to do now, briefly acknowledge solved systems if relevant and then weight the most evidenced remaining mechanism, location, or dependency.\n"
        "For map-based questions, stay grounded in the visible layout and do not over-interpret puzzle relevance or narrative meaning unless it is explicit in the context.\n"
        "When one unfinished thread is clearly stronger than the rest, give it more weight without turning it into a command.\n"
        "Do not use imperative walkthrough language, and do not say do X then Y.\n"
        "Do not give explicit puzzle solutions unless the exact answer already appears in the player's own visible notes or context and the player is plainly asking for interpretation of those known facts; even then, phrase it as a weighted inference rather than an instruction.\n"
        "If evidence is thin, say so briefly and suggest inspection, but keep the suggestion grounded in the visible context.\n\n"
        "Context:\n"
        f"{context}\n"
        "Player request:\n"
        f"{player_request}"
    )


def extract_response_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return FALLBACK_MESSAGE


def request_companion_response(prompt: str) -> str:
    codex_response = request_codex_response(prompt)
    if codex_response:
        return codex_response

    return request_api_response(prompt)


def request_codex_response(prompt: str) -> str | None:
    if not codex_available():
        return None
    try:
        with tempfile.NamedTemporaryFile(mode="r+", encoding="utf-8", delete=True) as output_file:
            command = [
                "codex",
                "exec",
                "--color",
                "never",
                "--ephemeral",
                "--skip-git-repo-check",
                "--output-last-message",
                output_file.name,
                prompt,
            ]
            result = subprocess.run(
                command,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=60,
            )
            output_file.seek(0)
            text = output_file.read().strip()
            if result.returncode == 0 and text:
                return text
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def request_api_response(prompt: str) -> str:
    api_key = get_config_value("OPENAI_API_KEY")
    if not api_key:
        return FALLBACK_MESSAGE

    body = {
        "model": get_config_value("OPENAI_MODEL", DEFAULT_MODEL),
        "input": prompt,
        "max_output_tokens": 120,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return FALLBACK_MESSAGE
    return extract_response_text(payload)
