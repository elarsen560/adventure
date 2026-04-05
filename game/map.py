from __future__ import annotations

from dataclasses import dataclass

from game.state import GameState


@dataclass(frozen=True)
class MapNode:
    x: int
    y: int
    label: str


MAP_NODES = {
    "orrery_dome": MapNode(8, 0, "OR"),
    "library": MapNode(2, 2, "LI"),
    "archive": MapNode(6, 2, "AR"),
    "dome_antechamber": MapNode(8, 2, "DA"),
    "keepers_quarters": MapNode(0, 4, "KQ"),
    "west_hall": MapNode(2, 4, "WH"),
    "foyer": MapNode(4, 4, "FO"),
    "east_hall": MapNode(6, 4, "EH"),
    "lift_landing": MapNode(8, 4, "LL"),
    "workshop": MapNode(2, 6, "WS"),
    "generator_room": MapNode(4, 6, "GR"),
    "pump_room": MapNode(6, 6, "PR"),
    "cliff_path": MapNode(0, 8, "CP"),
    "front_gate": MapNode(2, 8, "FG"),
    "courtyard": MapNode(4, 8, "CY"),
    "sea_cave": MapNode(0, 10, "SC"),
    "conservatory": MapNode(4, 10, "CO"),
}

MAP_EDGES = [
    ("cliff_path", "front_gate", "east"),
    ("cliff_path", "sea_cave", "south"),
    ("front_gate", "courtyard", "east"),
    ("courtyard", "foyer", "north"),
    ("courtyard", "conservatory", "south"),
    ("foyer", "west_hall", "west"),
    ("foyer", "east_hall", "east"),
    ("west_hall", "library", "north"),
    ("west_hall", "workshop", "south"),
    ("west_hall", "keepers_quarters", "west"),
    ("workshop", "generator_room", "east"),
    ("east_hall", "archive", "north"),
    ("east_hall", "pump_room", "south"),
    ("east_hall", "lift_landing", "east"),
    ("lift_landing", "dome_antechamber", "north"),
    ("dome_antechamber", "orrery_dome", "north"),
]

CELL_WIDTH = 6
VERTICAL_STEP = 3


def render_map(state: GameState, *, reveal_all: bool = False, debug_label: bool = False) -> str:
    visible_rooms = set(MAP_NODES) if reveal_all else visible_map_rooms(state)
    width = (max(node.x for node in MAP_NODES.values()) + 1) * CELL_WIDTH + 1
    height = display_row(max(node.y for node in MAP_NODES.values())) + 1
    canvas = [[" " for _ in range(width)] for _ in range(height)]

    for room_a, room_b, direction in MAP_EDGES:
        if room_a not in visible_rooms or room_b not in visible_rooms:
            continue
        draw_connection(canvas, room_a, room_b, direction, state)

    for room_id in visible_rooms:
        draw_room(canvas, room_id, state)

    lines = ["".join(row).rstrip() for row in canvas]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    header = "DEBUG FULL MAP\n" if debug_label else ""
    return header + "\n".join(lines) + "\n\n@ current, O visited,? unexplored, x blocked"


def visible_map_rooms(state: GameState) -> set[str]:
    visible = set(state.discovered_rooms)
    for room_id in list(state.discovered_rooms):
        for neighbor in neighbors(room_id):
            visible.add(neighbor)
    visible.add(state.current_room)
    return visible


def neighbors(room_id: str) -> set[str]:
    adjacent = set()
    for room_a, room_b, _ in MAP_EDGES:
        if room_id == room_a:
            adjacent.add(room_b)
        elif room_id == room_b:
            adjacent.add(room_a)
    return adjacent


def draw_room(canvas: list[list[str]], room_id: str, state: GameState) -> None:
    node = MAP_NODES[room_id]
    row = display_row(node.y)
    col = node.x * CELL_WIDTH
    marker = "@ " if room_id == state.current_room else "O " if room_id in state.discovered_rooms else "? "
    token = f"[{marker}{node.label}]"
    for index, char in enumerate(token):
        canvas[row][col + index] = char


def draw_connection(canvas: list[list[str]], room_a: str, room_b: str, direction: str, state: GameState) -> None:
    node_a = MAP_NODES[room_a]
    node_b = MAP_NODES[room_b]
    blocked = edge_blocked(room_a, room_b, state)

    if direction in {"east", "west"}:
        row = display_row(node_a.y)
        left = min(node_a.x, node_b.x) * CELL_WIDTH + 4
        right = max(node_a.x, node_b.x) * CELL_WIDTH
        for col in range(left, right):
            canvas[row][col] = "x" if blocked else "-"
        return

    col = node_a.x * CELL_WIDTH + 2
    top = display_row(min(node_a.y, node_b.y)) + 1
    bottom = display_row(max(node_a.y, node_b.y))
    for row in range(top, bottom):
        canvas[row][col] = "x" if blocked else "|"


def display_row(y_value: int) -> int:
    return (y_value // 2) * VERTICAL_STEP


def edge_blocked(room_a: str, room_b: str, state: GameState) -> bool:
    pair = {room_a, room_b}
    if pair == {"front_gate", "courtyard"}:
        return not state.flags["front_gate_unlocked"]
    if pair == {"workshop", "generator_room"}:
        return not state.flags["pump_drained"]
    if pair == {"east_hall", "archive"}:
        return not state.flags["archive_unlocked"]
    if pair == {"lift_landing", "dome_antechamber"}:
        return not (
            state.flags["power_on"]
            and state.flags["lift_oiled"]
            and "transit_token" in state.inventory
        )
    if pair == {"west_hall", "keepers_quarters"}:
        return not state.flags["secret_door_open"]
    return False


def room_lookup(query: str) -> str | None:
    query = " ".join(query.lower().split())
    for room_id, node in MAP_NODES.items():
        if query == room_id:
            return room_id
    return None
