from __future__ import annotations

import re
from dataclasses import dataclass


ARTICLES = {"the", "a", "an", "to", "at", "with"}
DIRECTION_ALIASES = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
}
VERB_ALIASES = {
    "l": "look",
    "x": "examine",
    "inspect": "examine",
    "read": "examine",
    "search": "examine",
    "study": "examine",
    "move": "go",
    "walk": "go",
    "travel": "go",
    "get": "take",
    "pick": "take",
    "pickup": "take",
    "grab": "take",
    "put": "drop",
    "apply": "use",
    "insert": "use",
    "turn": "use",
    "inv": "inventory",
    "i": "inventory",
    "m": "map",
    "?": "help",
    "exit": "quit",
}


@dataclass(frozen=True)
class Command:
    action: str
    target: str | None = None
    tool: str | None = None
    raw: str = ""


def _normalize(text: str) -> list[str]:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    parts = [part for part in text.split() if part]
    if parts[:2] == ["pick", "up"]:
        parts = ["take", *parts[2:]]
    return parts


def parse_command(text: str) -> Command:
    parts = _normalize(text)
    if not parts:
        return Command("empty", raw=text)

    if len(parts) == 1 and parts[0] in DIRECTION_ALIASES:
        return Command("go", DIRECTION_ALIASES[parts[0]], raw=text)
    if len(parts) == 1 and parts[0] in {"north", "south", "east", "west"}:
        return Command("go", parts[0], raw=text)

    verb = VERB_ALIASES.get(parts[0], parts[0])
    rest = parts[1:]

    if verb == "look" and rest and rest[0] in {"at", "into"}:
        verb = "examine"
        rest = rest[1:]
    elif verb == "talk" and rest and rest[0] == "to":
        rest = rest[1:]

    if verb == "go" and rest and rest[0] in DIRECTION_ALIASES:
        rest[0] = DIRECTION_ALIASES[rest[0]]

    if verb in {"save", "load", "enter", "map"}:
        target = " ".join(rest) if rest else None
        return Command(verb, target=target, raw=text)

    if verb == "use" and ("on" in rest or "to" in rest):
        pivot_word = "on" if "on" in rest else "to"
        pivot = rest.index(pivot_word)
        tool = " ".join(word for word in rest[:pivot] if word not in ARTICLES) or None
        target = " ".join(word for word in rest[pivot + 1 :] if word not in ARTICLES) or None
        return Command("use", target=target, tool=tool, raw=text)

    target = " ".join(word for word in rest if word not in ARTICLES) or None
    return Command(verb, target=target, raw=text)
