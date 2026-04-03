from __future__ import annotations

import random
import sys
from pathlib import Path

from game.companion import FALLBACK_MESSAGE, build_companion_context, build_companion_prompt, companion_available, request_companion_response
from game.content import ITEMS, NPCS, ROOMS, intro_text, parse_args
from game.ambient import select_ambient_line, should_emit_ambient
from game.map import render_map, room_lookup
from game.parser import Command, parse_command
from game.persistence import load_game, save_game
from game.state import GameState, best_match, current_room_items, extracted_keywords, find_item_id, find_npc_id, phrase_variants, reveal_hidden_item, visible_npcs


FEATURE_ALIASES = {
    "front_gate": {
        "front gate": "gate",
        "lock": "gate",
        "gate lock": "gate",
        "padlock": "gate",
        "gate mechanism": "gate",
        "mechanism": "gate",
        "device": "gate",
        "chains": "chain",
        "links": "chain",
    },
    "courtyard": {
        "spout": "fountain",
        "basin": "fountain",
        "compass": "tiles",
        "rose": "tiles",
    },
    "west_hall": {
        "moon painting": "painting",
        "frame": "painting",
        "latch": "painting",
        "panel": "painting",
    },
    "east_hall": {
        "door": "archive door",
        "archive": "archive door",
        "archive lock": "archive door",
        "wheel": "archive door",
        "wheel lock": "archive door",
        "lock": "archive door",
        "mechanism": "archive door",
        "device": "archive door",
        "cables": "conduits",
        "wires": "conduits",
    },
    "workshop": {
        "table": "bench",
        "tarp": "lift gears",
        "gears": "lift gears",
    },
    "generator_room": {
        "dynamo": "generator",
        "machine": "generator",
        "mechanism": "generator",
        "device": "generator",
        "slot": "panel",
        "fuse slot": "panel",
        "maintenance panel": "panel",
        "flood mark": "water",
    },
    "pump_room": {
        "valve": "spindle",
        "wheel mount": "spindle",
        "pump": "spindle",
        "mechanism": "spindle",
        "device": "spindle",
        "drain": "cistern",
    },
    "conservatory": {
        "planters": "labels",
        "plaques": "labels",
        "beds": "plants",
        "vines": "plants",
    },
    "archive": {
        "table": "cases",
        "case": "cases",
        "instruments": "cases",
        "files": "drawers",
    },
    "lift_landing": {
        "cage": "lift",
        "carriage": "lift",
        "slot": "lift",
        "call slot": "lift",
        "mechanism": "lift",
        "device": "lift",
        "lattice": "gate",
        "lift gate": "gate",
        "gears": "lift",
    },
    "dome_antechamber": {
        "door": "inner door",
        "iris": "inner door",
    },
    "orrery_dome": {
        "machine": "orrery",
        "mechanism": "orrery",
        "device": "orrery",
        "beacon": "orrery",
        "mount": "socket",
        "ring": "socket",
        "controls": "levers",
        "alignment controls": "levers",
    },
    "sea_cave": {
        "niche": "offerings",
        "chalk": "wall",
        "marks": "wall",
    },
    "keepers_quarters": {
        "bed": "cot",
        "tea": "tea service",
        "tray": "tea service",
        "service": "tea service",
        "journals": "notebooks",
    },
}

ROOM_DESCRIPTION_REFERENTS = {
    "cliff_path": {
        "glint": "observatory",
        "edge": "observatory",
        "path edge": "observatory",
        "metallic glint": "observatory",
        "metal": "observatory",
    },
    "front_gate": {
        "ironwork": "gate",
        "bar": "gate",
        "bars": "gate",
        "hinge": "gate",
    },
    "courtyard": {
        "metallic": "fountain",
        "center": "fountain",
    },
    "generator_room": {
        "machine": "generator",
    },
    "keepers_quarters": {
        "glimmer": "tea service",
        "comforts": "tea service",
    },
}


HELP_TEXT = """Supported commands:
look
examine <thing>
go <direction>
north/south/east/west (or n/s/e/w)
take/get <item>
drop <item>
use <item>
use <item> on <target>
open <thing>
unlock <thing>
enter <code>
ask [question]
note <text>
notes
inventory / i
map
talk <character>
help
save [filename]
load [filename]
quit
set levers <a> <b> <c>"""

DEBUG_HELP_TEXT = """Debug commands:
goto <room>
full map
rooms"""


class Game:
    def __init__(self, seed: int | None = None, debug: bool = False):
        self.state = GameState.new(seed if seed is not None else random.randint(1000, 9999))
        self.state.debug_mode = debug

    def set_state(self, state: GameState) -> None:
        self.state = state

    def describe_room(self) -> str:
        room = ROOMS[self.state.current_room]
        lines = [f"\n{room.name}", room.description]
        state_note = self.room_state_note()
        if state_note:
            lines.append(state_note)
        hidden_note = self.hidden_item_hint()
        if hidden_note:
            lines.append(hidden_note)
        room_items = current_room_items(self.state)
        if room_items:
            lines.append("You notice here: " + ", ".join(ITEMS[item_id].name for item_id in room_items) + ".")
        npcs = visible_npcs(self.state, self.state.current_room)
        if npcs:
            names = []
            for npc_id in npcs:
                name = NPCS[npc_id].name
                if npc_id == "wren" and not self.state.flags["wren_awake"]:
                    name += " (motionless)"
                names.append(name)
            lines.append("Present: " + ", ".join(names) + ".")
        exits = list(room.exits)
        if self.state.current_room == "east_hall":
            exits = [direction for direction in exits if direction != "north"]
            exits.append("north" if self.state.flags["archive_unlocked"] else "north (sealed archive door)")
        lines.append("Exits: " + ", ".join(exits) + ".")
        return "\n".join(lines)

    def room_state_note(self) -> str | None:
        room_id = self.state.current_room
        flags = self.state.flags
        if room_id == "front_gate" and flags["front_gate_unlocked"]:
            return "The chain now hangs slack from the open gate."
        if room_id == "pump_room" and flags["pump_drained"]:
            return "The spindle now wears its fitted handwheel, and the drainage channels rumble steadily below."
        if room_id == "generator_room" and flags["power_on"]:
            return "The dynamo is running now, filling the room with a steady electrical thrum."
        if room_id == "conservatory" and flags["wren_awake"]:
            return "Wren stands alert among the wet vines, head tilted as if listening for distant machinery."
        if room_id == "east_hall" and flags["archive_unlocked"]:
            return "The archive door stands unsealed, its wheel lock resting at the completed sequence."
        if room_id == "lift_landing":
            notes = []
            if flags["power_on"]:
                notes.append("the call slot glows with restored power")
            if flags["lift_oiled"]:
                notes.append("fresh oil darkens the guide gears")
            if notes:
                return "The lift looks changed: " + "; ".join(notes) + "."
        if room_id == "west_hall" and flags["secret_door_open"]:
            return "The moon painting hangs open on a concealed hinge, exposing the passage behind it."
        if room_id == "orrery_dome":
            notes = []
            if flags["lens_installed"]:
                notes.append("the star lens is seated in the silver socket")
            else:
                notes.append("the empty silver socket still waits for its missing lens")
            notes.append("the three levers are numbered one through four")
            return "The mechanism has changed: " + "; ".join(notes) + "."
        return None

    def hidden_item_hint(self) -> str | None:
        hidden = self.state.hidden_items.get(self.state.current_room, [])
        if "groundskeeper_key" in hidden:
            if self.state.current_room == "cliff_path":
                return "Lightning picks out a brief metallic glint somewhere near the edge of the path."
            if self.state.current_room == "front_gate":
                return "Something small catches the light within the gate's ironwork."
            if self.state.current_room == "sea_cave":
                return "Among the offerings, one hard shape reflects more sharply than shell or wax."
        room_items = current_room_items(self.state)
        if "transit_token" in room_items:
            if self.state.current_room == "archive":
                return "On the central table, a dull brass circle interrupts the ordered grey of cases and papers."
            if self.state.current_room == "keepers_quarters":
                return "A small brass glimmer rests among the private comforts of the room."
        return None

    def resolve_feature(self, target: str) -> str | None:
        room = ROOMS[self.state.current_room]
        option_map: dict[str, str] = {}
        for feature_name, feature_text in room.features.items():
            for variant in phrase_variants(feature_name):
                option_map[variant] = feature_name
            for keyword in extracted_keywords(feature_name, feature_text):
                option_map.setdefault(keyword, feature_name)
        for alias, feature_name in FEATURE_ALIASES.get(self.state.current_room, {}).items():
            for variant in phrase_variants(alias):
                option_map[variant] = feature_name
        for alias, feature_name in ROOM_DESCRIPTION_REFERENTS.get(self.state.current_room, {}).items():
            for variant in phrase_variants(alias):
                option_map[variant] = feature_name
        return best_match(target, option_map)

    def room_target_hints(self) -> str:
        room = ROOMS[self.state.current_room]
        names = list(room.features)
        names.extend(ITEMS[item_id].name for item_id in current_room_items(self.state))
        npcs = visible_npcs(self.state, self.state.current_room)
        names.extend(NPCS[npc_id].name for npc_id in npcs)
        if not names:
            return "There is nothing obvious to focus on."
        return "You might try " + ", ".join(names[:4]) + "."

    def single_feature_choice(self, *, allow_hidden_gate: bool = False) -> str | None:
        room = ROOMS[self.state.current_room]
        choices = list(room.features)
        if allow_hidden_gate and self.state.current_room == "front_gate":
            return "gate"
        return choices[0] if len(choices) == 1 else None

    def unknown_target_hint(self) -> str:
        room_id = self.state.current_room
        hints = {
            "front_gate": "Try examining the gate, chain, or lock.",
            "east_hall": "Try examining the archive door or conduits.",
            "generator_room": "Try examining the generator or panel.",
            "pump_room": "Try examining the spindle or cistern.",
            "lift_landing": "Try examining the lift or its gate.",
            "orrery_dome": "Try examining the orrery, socket, or levers.",
        }
        return hints.get(room_id, "Try 'look' to review the room, or 'examine <thing>' for a closer look.")

    def set_levers_hint(self) -> str:
        return "When you know the final positions, use the exact syntax: 'set levers <a> <b> <c>'."

    def process(self, text: str) -> str:
        command = parse_command(text)
        if command.action == "empty":
            return "The storm says plenty already. Type a command."

        handlers = {
            "look": self.do_look,
            "examine": self.do_examine,
            "go": self.do_go,
            "take": self.do_take,
            "drop": self.do_drop,
            "use": self.do_use,
            "open": self.do_open,
            "unlock": self.do_unlock,
            "ask": self.do_ask,
            "note": self.do_note,
            "notes": self.do_notes,
            "inventory": self.do_inventory,
            "map": self.do_map,
            "goto": self.do_goto,
            "full_map": self.do_full_map,
            "rooms": self.do_rooms,
            "help": self.do_help,
            "talk": self.do_talk,
            "save": self.do_save,
            "load": self.do_load,
            "quit": self.do_quit,
            "enter": self.do_enter,
        }
        handler = handlers.get(command.action)
        if not handler:
            if self.state.current_room == "orrery_dome" and text.lower().strip().startswith(("set ", "align ", "position ")):
                return self.set_levers_hint()
            return "I don't understand that."
        response = handler(command)
        self.record_history(command.raw or command.action, response)
        self.state.turn_count += 1
        ambient = None
        if self.state.running and should_emit_ambient(self.state, command.action):
            ambient = select_ambient_line(self.state)
        if ambient:
            return response + "\n" + ambient
        return response

    def record_history(self, command_text: str, response_text: str) -> None:
        self.state.recent_history.append({"command": command_text, "response": response_text})
        self.state.recent_history = self.state.recent_history[-10:]

    def do_look(self, _: Command) -> str:
        return self.describe_room()

    def do_examine(self, command: Command) -> str:
        if not command.target:
            return "Examine what?"
        target = command.target
        room = ROOMS[self.state.current_room]

        if target in {"room", "around"}:
            return self.describe_room()
        feature = self.resolve_feature(target)
        if feature:
            return self.examine_feature(feature)

        item_id = find_item_id(target, self.state.inventory + current_room_items(self.state))
        if item_id:
            if item_id in self.state.clue_texts:
                return self.state.clue_texts[item_id]
            return ITEMS[item_id].description

        npc_id = find_npc_id(target, visible_npcs(self.state, self.state.current_room))
        if npc_id:
            if npc_id == "wren" and not self.state.flags["wren_awake"]:
                return NPCS[npc_id].description + " A keyhole glints in the spring housing at its back."
            return NPCS[npc_id].description + " Its glass eyes track you with patient attention."

        if self.state.current_room == "conservatory" and target in {"labels", "plaques", "planters"}:
            return self.state.clue_texts["conservatory_labels"]
        if self.state.current_room == "west_hall" and target in {"moon painting", "painting"}:
            if self.state.flags["secret_door_open"]:
                return "The painting has swung aside to reveal the hidden keeper's quarters."
            return "Behind the frame, the wall sounds hollow."

        return "You see nothing special. " + self.room_target_hints()

    def examine_feature(self, target: str) -> str:
        room_id = self.state.current_room
        room = ROOMS[room_id]
        if room_id == "front_gate" and target in {"gate", "chain"} and "groundskeeper_key" in self.state.hidden_items.get("front_gate", []):
            reveal_hidden_item(self.state, "front_gate", "groundskeeper_key")
            feature_text = room.features[target]
            return feature_text + " The ironwork groans in the wind. Caught in the links near one hinge is a groundskeeper key."
        if room_id == "cliff_path" and target == "observatory" and "groundskeeper_key" in self.state.hidden_items.get("cliff_path", []):
            reveal_hidden_item(self.state, "cliff_path", "groundskeeper_key")
            return room.features[target] + " Even from here the front gate lock looks intact. At the edge of the path a small metal glint catches the lightning: a groundskeeper key."
        if room_id == "sea_cave" and target in {"offerings", "wall"} and "groundskeeper_key" in self.state.hidden_items.get("sea_cave", []):
            reveal_hidden_item(self.state, "sea_cave", "groundskeeper_key")
            return room.features[target] + " Behind a crust of wax and shells lies a groundskeeper key left among the offerings."
        if room_id == "archive" and target == "cases" and "transit_token" in current_room_items(self.state):
            return room.features[target] + " One open padded case holds a transit token, its brass face stamped DOME LIFT."
        if room_id == "keepers_quarters" and target == "tea service" and "transit_token" in current_room_items(self.state):
            return room.features[target] + " Beside the cup sits a transit token, as if set down during an interrupted meal."
        if room_id == "keepers_quarters" and target == "notebooks" and "transit_token" in current_room_items(self.state):
            return room.features[target] + " A transit token has been tucked beside the shelf, close to hand."
        if room_id == "conservatory" and target in {"plants", "shutters"} and "winding_key" in self.state.hidden_items.get("conservatory", []):
            reveal_hidden_item(self.state, "conservatory", "winding_key")
            return room.features[target] + " One tough vine has wrapped itself around something metallic. Tangled in the stems is a brass winding key."
        if room_id == "front_gate" and target == "gate":
            if self.state.flags["front_gate_unlocked"]:
                return "The gate stands open now, chain loose and lock defeated. You can go east into the courtyard."
            return room.features[target] + " The lock looks like the part that matters."
        if room_id == "east_hall" and target == "archive door":
            if self.state.flags["archive_unlocked"]:
                return "The archive door stands open, its wheel lock resting in the solved position."
            return room.features[target] + " The wheel lock suggests a four-word sequence. If you know it, try 'enter <code>'."
        if room_id == "generator_room" and target == "generator":
            if self.state.flags["power_on"]:
                return "The dynamo is alive now, its coils humming behind the panel."
            return room.features[target] + " The exposed panel and empty fuse slot are the obvious problem."
        if room_id == "generator_room" and target == "panel":
            if self.state.flags["power_on"]:
                return "A ceramic fuse is seated firmly in the panel. The indicator lamp glows a steady amber."
            return room.features[target] + " The slot looks sized for a ceramic fuse cartridge."
        if room_id == "pump_room" and target == "spindle":
            if self.state.flags["pump_drained"]:
                return "The handwheel is fitted and the spindle is locked open. The drainage system is already working."
            return room.features[target] + " It needs a wheel or handle before you can turn it."
        if room_id == "lift_landing" and target == "lift":
            if not self.state.flags["power_on"]:
                return room.features[target] + " Without power, without oil, and without a transit token, it is going nowhere."
            if not self.state.flags["lift_oiled"]:
                return room.features[target] + " The restored slot glows, but the guide gears still look dry."
            if "transit_token" not in self.state.inventory:
                return room.features[target] + " It is powered and free enough to move, but the call slot still wants a transit token."
            return room.features[target] + " The lift looks ready. Going north will ride it up."
        if room_id == "orrery_dome" and target == "socket":
            if self.state.flags["lens_installed"]:
                return "The star lens sits in the socket, feeding pale light into the machine's tracks."
            return room.features[target] + " The missing part is lens-shaped."
        if room_id == "orrery_dome" and target == "levers":
            if self.state.flags["lens_installed"]:
                return room.features[target] + " When you know the three final numbers, use 'set levers <a> <b> <c>'."
            return room.features[target] + " The machine likely needs its lens before the final alignment matters, but the command you will eventually need is 'set levers <a> <b> <c>'."
        if room_id == "west_hall" and target == "painting":
            if self.state.flags["secret_door_open"]:
                return "The moon painting has swung aside, revealing the hidden keeper's quarters."
            return room.features[target] + " The frame hides a latch, but you need a better look at it."
        if room_id == "conservatory" and target == "labels":
            return self.state.clue_texts["conservatory_labels"] + "\nThe sequence looks important enough to enter somewhere exactly as written."
        return room.features[target]

    def do_go(self, command: Command) -> str:
        if not command.target:
            exits = ", ".join(ROOMS[self.state.current_room].exits)
            return f"Go where? Exits are {exits}."
        room = ROOMS[self.state.current_room]
        direction = command.target
        if direction not in room.exits:
            return "You can't go that way."
        destination = room.exits[direction]

        if self.state.current_room == "front_gate" and direction == "east" and not self.state.flags["front_gate_unlocked"]:
            return "The gate is locked."
        if self.state.current_room == "east_hall" and direction == "north" and not self.state.flags["archive_unlocked"]:
            return "The archive door is shut."
        if self.state.current_room == "workshop" and direction == "east" and not self.state.flags["pump_drained"]:
            return "The way is flooded."
        if self.state.current_room == "lift_landing" and direction == "north":
            if not self.state.flags["power_on"]:
                return "The lift has no power."
            if not self.state.flags["lift_oiled"]:
                return "The lift jams."
            if "transit_token" not in self.state.inventory:
                return "The call slot flashes amber. The lift requires a transit token."
            return self.move_to(destination) + "\nThe lift carries you upward with the solemn patience of old machinery."

        return self.move_to(destination)

    def move_to(self, destination: str) -> str:
        self.state.current_room = destination
        self.state.discovered_rooms.add(destination)
        return self.describe_room()

    def do_take(self, command: Command) -> str:
        if not command.target:
            room_items = current_room_items(self.state)
            if len(room_items) == 1:
                item_id = room_items[0]
                self.state.room_items[self.state.current_room].remove(item_id)
                self.state.inventory.append(item_id)
                return f"You take the {ITEMS[item_id].name}."
            return "Take what?"
        item_id = find_item_id(command.target, current_room_items(self.state))
        if not item_id:
            room_items = current_room_items(self.state)
            if len(room_items) == 1 and command.target in {"it", "thing", "object"}:
                item_id = room_items[0]
                self.state.room_items[self.state.current_room].remove(item_id)
                self.state.inventory.append(item_id)
                return f"You take the {ITEMS[item_id].name}."
            names = ", ".join(ITEMS[item_id].name for item_id in room_items) if room_items else "nothing portable"
            return f"You can't take that. Here you can take {names}."
        self.state.room_items[self.state.current_room].remove(item_id)
        self.state.inventory.append(item_id)
        return f"You take the {ITEMS[item_id].name}."

    def do_drop(self, command: Command) -> str:
        if not command.target:
            if len(self.state.inventory) == 1:
                item_id = self.state.inventory[0]
                self.state.inventory.remove(item_id)
                self.state.room_items.setdefault(self.state.current_room, []).append(item_id)
                return f"You set down the {ITEMS[item_id].name}."
            return "Drop what?"
        item_id = find_item_id(command.target, self.state.inventory)
        if not item_id:
            return "You aren't carrying that."
        self.state.inventory.remove(item_id)
        self.state.room_items.setdefault(self.state.current_room, []).append(item_id)
        return f"You set down the {ITEMS[item_id].name}."

    def do_use(self, command: Command) -> str:
        if not command.tool and command.target:
            tool_id = find_item_id(command.target, self.state.inventory)
            if not tool_id:
                return "You aren't carrying that."
            return self.use_item(tool_id, None)
        if not command.tool:
            if len(self.state.inventory) == 1:
                return self.use_item(self.state.inventory[0], None)
            return "Use what?"
        tool_id = find_item_id(command.tool, self.state.inventory)
        if not tool_id:
            if len(self.state.inventory) == 1:
                tool_id = self.state.inventory[0]
                return self.use_item(tool_id, command.target)
            return "You aren't carrying that."
        return self.use_item(tool_id, command.target)

    def use_item(self, item_id: str, target: str | None) -> str:
        room_id = self.state.current_room

        if item_id == "groundskeeper_key" and room_id == "front_gate" and target in {None, "gate", "lock", "front gate"}:
            if not self.state.flags["front_gate_unlocked"]:
                self.state.flags["front_gate_unlocked"] = True
                return "The key turns after a gritty pause. The chain loosens and the front gate stands open."
            return "It is already unlocked."
        if item_id == "handwheel" and room_id == "pump_room" and target in {"spindle", "valve", "pump", None}:
            if not self.state.flags["pump_drained"]:
                self.state.flags["pump_drained"] = True
                return "You fit the handwheel to the spindle and crank until the cistern roars awake. Somewhere nearby, trapped water drains away from the generator room."
            return "The pump is already running."
        if item_id == "fuse" and room_id == "generator_room" and target in {"panel", "generator", "slot", None}:
            if not self.state.flags["power_on"]:
                self.state.flags["power_on"] = True
                if item_id in self.state.inventory:
                    self.state.inventory.remove(item_id)
                return "You seat the ceramic fuse in the open panel. The dynamo coughs, then the observatory wakes one circuit at a time with a bass electric hum."
            return "The power is already on."
        if item_id == "oil_flask" and room_id == "lift_landing" and target in {"lift", "gears", "gate", None}:
            self.state.flags["lift_oiled"] = True
            return "A few drops of clockwork oil into the exposed guide gears are enough. The lift answers with a smoother, less resentful click."
        if item_id == "winding_key" and room_id == "conservatory" and target in {"wren", "automaton", "caretaker", None}:
            if not self.state.flags["wren_awake"]:
                self.state.flags["wren_awake"] = True
                return "You wind the brass key into the automaton's spring housing. Wren straightens, blinks twice, and whispers, 'Signal first. Questions after.'"
            return "Wren is already awake."
        if item_id == "star_lens" and room_id == "orrery_dome" and target in {"socket", "orrery", "machine", None}:
            if not self.state.flags["lens_installed"]:
                self.state.flags["lens_installed"] = True
                return "The star lens settles into the silver socket with a resonant chime. Pale threads of light wake along the orrery tracks."
            return "The lens is already in place."
        if item_id == "match_tin" and room_id == "west_hall" and target in {"painting", "moon painting"}:
            if not self.state.flags["secret_door_open"]:
                self.state.flags["secret_door_open"] = True
                return "By matchlight you spot a latch hidden in the painting frame. The panel swings inward, revealing the keeper's quarters."
            return "The panel is already open."

        if room_id == "orrery_dome" and item_id == "star_lens":
            return "The star lens belongs in the socket at the center of the orrery."
        if room_id == "lift_landing" and item_id == "oil_flask":
            return "The oil needs to go on the lift itself, especially the guide gears."
        return "Nothing happens."

    def do_open(self, command: Command) -> str:
        if not command.target:
            target = self.single_feature_choice(allow_hidden_gate=True)
            if target:
                command = Command(command.action, target=target, raw=command.raw)
            else:
                return "Open what?"
        if self.state.current_room == "west_hall" and command.target in {"painting", "moon painting"}:
            if self.state.flags["secret_door_open"] or self.state.flags["wren_awake"]:
                if not self.state.flags["secret_door_open"]:
                    self.state.flags["secret_door_open"] = True
                self.state.current_room = "keepers_quarters"
                self.state.discovered_rooms.add("keepers_quarters")
                return self.describe_room()
            return "It won't open."
        if self.state.current_room == "front_gate" and command.target in {"gate", "front gate"}:
            if self.state.flags["front_gate_unlocked"]:
                return "The gate stands ready. You can go east into the courtyard."
            return "The chain and lock still hold it shut."
        return "It won't open. " + self.room_target_hints()

    def do_unlock(self, command: Command) -> str:
        if not command.target:
            if self.state.current_room == "front_gate":
                command = Command(command.action, target="gate", raw=command.raw)
            else:
                return "Unlock what?"
        if command.target in {"gate", "front gate"}:
            if "groundskeeper_key" not in self.state.inventory:
                return "You need the groundskeeper key."
            return self.use_item("groundskeeper_key", "gate")
        if command.target in {"archive", "archive door", "door"} and self.state.current_room == "east_hall":
            return "The archive lock wants a four-word sequence. Use 'enter <code>'."
        return "You can't unlock that. " + self.room_target_hints()

    def do_enter(self, command: Command) -> str:
        if self.state.current_room != "east_hall":
            return "Nothing happens."
        if not command.target:
            return "Enter what code?"
        words = command.target.split()
        if words == self.state.variation["archive_code"]:
            self.state.flags["archive_unlocked"] = True
            return "The wheel lock clicks through four perfect stops. The archive door unseals to the north."
        return "The lock clicks and rejects the sequence."

    def do_inventory(self, _: Command) -> str:
        if not self.state.inventory:
            return "You are carrying nothing."
        return "You carry: " + ", ".join(ITEMS[item_id].name for item_id in self.state.inventory) + "."

    def do_note(self, command: Command) -> str:
        if not command.target:
            return "Write what?"
        self.state.notes.append(command.target)
        return "Noted."

    def do_notes(self, _: Command) -> str:
        if not self.state.notes:
            return "Your notebook is empty."
        lines = ["Notebook:"]
        for index, note in enumerate(self.state.notes, start=1):
            lines.append(f"{index}. {note}")
        return "\n".join(lines)

    def do_ask(self, command: Command) -> str:
        if not companion_available():
            return FALLBACK_MESSAGE
        context = build_companion_context(
            room_name=ROOMS[self.state.current_room].name,
            room_text=self.describe_room().strip(),
            inventory=[ITEMS[item_id].name for item_id in self.state.inventory],
            notes=list(self.state.notes),
            map_text=render_map(self.state),
            recent_history=list(self.state.recent_history),
        )
        prompt = build_companion_prompt(context, command.target)
        return request_companion_response(prompt)

    def do_help(self, _: Command) -> str:
        if self.state.debug_mode:
            return HELP_TEXT + "\n" + DEBUG_HELP_TEXT
        return HELP_TEXT

    def do_map(self, _: Command) -> str:
        return render_map(self.state)

    def do_full_map(self, _: Command) -> str:
        if not self.state.debug_mode:
            return "I don't understand that."
        return render_map(self.state, reveal_all=True, debug_label=True)

    def do_rooms(self, _: Command) -> str:
        if not self.state.debug_mode:
            return "I don't understand that."
        lines = ["Rooms:"]
        for room_id, room in ROOMS.items():
            lines.append(f"{room_id}: {room.name}")
        return "\n".join(lines)

    def do_goto(self, command: Command) -> str:
        if not self.state.debug_mode:
            return "I don't understand that."
        if not command.target:
            return "Goto where?"
        destination = self.resolve_room_target(command.target)
        if destination is None:
            return "No such room."
        self.state.current_room = destination
        self.state.discovered_rooms = {destination}
        return self.describe_room()

    def resolve_room_target(self, query: str) -> str | None:
        direct = room_lookup(query)
        if direct:
            return direct
        normalized = " ".join(query.lower().split())
        for room_id, room in ROOMS.items():
            if normalized == room.name.lower():
                return room_id
        return None

    def do_talk(self, command: Command) -> str:
        if not command.target:
            return "Talk to whom?"
        npc_id = find_npc_id(command.target, visible_npcs(self.state, self.state.current_room))
        if not npc_id:
            return "No answer."
        if npc_id == "wren" and not self.state.flags["wren_awake"]:
            return "Wren is still and silent."

        if not self.state.flags["power_on"]:
            return "Wren says, 'Drain the lower channels. Fit the spare fuse. The station remembers how to wake.'"
        if not self.state.flags["archive_unlocked"]:
            code = " ".join(self.state.variation["archive_code"])
            return f"Wren says, 'The archive still obeys the garden order: {code}.'"
        if not self.state.flags["secret_door_open"]:
            return "Wren says, 'The keeper hid comforts behind moonlight. Fire reveals what daylight misses.'"
        if not self.state.flags["signal_lit"]:
            return "Wren says, 'Lens first, then the final three positions from the astronomer's last page. When you have them, set the levers directly.'"
        return "Wren inclines its head. 'Signal confirmed. About time.'"

    def do_save(self, command: Command) -> str:
        path = save_game(self.state, command.target)
        return f"Game saved to {path}."

    def do_load(self, command: Command) -> str:
        path = command.target
        try:
            self.state = load_game(path)
        except FileNotFoundError:
            requested = path or "the default save file"
            return f"Could not find {requested}."
        return "Game loaded.\n" + self.describe_room()

    def do_quit(self, _: Command) -> str:
        self.state.running = False
        return "You leave the observatory to its weather."

    def try_victory(self, text: str) -> str | None:
        if self.state.current_room != "orrery_dome":
            return None
        normalized = " ".join(text.lower().split())
        expected = f"set levers {' '.join(str(value) for value in self.state.variation['alignment'])}"
        if normalized in {"set lever", "set levers", "align levers", "move levers", "use levers"}:
            return self.set_levers_hint()
        if normalized.startswith("set ") and not normalized.startswith("set levers "):
            return self.set_levers_hint()
        if normalized != expected:
            return None
        if not self.state.flags["lens_installed"]:
            return "The mechanism turns a fraction, then halts. The star lens still needs to be installed."
        self.state.flags["signal_lit"] = True
        self.state.won = True
        self.state.running = False
        return (
            "The three levers fall into their final positions. The orrery gathers itself, light threads through the star lens, and the Dawn Signal erupts upward through the dome in a column of gold-white fire.\n"
            "Far out beyond the storm, a ship answers with a single horn blast.\n\n"
            "Asterfall Observatory is lit again. You have won."
        )


def run_game() -> None:
    args = parse_args(sys.argv[1:])
    game = Game(seed=args.seed, debug=args.debug)
    print(intro_text(game.state))
    print(game.describe_room())
    print("\nType 'help' for commands.")
    while game.state.running:
        try:
            raw = input("\n> ")
        except EOFError:
            print("\nThe signal can wait no longer.")
            break
        victory = game.try_victory(raw)
        if victory:
            print(victory)
            break
        response = game.process(raw)
        print(response)


def save_exists(path: str | None = None) -> bool:
    return Path(path or "saves/asterfall_save.json").exists()
