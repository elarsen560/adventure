from __future__ import annotations

import random

from game.content import AMBIENT_POOLS
from game.state import GameState


AMBIENT_EXCLUDED_ACTIONS = {"help", "notes", "map", "save", "load", "inventory"}
AMBIENT_CHANCE = 0.2
AMBIENT_MIN_GAP = 2


def should_emit_ambient(state: GameState, action: str) -> bool:
    if action in AMBIENT_EXCLUDED_ACTIONS:
        return False
    if state.turn_count - state.last_ambient_turn <= AMBIENT_MIN_GAP:
        return False
    roll = random.Random(f"{state.seed}:ambient:{state.turn_count}:{state.current_room}").random()
    return roll < AMBIENT_CHANCE


def ambient_candidates(state: GameState) -> list[str]:
    candidates = []
    candidates.extend(AMBIENT_POOLS.get("global", []))
    candidates.extend(AMBIENT_POOLS.get(state.current_room, []))
    if state.flags.get("power_on"):
        candidates.extend(AMBIENT_POOLS.get("power_on", []))
    if state.flags.get("archive_unlocked"):
        candidates.extend(AMBIENT_POOLS.get("archive_unlocked", []))
    if state.flags.get("secret_door_open"):
        candidates.extend(AMBIENT_POOLS.get("secret_door_open", []))
    if state.flags.get("lens_installed"):
        candidates.extend(AMBIENT_POOLS.get("lens_installed", []))
    return candidates


def select_ambient_line(state: GameState) -> str | None:
    candidates = ambient_candidates(state)
    if not candidates:
        return None
    room_key = f"{state.current_room}|{int(state.flags.get('power_on', False))}|{int(state.flags.get('archive_unlocked', False))}|{int(state.flags.get('secret_door_open', False))}|{int(state.flags.get('lens_installed', False))}"
    recent = set(state.ambient_history.get(room_key, []))
    fresh = [line for line in candidates if line not in recent]
    pool = fresh or candidates
    choice = random.Random(f"{state.seed}:ambient-choice:{state.turn_count}:{room_key}").choice(pool)
    history = list(state.ambient_history.get(room_key, []))
    history.append(choice)
    state.ambient_history[room_key] = history[-3:]
    state.last_ambient_turn = state.turn_count
    return choice
