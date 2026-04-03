from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from game.content import ITEMS, NPCS, ROOMS, build_variation


KEY_DISCOVERY_RULES = {
    "cliff_path": ("examine observatory",),
    "front_gate": ("examine gate", "examine lock", "examine chain"),
    "sea_cave": ("examine offerings", "examine wall"),
}

STOPWORDS = {
    "the",
    "and",
    "with",
    "from",
    "that",
    "this",
    "into",
    "onto",
    "near",
    "over",
    "under",
    "your",
    "their",
    "them",
    "when",
    "where",
    "have",
    "been",
    "once",
    "only",
    "just",
    "still",
    "looks",
    "look",
    "room",
    "stone",
    "metal",
}


def canonical(text: str) -> str:
    return " ".join(text.lower().split())


def _singularize(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def phrase_variants(text: str) -> set[str]:
    normalized = canonical(text)
    tokens = normalized.split()
    variants = {normalized}
    singular_tokens = [_singularize(token) for token in tokens]
    variants.add(" ".join(singular_tokens))
    variants.add(" ".join(token.replace("-", " ") for token in tokens))
    variants = {variant.strip() for variant in variants if variant.strip()}
    return variants


def match_alias(name: str, aliases: tuple[str, ...], query: str) -> bool:
    query_variants = phrase_variants(query)
    names = set()
    for value in (name, *aliases):
        names.update(phrase_variants(value))
    if query_variants & names:
        return True
    query_text = canonical(query)
    return any(query_text in name_variant or name_variant in query_text for name_variant in names if len(name_variant) >= 4)


def best_match(query: str, options: dict[str, str]) -> str | None:
    normalized = canonical(query)
    if not normalized:
        return None
    for variant in phrase_variants(normalized):
        if variant in options:
            return options[variant]
    contains = [target for alias, target in options.items() if normalized in alias or alias in normalized]
    if len(set(contains)) == 1:
        return contains[0]
    close = difflib.get_close_matches(normalized, list(options), n=1, cutoff=0.74)
    if close:
        return options[close[0]]
    return None


def extracted_keywords(*texts: str) -> set[str]:
    words = set()
    for text in texts:
        for raw in text.lower().replace("-", " ").split():
            token = "".join(char for char in raw if char.isalpha())
            token = _singularize(token)
            if len(token) >= 4 and token not in STOPWORDS:
                words.add(token)
    return words


@dataclass
class GameState:
    seed: int
    current_room: str = "cliff_path"
    debug_mode: bool = False
    inventory: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    recent_history: list[dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    last_ambient_turn: int = -99
    ambient_history: dict[str, list[str]] = field(default_factory=dict)
    room_items: dict[str, list[str]] = field(default_factory=dict)
    hidden_items: dict[str, list[str]] = field(default_factory=dict)
    discovered_rooms: set[str] = field(default_factory=set)
    flags: dict[str, bool] = field(default_factory=dict)
    variation: dict = field(default_factory=dict)
    clue_texts: dict[str, str] = field(default_factory=dict)
    running: bool = True
    won: bool = False

    @classmethod
    def new(cls, seed: int) -> "GameState":
        variation = build_variation(seed)
        state = cls(seed=seed, variation=variation)
        state.discovered_rooms = {"cliff_path"}
        state.flags = {
            "front_gate_unlocked": False,
            "pump_drained": False,
            "power_on": False,
            "wren_awake": False,
            "archive_unlocked": False,
            "lift_oiled": False,
            "secret_door_open": False,
            "lens_installed": False,
            "signal_lit": False,
        }
        state.room_items = {
            "courtyard": ["handwheel"],
            "workshop": ["fuse", "oil_flask"],
            "library": ["constellation_folio"],
            "archive": ["star_lens", "logbook_page"],
            "keepers_quarters": [],
        }
        state.hidden_items = {
            variation["key_room"]: ["groundskeeper_key"],
            "conservatory": ["winding_key"],
        }
        state.room_items[variation["token_room"]].append("transit_token")
        if variation["reward_room"] not in state.room_items:
            state.room_items[variation["reward_room"]] = []
        if "match_tin" not in state.room_items[variation["reward_room"]]:
            state.room_items[variation["reward_room"]].append("match_tin")
        state.clue_texts = build_clue_texts(variation)
        validate_starting_key_access(state)
        return state

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "current_room": self.current_room,
            "debug_mode": self.debug_mode,
            "inventory": self.inventory,
            "notes": self.notes,
            "recent_history": self.recent_history,
            "turn_count": self.turn_count,
            "last_ambient_turn": self.last_ambient_turn,
            "ambient_history": self.ambient_history,
            "room_items": self.room_items,
            "hidden_items": self.hidden_items,
            "discovered_rooms": sorted(self.discovered_rooms),
            "flags": self.flags,
            "variation": self.variation,
            "clue_texts": self.clue_texts,
            "running": self.running,
            "won": self.won,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        state = cls(seed=data["seed"])
        state.current_room = data["current_room"]
        state.debug_mode = data.get("debug_mode", False)
        state.inventory = list(data["inventory"])
        state.notes = list(data.get("notes", []))
        state.recent_history = [dict(item) for item in data.get("recent_history", [])]
        state.turn_count = data.get("turn_count", 0)
        state.last_ambient_turn = data.get("last_ambient_turn", -99)
        state.ambient_history = {k: list(v) for k, v in data.get("ambient_history", {}).items()}
        state.room_items = {k: list(v) for k, v in data["room_items"].items()}
        state.hidden_items = {k: list(v) for k, v in data["hidden_items"].items()}
        state.discovered_rooms = set(data["discovered_rooms"])
        state.flags = dict(data["flags"])
        state.variation = dict(data["variation"])
        state.clue_texts = dict(data["clue_texts"])
        state.running = data.get("running", True)
        state.won = data.get("won", False)
        return state


def build_clue_texts(variation: dict) -> dict[str, str]:
    code = variation["archive_code"]
    return {
        "constellation_folio": (
            "The folio lists four maintenance constellations used on internal station locks: "
            f"{', '.join(code)}.\n"
            "A penciled note adds: 'The conservatory beds preserve the order if the lamps go out.'"
        ),
        "conservatory_labels": (
            "The central planters are labeled in a clockwise ring: "
            f"{' -> '.join(code)}.\n"
            "Each plaque is polished by anxious fingers."
        ),
        "logbook_page": (
            "The torn log page reads: 'Final Dawn Signal alignment remains "
            f"{variation['alignment'][0]}, {variation['alignment'][1]}, {variation['alignment'][2]} "
            "after lens seating. Do not trust the painted calibrations; they drift in coastal cold.'"
        ),
    }


def find_item_id(query: str, item_ids: list[str]) -> str | None:
    option_map: dict[str, str] = {}
    for item_id in item_ids:
        item = ITEMS[item_id]
        for value in (item.name, *item.aliases):
            for variant in phrase_variants(value):
                option_map[variant] = item_id
        for keyword in extracted_keywords(item.name, item.description, *item.aliases):
            option_map.setdefault(keyword, item_id)
    return best_match(query, option_map)


def find_npc_id(query: str, npc_ids: list[str]) -> str | None:
    option_map: dict[str, str] = {}
    for npc_id in npc_ids:
        npc = NPCS[npc_id]
        for value in (npc.name, *npc.aliases):
            for variant in phrase_variants(value):
                option_map[variant] = npc_id
        for keyword in extracted_keywords(npc.name, npc.description, *npc.aliases):
            option_map.setdefault(keyword, npc_id)
    return best_match(query, option_map)


def visible_npcs(state: GameState, room_id: str) -> list[str]:
    if room_id == "conservatory":
        return ["wren"]
    return []


def current_room_items(state: GameState) -> list[str]:
    return list(state.room_items.get(state.current_room, []))


def reveal_hidden_item(state: GameState, room_id: str, item_id: str) -> None:
    hidden = state.hidden_items.get(room_id, [])
    if item_id in hidden:
        hidden.remove(item_id)
        state.room_items.setdefault(room_id, []).append(item_id)


def validate_starting_key_access(state: GameState) -> None:
    key_room = state.variation["key_room"]
    accessible_rooms = {"cliff_path", "front_gate", "sea_cave"}
    if key_room not in accessible_rooms:
        raise ValueError(f"Groundskeeper key placed in inaccessible room: {key_room}")
    hidden = state.hidden_items.get(key_room, [])
    room_items = state.room_items.get(key_room, [])
    if "groundskeeper_key" not in hidden and "groundskeeper_key" not in room_items:
        raise ValueError(f"Groundskeeper key missing from designated room: {key_room}")
    if key_room not in KEY_DISCOVERY_RULES:
        raise ValueError(f"No discovery rules defined for groundskeeper key room: {key_room}")
