from __future__ import annotations

import random


HAZARD_DEFINITIONS = {
    "swinging_hoist": {
        "room": "workshop",
        "clue": "Above the main bench, a loose chain hoist gives a small uneasy swing whenever the observatory shudders.",
        "lingering": "The slack hoist still sways over the bench, waiting for another careless reach.",
        "resolve_features": {"bench", "lift gears"},
        "aliases": {
            "hoist": "bench",
            "chain hoist": "bench",
            "chain": "bench",
            "weight": "bench",
            "hook": "bench",
        },
        "resolve_text": (
            "Up close, the danger is plain enough: the hoist's arc favors the right side of the bench. "
            "Working from the left would keep clear of it."
        ),
        "take_items": {"fuse", "oil_flask"},
        "warning": (
            "As you reach across the bench, the loose hoist swings down with a hard iron clatter and misses your hand by inches. "
            "The workshop can be worked safely, but not carelessly. A closer look at the bench would tell you how."
        ),
        "game_over": (
            "You reach in blindly a second time. The neglected hoist drops its weight at the same moment the floor trembles, "
            "striking you and driving you hard against the bench. The workshop settles into silence around you, and Asterfall goes dark."
        ),
    },
    "shifting_cases": {
        "room": "archive",
        "clue": "One leaning stack of instrument cases on the central table looks ready to slide if disturbed the wrong way.",
        "lingering": "The tilted cases remain poised on the edge of collapse.",
        "resolve_features": {"cases", "drawers"},
        "aliases": {
            "stack": "cases",
            "leaning stack": "cases",
            "instrument cases": "cases",
            "table": "cases",
        },
        "resolve_text": (
            "From this angle you can see which case is load-bearing and which are only resting against it. "
            "There is a safe way to reach the table, provided you keep to the anchored side."
        ),
        "take_items": {"star_lens", "logbook_page", "transit_token"},
        "warning": (
            "The cases shift at once with a dry sliding scrape. You snatch your hand back before the stack comes down. "
            "Another careless tug might bring the whole table over; the cases deserve a closer look first."
        ),
        "game_over": (
            "You disturb the leaning stack again. This time the cases go all at once, striking the table into you and driving you to the archive floor beneath lacquered weight and steel corners. "
            "The sealed room closes over the noise almost immediately."
        ),
    },
    "snapping_lattice": {
        "room": "lift_landing",
        "clue": "One lattice runner has sprung inward; the gate looks as though it might snap or catch at a careless hand.",
        "lingering": "The bent lattice runner still waits in the gate's track, ugly and ready to bite.",
        "resolve_features": {"lift", "gate"},
        "aliases": {
            "runner": "gate",
            "lattice runner": "gate",
            "lattice": "gate",
            "track": "gate",
        },
        "resolve_text": (
            "Seen closely, the fault is manageable: the bent runner only catches if the gate is taken head-on. "
            "With a careful angle there is room enough to work around it."
        ),
        "use_items": {"oil_flask"},
        "warning": (
            "The bent runner snaps toward your hand with a sharp metallic report. You jerk away before it catches skin. "
            "The lift is usable, but not if you trust the gate at a glance. Examining it would be wiser."
        ),
        "game_over": (
            "You commit your weight to the faulty gate again. The runner catches, throws the lattice sideways, and sends you hard against the lift frame and into the shaft threshold. "
            "By the time the echoes die, the old carriage hangs motionless above you."
        ),
    },
}


def select_hazard(seed: int) -> tuple[str, str]:
    rng = random.Random(seed + 404)
    hazard_id = rng.choice(sorted(HAZARD_DEFINITIONS))
    return hazard_id, HAZARD_DEFINITIONS[hazard_id]["room"]


def validate_hazard_selection(hazard_type: str | None, hazard_room: str | None) -> None:
    if not hazard_type or not hazard_room:
        raise ValueError("Hazard selection is incomplete.")
    hazard = hazard_definition(hazard_type)
    if not hazard:
        raise ValueError(f"Unknown hazard type: {hazard_type}")
    if hazard["room"] != hazard_room:
        raise ValueError(f"Hazard room mismatch for {hazard_type}: {hazard_room}")
    if hazard_room not in {"workshop", "archive", "lift_landing"}:
        raise ValueError(f"Hazard room is not a valid mid-game room: {hazard_room}")


def hazard_definition(hazard_type: str | None) -> dict | None:
    if not hazard_type:
        return None
    return HAZARD_DEFINITIONS.get(hazard_type)


def hazard_clue(hazard_type: str | None, current_room: str, resolved: bool) -> str | None:
    hazard = hazard_definition(hazard_type)
    if not hazard or resolved or hazard["room"] != current_room:
        return None
    return hazard["clue"]


def hazard_lingering_text(hazard_type: str | None, current_room: str, resolved: bool, warnings: int) -> str | None:
    hazard = hazard_definition(hazard_type)
    if not hazard or resolved or warnings <= 0 or hazard["room"] != current_room:
        return None
    return hazard["lingering"]


def hazard_resolves_on_examine(hazard_type: str | None, current_room: str, target: str) -> str | None:
    hazard = hazard_definition(hazard_type)
    if not hazard or hazard["room"] != current_room:
        return None
    if target not in hazard["resolve_features"]:
        return None
    return hazard["resolve_text"]


def hazard_feature_aliases(hazard_type: str | None, current_room: str) -> dict[str, str]:
    hazard = hazard_definition(hazard_type)
    if not hazard or hazard["room"] != current_room:
        return {}
    return dict(hazard.get("aliases", {}))


def hazard_hint_targets(hazard_type: str | None, current_room: str) -> list[str]:
    hazard = hazard_definition(hazard_type)
    if not hazard or hazard["room"] != current_room:
        return []
    seen: list[str] = []
    for value in (*hazard.get("resolve_features", ()), *hazard.get("aliases", {}).keys()):
        if value not in seen:
            seen.append(value)
    return seen


def should_warn_on_take(hazard_type: str | None, current_room: str, item_id: str) -> bool:
    hazard = hazard_definition(hazard_type)
    if not hazard or hazard["room"] != current_room:
        return False
    return item_id in hazard.get("take_items", set())


def should_warn_on_use(hazard_type: str | None, current_room: str, item_id: str) -> bool:
    hazard = hazard_definition(hazard_type)
    if not hazard or hazard["room"] != current_room:
        return False
    return item_id in hazard.get("use_items", set())


def should_warn_on_go(hazard_type: str | None, current_room: str, direction: str) -> bool:
    return hazard_type == "snapping_lattice" and current_room == "lift_landing" and direction == "north"
