from __future__ import annotations

import json
from pathlib import Path

from game.content import SAVE_FILE
from game.state import GameState


def resolve_save_path(path: str | None = None) -> Path:
    if path is None:
        return Path(SAVE_FILE)
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    if candidate.parent == Path("."):
        return Path("saves") / candidate.name
    return candidate


def save_game(state: GameState, path: str | None = None) -> str:
    save_path = resolve_save_path(path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
    return str(save_path)


def load_game(path: str | None = None) -> GameState:
    save_path = resolve_save_path(path)
    data = json.loads(save_path.read_text(encoding="utf-8"))
    return GameState.from_dict(data)
