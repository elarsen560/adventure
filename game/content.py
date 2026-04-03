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
        "A flagstone path clings to the headland above a black and restless sea. Ahead, Asterfall Observatory rises from the rain like a stranded cathedral of brass and stone.",
        exits={"east": "front_gate", "south": "sea_cave"},
        features={
            "sea": "Below the cliff, surf breaks in white seams against the rock.",
            "observatory": "Asterfall's dome is dark, but not dead. It looks as if it has merely been waiting.",
        },
    ),
    "front_gate": Room(
        "front_gate",
        "Front Gate",
        "A wrought-iron gate bars the final ascent. The bars are chained, but the old lock still looks serviceable.",
        exits={"west": "cliff_path", "east": "courtyard"},
        features={
            "gate": "The gate is chained shut. A lock plate sits beneath a scab of salt.",
            "chain": "Old iron links loop the bars. They will not yield without the key.",
        },
    ),
    "courtyard": Room(
        "courtyard",
        "Courtyard",
        "Rainwater glitters in the cracked courtyard tiles. A dry fountain crouches at the center, and three doors lead into the observatory proper.",
        exits={"west": "front_gate", "north": "foyer", "south": "conservatory"},
        features={
            "fountain": "The basin is dry except for rain. Something metallic sits where a spout should be.",
            "tiles": "The tiles show a compass rose worked in pale stone.",
        },
    ),
    "foyer": Room(
        "foyer",
        "Foyer",
        "The foyer smells of dust, cold brass, and the mineral bite of old storms. Portraits of keepers line the walls with the patient expression of people who knew how long a night can be.",
        exits={"south": "courtyard", "west": "west_hall", "east": "east_hall"},
        features={
            "portraits": "Generations of keepers hold lanterns, charts, and impossible levels of composure.",
            "desk": "The concierge desk has been stripped clean except for rings of long-dried lamp oil.",
        },
    ),
    "west_hall": Room(
        "west_hall",
        "West Hall",
        "A long hall bends around the observatory's western wall. Wind presses at the tall windows and the lamps sway faintly though they are unlit.",
        exits={"east": "foyer", "north": "library", "south": "workshop"},
        features={
            "windows": "Beyond the wet glass, the sea heaves under a low slate sky.",
            "painting": "A moonlit seascape hangs slightly askew.",
        },
    ),
    "east_hall": Room(
        "east_hall",
        "East Hall",
        "This side of the observatory feels more industrial. Cable conduits run along the ceiling toward the station's inner machinery.",
        exits={"west": "foyer", "north": "archive", "south": "pump_room", "east": "lift_landing"},
        features={
            "archive door": "A steel archive door with a four-symbol wheel lock. The lock expects a sequence, not a key.",
            "conduits": "Heavy conduits vanish into the wall toward the lift and generator circuits.",
        },
    ),
    "library": Room(
        "library",
        "Library",
        "Shelves crowd the circular library from floor to ceiling. Salt has curled the chart edges, but the room still feels inhabited by careful thought.",
        exits={"south": "west_hall"},
        features={
            "shelves": "Astronomical atlases and weather ledgers lean against each other in exhausted ranks.",
            "reading table": "A brass lamp stands on a broad table beside a scattering of chart weights.",
        },
    ),
    "workshop": Room(
        "workshop",
        "Workshop",
        "Benches line the workshop under a haze of filings and old grease. Half-repaired clockwork and storm lanterns wait exactly where they were abandoned.",
        exits={"north": "west_hall", "east": "generator_room"},
        features={
            "bench": "The main bench is scarred by decades of improvised repairs.",
            "lift gears": "Replacement gears for the dome lift lie under a tarp, each labeled in a keeper's tidy hand.",
        },
    ),
    "generator_room": Room(
        "generator_room",
        "Generator Room",
        "Copper coils and flywheels fill the chamber. Water stains ring the lower walls, and the station's emergency dynamo sits silent behind a maintenance panel.",
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
        "A drain cistern and a rusted spindle occupy most of the pump room. Somewhere beneath the floor, seawater gurgles through stone channels.",
        exits={"north": "east_hall"},
        features={
            "spindle": "A square valve spindle protrudes from the pump housing, naked without its wheel.",
            "cistern": "The cistern feeds the drainage channels that protect the generator room.",
        },
    ),
    "conservatory": Room(
        "conservatory",
        "Conservatory",
        "Glass ribs arch overhead, blurred by algae and salt. Night-blooming vines have escaped their trellises and wrapped around brass irrigation frames.",
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
        "The archive is a climate-tight vault of steel drawers, lacquered cases, and carefully catalogued instruments. Someone rushed here before the evacuation and left in a hurry.",
        exits={"south": "east_hall"},
        features={
            "cases": "Most cases stand open and empty, but one padded case still waits on the central table.",
            "drawers": "The labeled drawers record weather, lamp maintenance, and star corrections year by year.",
        },
    ),
    "lift_landing": Room(
        "lift_landing",
        "Lift Landing",
        "A cage lift stands behind a lattice gate, all brass ribs and riveted glass. The carriage hangs ready, but the call slot is dark.",
        exits={"west": "east_hall", "north": "dome_antechamber"},
        features={
            "lift": "The observatory lift needs station power, a transit token, and a touch of mechanical mercy.",
            "gate": "The lift gate folds inward once the carriage is unlocked.",
        },
    ),
    "dome_antechamber": Room(
        "dome_antechamber",
        "Dome Antechamber",
        "The air is colder here. An arched corridor curves around the base of the great dome, where brass plaques record eclipses, comets, and ships saved by the signal light.",
        exits={"south": "lift_landing", "north": "orrery_dome"},
        features={
            "plaques": "The plaques credit no single keeper. The station endured because people left each other instructions.",
            "inner door": "A circular iris door stands open just enough to reveal the heart of the dome beyond.",
        },
    ),
    "orrery_dome": Room(
        "orrery_dome",
        "Orrery Dome",
        "The main dome opens above an immense brass orrery whose tracks lead upward into the beacon lens housing. Three alignment levers surround a silver socket where something vital is missing.",
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
        "A narrow cave opens beneath the cliff, safe only at this stage of the tide. The walls glitter with mica and discarded offerings left by superstitious keepers.",
        exits={"north": "cliff_path"},
        features={
            "offerings": "Buttons, shells, and candle wax cluster in a dry niche above the tide line.",
            "wall": "One rock face bears old chalk tally marks and a scratched keeper's proverb.",
        },
    ),
    "keepers_quarters": Room(
        "keepers_quarters",
        "Keeper's Quarters",
        "A hidden room tucked behind the moon painting. The chamber holds a narrow cot, a tea service, and shelves of private notebooks that never entered the official archive.",
        exits={"east": "west_hall"},
        features={
            "cot": "The blankets are folded with military precision.",
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
        "Asterfall Observatory has been dark for nine nights.\n"
        "The relief ship should already be visible offshore, but the storm has swallowed the horizon and the station's signal beacon remains dead.\n"
        "You have one chance to climb inside, restore the Dawn Signal, and give the coast something brighter than lightning to steer by.\n\n"
        f"Run seed: {state.seed}\n"
        f"{state.variation['intro_line']}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Asterfall Observatory.")
    parser.add_argument("seed", nargs="?", type=int, help="Optional seed for a reproducible run.")
    return parser.parse_args(argv)
