from __future__ import annotations

import argparse
import random

from game.models import Item, NPC, Room


SAVE_FILE = "saves/asterfall_save.json"

CODE_SETS = [
    ("heron", "ember", "crown", "tide"),
    ("thorn", "moon", "key", "wave"),
    ("glass", "rook", "sun", "well"),
    ("spire", "salt", "mask", "reed"),
]


AMBIENT_POOLS = {
    "global": [
        "Somewhere in the stonework, water ticks with patient regularity.",
        "The observatory answers the storm in sighs, creaks, and distant metal knocks.",
        "For a moment the wind drops, and the whole station seems to hold its breath.",
    ],
    "cliff_path": [
        "Spray drifts up from below and salts the air.",
        "Far beneath the path, surf bursts white against unseen rock.",
    ],
    "front_gate": [
        "The chain gives a faint iron clink whenever the wind changes.",
        "Rain beads on the gate bars and runs black down the metal.",
    ],
    "foyer": [
        "A loose frame taps softly somewhere along the wall of portraits.",
        "Your steps leave the foyer listening after you.",
    ],
    "east_hall": [
        "Conduits in the ceiling mutter whenever the weather surges.",
        "The corridor smells faintly of old oil and cold metal.",
    ],
    "generator_room": [
        "The heavy machinery seems to brood in the dark.",
        "Water still glistens in seams between the floor stones.",
    ],
    "conservatory": [
        "Leaves whisper together under the burden of rain.",
        "Somewhere among the vines, a drop of water falls with clocklike precision.",
    ],
    "archive": [
        "The sealed room swallows sound almost completely.",
        "A drawer settles deeper in its runners with a dry wooden click.",
    ],
    "lift_landing": [
        "The lift cables vanish upward into shadow without a sound.",
        "The empty carriage rocks so slightly you cannot be sure it moved at all.",
    ],
    "orrery_dome": [
        "High overhead, the dome returns the storm as a low distant murmur.",
        "Brass and darkness fill the great chamber with a solemn expectancy.",
    ],
    "power_on": [
        "Somewhere deeper in the station, a restored relay snaps shut.",
        "A low electrical hum now threads the silence.",
    ],
    "archive_unlocked": [
        "The unsealed archive door gives an occasional minute settling click.",
    ],
    "secret_door_open": [
        "From the hidden passage comes the faint dry smell of paper and old tea.",
    ],
    "lens_installed": [
        "A pale gleam lingers in the dome machinery, then fades again.",
    ],
}


ITEMS = {
    "groundskeeper_key": Item(
        "groundskeeper_key",
        "groundskeeper key",
        "A black iron key tagged with a verdigrised brass plate stamped GATE.",
        aliases=("key", "gate key", "iron key", "groundskeeper key"),
    ),
    "winding_key": Item(
        "winding_key",
        "winding key",
        "A thumb-sized brass key for a spring motor or automaton.",
        aliases=("brass key", "key"),
    ),
    "handwheel": Item(
        "handwheel",
        "brass handwheel",
        "A removable wheel with square teeth on its hub. It looks made to fit a valve spindle.",
        aliases=("wheel", "valve wheel", "handwheel"),
    ),
    "fuse": Item(
        "fuse",
        "ceramic fuse",
        "A heavy ceramic fuse cartridge, sooted but still intact.",
        aliases=("cartridge", "fuse"),
    ),
    "oil_flask": Item(
        "oil_flask",
        "oil flask",
        "A narrow flask of clockwork oil with enough left for one stubborn mechanism.",
        aliases=("oil", "flask"),
    ),
    "constellation_folio": Item(
        "constellation_folio",
        "constellation folio",
        "Loose chart sheets describing the station's private mnemonic constellations.",
        aliases=("folio", "charts"),
    ),
    "transit_token": Item(
        "transit_token",
        "transit token",
        "A punched brass token labeled DOME LIFT. Its edge is worn smooth by use.",
        aliases=("token", "brass token"),
    ),
    "star_lens": Item(
        "star_lens",
        "star lens",
        "A dense crystal lens ringed in silver, cold in the hand and faintly luminous.",
        aliases=("lens",),
    ),
    "match_tin": Item(
        "match_tin",
        "match tin",
        "A dry tin of storm matches. The keeper believed in backup plans.",
        aliases=("matches", "tin", "match tin"),
    ),
    "logbook_page": Item(
        "logbook_page",
        "logbook page",
        "A torn page from the chief astronomer's log, marked with three final alignment positions.",
        aliases=("page", "logbook", "page from logbook"),
    ),
}


NPCS = {
    "wren": NPC(
        "wren",
        "Wren",
        "A brass caretaker automaton shaped like a narrow-shouldered groundskeeper, currently slumped and still.",
        aliases=("automaton", "caretaker", "brass caretaker"),
    )
}


ROOMS = {
    "cliff_path": Room(
        "cliff_path",
        "Cliff Path",
        "The flagstone path winds along the lip of the headland, slick with rain and white with salt. Far below, the sea hammers the cliffs in heavy black folds. Ahead, Asterfall Observatory looms through the weather, all blind windows, greened brass, and the vast curve of its darkened dome.",
        exits={"east": "front_gate", "south": "sea_cave"},
        features={
            "sea": "Below the cliff, surf breaks in white seams against the rock.",
            "observatory": "Asterfall's dome is dark, but not dead. It looks as if it has merely been waiting.",
        },
    ),
    "front_gate": Room(
        "front_gate",
        "Front Gate",
        "You stand before the observatory's outer gate, where twisted iron spears rise higher than a man's head. A chain has been looped through the bars and drawn tight. The old lock is furred with salt, but the keeper who closed it expected it might one day be opened again.",
        exits={"west": "cliff_path", "east": "courtyard"},
        features={
            "gate": "The gate is chained shut. A lock plate sits beneath a scab of salt.",
            "chain": "Old iron links loop the bars. They will not yield without the key.",
        },
    ),
    "courtyard": Room(
        "courtyard",
        "Courtyard",
        "Within the gate lies a broad stone courtyard open to the storm. Rainwater pools in the cracks between worn tiles and runs in silver threads toward a dry fountain at the center. Arched doors open north and south, while the dark gate waits to the west.",
        exits={"west": "front_gate", "north": "foyer", "south": "conservatory"},
        features={
            "fountain": "The basin is dry except for rain. Something metallic sits where a spout should be.",
            "tiles": "The tiles show a compass rose worked in pale stone.",
        },
    ),
    "foyer": Room(
        "foyer",
        "Foyer",
        "The great foyer is close and still after the violence outside. Your footsteps echo off marble and old wood. Portraits of former keepers line the walls, their severe faces half-lost in dust, each painted with lamp, chart, or sextant in hand as though expecting inspection at any moment.",
        exits={"south": "courtyard", "west": "west_hall", "east": "east_hall"},
        features={
            "portraits": "Generations of keepers hold lanterns, charts, and impossible levels of composure.",
            "desk": "The concierge desk has been stripped clean except for rings of long-dried lamp oil.",
        },
    ),
    "west_hall": Room(
        "west_hall",
        "West Hall",
        "This curving hall follows the western wall of the observatory. Tall windows shudder in their frames whenever the gale rises. The lamps are dark, yet they swing almost imperceptibly, stirred by drafts from cracks too small to see.",
        exits={"east": "foyer", "north": "library", "south": "workshop"},
        features={
            "windows": "Beyond the wet glass, the sea heaves under a low slate sky.",
            "painting": "A moonlit seascape hangs slightly askew.",
        },
    ),
    "east_hall": Room(
        "east_hall",
        "East Hall",
        "The eastern passage is less gracious and more mechanical. Riveted panels, conduit trunks, and junction boxes crowd the stonework. Everything here was built to serve the hidden engines of the observatory rather than its people.",
        exits={"west": "foyer", "north": "archive", "south": "pump_room", "east": "lift_landing"},
        features={
            "archive door": "A steel archive door with a four-symbol wheel lock. The lock expects a sequence, not a key.",
            "conduits": "Heavy conduits vanish into the wall toward the lift and generator circuits.",
        },
    ),
    "library": Room(
        "library",
        "Library",
        "Shelves climb the circular walls from floor to ceiling, burdened with atlases, weather journals, and boxed ephemerides. Salt has curled the edges of many charts, yet the room keeps the hush of long study, as if someone has only just stepped away from the reading table.",
        exits={"south": "west_hall"},
        features={
            "shelves": "Astronomical atlases and weather ledgers lean against each other in exhausted ranks.",
            "reading table": "A brass lamp stands on a broad table beside a scattering of chart weights.",
        },
    ),
    "workshop": Room(
        "workshop",
        "Workshop",
        "The workshop smells of oil, filings, and scorched wick. Benches stand crowded with clockwork assemblies, brass housings, and lantern parts laid down in the middle of repair and never touched again. It is the sort of room where difficult machines were bullied into obedience by practical hands.",
        exits={"north": "west_hall", "east": "generator_room"},
        features={
            "bench": "The main bench is scarred by decades of improvised repairs.",
            "lift gears": "Replacement gears for the dome lift lie under a tarp, each labeled in a keeper's tidy hand.",
        },
    ),
    "generator_room": Room(
        "generator_room",
        "Generator Room",
        "Copper windings, flywheels, and cast housings fill the room so completely that the walls seem built around them. Water stains band the lower stone like old tide marks. At the center rests the emergency dynamo, mute and cold behind an open maintenance panel.",
        exits={"west": "workshop"},
        features={
            "generator": "The emergency dynamo needs a fuse before it can safely carry current.",
            "panel": "The maintenance panel hangs open, exposing an empty ceramic fuse slot.",
            "water": "A dark tide mark on the wall shows how recently the room was flooded.",
        },
    ),
    "pump_room": Room(
        "pump_room",
        "Pump Room",
        "The air here is wet and mineral. A squat pump housing rises beside a drainage cistern black with old damp. Somewhere below the floor, trapped seawater mutters through channels cut into the rock itself.",
        exits={"north": "east_hall"},
        features={
            "spindle": "A square valve spindle protrudes from the pump housing, naked without its wheel.",
            "cistern": "The cistern feeds the drainage channels that protect the generator room.",
        },
    ),
    "conservatory": Room(
        "conservatory",
        "Conservatory",
        "The conservatory lies under a ribbed roof of storm-blind glass. Once it must have been green and bright; now it is all damp leaves, pale blossoms, and brass trellises gone green with neglect. Vines have crawled over everything, claiming irrigation frames and benches alike.",
        exits={"north": "courtyard"},
        features={
            "plants": "The keepers cultivated symbolic plants here, each bed labeled with a station constellation.",
            "labels": "Brass plaques sit at the ends of four central planters.",
            "shutters": "The storm shutters are half-seized, leaving the room in greenish twilight.",
        },
    ),
    "archive": Room(
        "archive",
        "Archive",
        "The archive is a sealed vault of lacquered cases, steel drawers, and catalogued instruments arranged with almost military exactness. Yet the order was broken at the end. Several drawers stand open, and one work table still bears the signs of hurried, unfinished selection.",
        exits={"south": "east_hall"},
        features={
            "cases": "Most cases stand open and empty, but one padded case still waits on the central table.",
            "drawers": "The labeled drawers record weather, lamp maintenance, and star corrections year by year.",
        },
    ),
    "lift_landing": Room(
        "lift_landing",
        "Lift Landing",
        "A brass cage lift waits here behind a folding lattice gate. Its carriage hangs in the shaft like a lantern gone dark, all riveted glass and metal ribs. The call slot is dead, and the whole mechanism carries the stiff silence of something long unrun.",
        exits={"west": "east_hall", "north": "dome_antechamber"},
        features={
            "lift": "The observatory lift needs station power, a transit token, and a touch of mechanical mercy.",
            "gate": "The lift gate folds inward once the carriage is unlocked.",
        },
    ),
    "dome_antechamber": Room(
        "dome_antechamber",
        "Dome Antechamber",
        "The temperature drops the instant you step out of the lift. This narrow annular corridor circles the base of the great dome. Brass plaques set into the walls commemorate eclipses observed, storms survived, and ships guided to safety by the signal above.",
        exits={"south": "lift_landing", "north": "orrery_dome"},
        features={
            "plaques": "The plaques credit no single keeper. The station endured because people left each other instructions.",
            "inner door": "A circular iris door stands open just enough to reveal the heart of the dome beyond.",
        },
    ),
    "orrery_dome": Room(
        "orrery_dome",
        "Orrery Dome",
        "You have reached the heart of Asterfall. Beneath the vast black bowl of the dome stands the great orrery, a forest of brass arms, toothed rings, and polished tracks climbing toward the beacon housing overhead. Around its base stand three numbered alignment levers and, at the center, a silver socket left painfully empty.",
        exits={"south": "dome_antechamber"},
        features={
            "orrery": "The mechanism can still move. It only lacks the lens and the proper final alignment.",
            "socket": "A silver mounting ring waits at the center of the machine.",
            "levers": "Three engraved levers can be set to numbered positions from one through four.",
        },
    ),
    "sea_cave": Room(
        "sea_cave",
        "Sea Cave",
        "A narrow cave opens under the cliff where the tide has withdrawn for the moment. The walls glitter faintly with mica and wet salt. In a dry niche above the waterline, generations of keepers have left small superstitious offerings against shipwreck and bad weather.",
        exits={"north": "cliff_path"},
        features={
            "offerings": "Buttons, shells, and candle wax cluster in a dry niche above the tide line.",
            "wall": "One rock face bears old chalk tally marks and a scratched keeper's proverb.",
        },
    ),
    "keepers_quarters": Room(
        "keepers_quarters",
        "Keeper's Quarters",
        "This hidden chamber was never meant for visitors. A narrow cot stands against the wall beside a small spirit lamp and a tea service turned brown with age. Shelves of private notebooks fill the rest of the room: the unofficial memory of the observatory, preserved behind a painted secret.",
        exits={"east": "west_hall"},
        features={
            "cot": "The blankets are folded with military precision.",
            "tea service": "A tarnished tray holds a pot, a cup, and the ring left by something metal set there in haste.",
            "notebooks": "The notebooks are practical, affectionate, and full of unofficial fixes for official problems.",
        },
    ),
}


def build_variation(seed: int) -> dict:
    rng = random.Random(seed)
    key_room = rng.choice(["cliff_path", "front_gate", "sea_cave"])
    token_room = rng.choice(["archive", "keepers_quarters"])
    reward_room = rng.choice(["library", "sea_cave", "keepers_quarters"])
    code_words = list(rng.choice(CODE_SETS))
    rng.shuffle(code_words)
    alignment = [rng.randint(1, 4) for _ in range(3)]
    intro_line = rng.choice(
        [
            "Stormglass glows along the parapets whenever lightning moves under the sea.",
            "Somewhere in the stonework, an old signal bell knocks softly to the wind.",
            "The dome's dark silhouette looks less abandoned than patient.",
        ]
    )
    return {
        "seed": seed,
        "key_room": key_room,
        "token_room": token_room,
        "reward_room": reward_room,
        "archive_code": code_words,
        "alignment": alignment,
        "intro_line": intro_line,
    }


def intro_text(state) -> str:
    return (
        "ASTerfall Observatory\n"
        "\n"
        "For nine nights the Dawn Signal has been dark.\n"
        "The relief steamer was due yesterday, but the storm has swallowed sea and sky alike, and no captain alive will risk this coast without the old light atop the headland.\n"
        "So you have come alone through wind, rain, and surf to wake a station that ought to have died with the century.\n"
        "If the machinery below the dome can be coaxed back to life, the beacon may yet burn before the rocks claim another hull.\n\n"
        f"Run seed: {state.seed}\n"
        f"{state.variation['intro_line']}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Asterfall Observatory.")
    parser.add_argument("seed", nargs="?", type=int, help="Optional seed for a reproducible run.")
    parser.add_argument("--debug", action="store_true", help="Enable debug-only testing commands.")
    return parser.parse_args(argv)
