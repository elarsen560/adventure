from __future__ import annotations

from dataclasses import dataclass, field

from game.content import ITEMS, NPCS, ROOMS, build_variation


KEY_DISCOVERY_RULES = {
    "cliff_path": ("examine observatory",),
    "front_gate": ("examine gate", "examine lock", "examine chain"),
    "sea_cave": ("examine offerings", "examine wall"),
}


def canonical(text: str) -> str:
    return " ".join(text.lower().split())


def match_alias(name: str, aliases: tuple[str, ...], query: str) -> bool:
    query = canonical(query)
    names = {canonical(name), *(canonical(alias) for alias in aliases)}
    return query in names


@dataclass
class GameState:
    seed: int
    current_room: str = "cliff_path"
    inventory: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
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
            "inventory": self.inventory,
            "notes": self.notes,
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
        state.inventory = list(data["inventory"])
        state.notes = list(data.get("notes", []))
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
    for item_id in item_ids:
        item = ITEMS[item_id]
        if match_alias(item.name, item.aliases, query):
            return item_id
    return None


def find_npc_id(query: str, npc_ids: list[str]) -> str | None:
    for npc_id in npc_ids:
        npc = NPCS[npc_id]
        if match_alias(npc.name, npc.aliases, query):
            return npc_id
    return None


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
