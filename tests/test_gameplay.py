from game.engine import Game
from game.ambient import ambient_candidates, should_emit_ambient
from game.npcs import FEATURED_NPCS, NPC_ROLE_DEFINITIONS, valid_role_room_pairs
from game.persistence import load_game, resolve_save_path, save_game
from game.state import validate_starting_key_access
from unittest.mock import patch


def _to_room(game: Game, room_id: str) -> None:
    game.state.current_room = room_id
    game.state.discovered_rooms.add(room_id)


def test_seeded_variation_is_reproducible():
    game_a = Game(seed=1337)
    game_b = Game(seed=1337)
    assert game_a.state.variation == game_b.state.variation
    assert game_a.state.hidden_items == game_b.state.hidden_items
    assert game_a.state.featured_npc_id == game_b.state.featured_npc_id
    assert game_a.state.featured_npc_room == game_b.state.featured_npc_room
    assert game_a.state.featured_npc_role == game_b.state.featured_npc_role


def test_debug_flag_sets_runtime_mode():
    game = Game(seed=1337, debug=True)
    assert game.state.debug_mode is True


def test_save_and_load_roundtrip(tmp_path):
    game = Game(seed=2001)
    game.process("look")
    game.process("note Check the generator panel")
    path = tmp_path / "save.json"
    save_game(game.state, str(path))
    loaded = load_game(str(path))
    assert loaded.seed == game.state.seed
    assert loaded.variation == game.state.variation
    assert loaded.current_room == game.state.current_room
    assert loaded.notes == ["Check the generator panel"]
    assert loaded.hazard_type == game.state.hazard_type
    assert loaded.hazard_room == game.state.hazard_room
    assert loaded.featured_npc_id == game.state.featured_npc_id
    assert loaded.featured_npc_room == game.state.featured_npc_room
    assert loaded.featured_npc_role == game.state.featured_npc_role


def test_bare_save_name_resolves_to_saves_folder():
    path = resolve_save_path("slot1")
    assert str(path) == "saves/slot1"


def test_full_playthrough_reaches_victory():
    game = Game(seed=4517)

    key_room = game.state.variation["key_room"]
    _to_room(game, key_room)
    game.process("examine offerings" if key_room == "sea_cave" else "examine observatory" if key_room == "cliff_path" else "examine gate")
    game.process("take groundskeeper key")

    _to_room(game, "front_gate")
    game.process("unlock gate")
    game.process("go east")
    game.process("take brass handwheel")
    game.process("go north")
    game.process("go west")
    game.process("go south")
    game.process("take ceramic fuse")
    game.process("take oil flask")
    _to_room(game, "pump_room")
    game.process("use brass handwheel on spindle")
    _to_room(game, "generator_room")
    game.process("use ceramic fuse on panel")
    _to_room(game, "library")
    game.process("take constellation folio")
    _to_room(game, "conservatory")
    game.process("examine plants")
    game.process("take winding key")
    game.process("use winding key on wren")
    _to_room(game, "east_hall")
    code = " ".join(game.state.variation["archive_code"])
    game.process(f"enter {code}")
    game.process("go north")
    game.process("take star lens")
    game.process("take logbook page")
    if game.state.variation["token_room"] == "archive":
        game.process("take transit token")
    else:
        _to_room(game, "west_hall")
        game.state.flags["secret_door_open"] = True
        game.process("open painting")
        game.process("take transit token")
    _to_room(game, "lift_landing")
    if game.state.hazard_type == "snapping_lattice":
        game.process("examine gate")
    game.process("use oil flask on lift")
    game.process("go north")
    game.process("go north")
    game.process("use star lens on socket")
    expected = "set levers " + " ".join(str(v) for v in game.state.variation["alignment"])
    result = game.try_victory(expected)
    assert result is not None
    assert game.state.won is True
    assert game.state.running is True


def test_restart_uses_fresh_game_state():
    game = Game(seed=4517)
    game.process("note Remember the archive code")
    game.state.flags["power_on"] = True

    restarted = Game(debug=game.state.debug_mode)

    assert restarted.state.seed != game.state.seed
    assert restarted.state.notes == []
    assert restarted.state.recent_history == []
    assert restarted.state.npc_history == []
    assert restarted.state.flags["power_on"] is False
    assert restarted.state.discovered_rooms == {"cliff_path"}


def test_feature_synonym_guides_archive_command():
    game = Game(seed=4517)
    _to_room(game, "east_hall")
    text = game.process("examine lock")
    assert "enter <code>" in text


def test_lever_hint_nudges_special_syntax():
    game = Game(seed=4517)
    _to_room(game, "orrery_dome")
    text = game.process("examine levers")
    assert "set levers <a> <b> <c>" in text


def test_take_error_suggests_look():
    game = Game(seed=4517)
    text = game.process("take token")
    assert text.startswith("You can't take that.")


def test_map_shows_current_room_and_adjacent_unknowns():
    game = Game(seed=4517)
    text = game.process("map")
    assert "[@ CP]" in text
    assert "[? FG]" in text
    assert "[? SC]" in text
    assert "[? CY]" not in text


def test_map_shows_blocked_and_opened_known_connections():
    game = Game(seed=4517)
    game.state.current_room = "front_gate"
    game.state.discovered_rooms.update({"cliff_path", "front_gate"})
    blocked = game.process("map")
    assert "x" in blocked
    game.state.flags["front_gate_unlocked"] = True
    opened = game.process("map")
    assert "---" in opened


def test_unlocking_gate_is_stable_on_repeat():
    game = Game(seed=4517)
    _to_room(game, "front_gate")
    game.state.inventory.append("groundskeeper_key")
    assert game.process("unlock gate") == "The key turns after a gritty pause. The chain loosens and the front gate stands open."
    assert game.process("unlock gate") == "It is already unlocked."


def test_adding_note_appends_to_notebook():
    game = Game(seed=4517)
    assert game.process("note The sea cave is worth another look.") == "Noted."
    assert game.state.notes == ["The sea cave is worth another look."]


def test_reading_notes_lists_entries():
    game = Game(seed=4517)
    game.process("note First clue")
    game.process("note Second clue")
    assert game.process("notes") == "Notebook:\n1. First clue\n2. Second clue"


def test_instructions_explain_key_features_without_spoilers():
    game = Game(seed=4517)
    text = game.process("instructions")
    assert "Explore by looking closely" in text
    assert "map" in text
    assert "Ask is a constrained companion" in text


def test_note_aliases_work():
    game = Game(seed=4517)
    assert game.process("new note Lift token may be upstairs") == "Noted."
    assert game.process("read notes") == "Notebook:\n1. Lift token may be upstairs"


def test_key_is_accessible_across_many_seeds():
    for seed in range(7300, 7400):
        game = Game(seed=seed)
        validate_starting_key_access(game.state)
        key_room = game.state.variation["key_room"]
        game.state.current_room = key_room
        game.state.discovered_rooms.add(key_room)
        room_text = game.process("look")
        if key_room == "cliff_path":
            assert "metallic glint" in room_text or "small metal glint" in room_text
            text = game.process("examine observatory")
        elif key_room == "front_gate":
            assert "catches the light" in room_text
            text = game.process("examine chain")
        else:
            assert "reflects more sharply" in room_text
            text = game.process("examine offerings")
        assert "groundskeeper key" in text
        assert game.process("take groundskeeper key").startswith("You take the groundskeeper key.")


def test_transit_token_has_hint_reveal_and_is_takable_across_many_seeds():
    for seed in range(7300, 7400):
        game = Game(seed=seed)
        token_room = game.state.variation["token_room"]
        game.state.current_room = token_room
        game.state.discovered_rooms.add(token_room)
        room_text = game.process("look")
        if token_room == "archive":
            assert "dull brass circle" in room_text
            text = game.process("examine cases")
        else:
            assert "small brass glimmer" in room_text
            text = game.process("examine tea service")
        assert "transit token" in text
        assert game.process("take token").startswith("You take the transit token.")


def test_ambient_system_excludes_utility_commands():
    game = Game(seed=4517)
    game.state.turn_count = 10
    assert should_emit_ambient(game.state, "help") is False
    assert should_emit_ambient(game.state, "notes") is False
    assert should_emit_ambient(game.state, "map") is False


def test_ambient_candidates_reflect_room_and_power_state():
    game = Game(seed=4517)
    game.state.current_room = "generator_room"
    before = ambient_candidates(game.state)
    assert any("machinery" in line or "Water still glistens" in line for line in before)
    game.state.flags["power_on"] = True
    after = ambient_candidates(game.state)
    assert len(after) > len(before)
    assert any("electrical hum" in line or "relay snaps" in line for line in after)


def test_ambient_can_append_to_normal_command_output():
    game = Game(seed=4517)
    game.state.turn_count = 7
    for _ in range(6):
        text = game.process("look")
        if "\n" in text and "Exits:" in text:
            trailing = text.splitlines()[-1]
            if trailing and trailing != "Exits: east, south.":
                assert trailing != "Exits: east, south."
                return
    raise AssertionError("Expected at least one ambient line to appear over several normal commands.")


def test_goto_moves_without_changing_progression_state():
    game = Game(seed=4517, debug=True)
    game.state.flags["power_on"] = False
    text = game.process("goto archive")
    assert game.state.current_room == "archive"
    assert game.state.discovered_rooms == {"archive"}
    assert game.state.flags["power_on"] is False
    assert "Archive" in text


def test_full_map_debug_command_reveals_all_rooms():
    game = Game(seed=4517, debug=True)
    text = game.process("full map")
    assert "DEBUG FULL MAP" in text
    assert "[? OR]" in text
    assert "[? AR]" in text


def test_rooms_command_lists_room_ids_and_names():
    game = Game(seed=4517, debug=True)
    text = game.process("rooms")
    assert "Rooms:" in text
    assert "cliff_path: Cliff Path" in text
    assert "orrery_dome: Orrery Dome" in text


def test_goto_accepts_friendly_room_name():
    game = Game(seed=4517, debug=True)
    game.process("goto Orrery Dome")
    assert game.state.current_room == "orrery_dome"


def test_room_description_noun_can_resolve_hidden_key_object():
    game = Game(seed=7308)
    text = game.process("examine glint")
    assert "groundskeeper key" in text
    assert game.process("take key").startswith("You take the groundskeeper key.")


def test_fuzzy_item_matching_handles_split_word():
    game = Game(seed=4517)
    game.state.current_room = "courtyard"
    game.state.discovered_rooms.add("courtyard")
    assert game.process("take hand wheel").startswith("You take the brass handwheel.")


def test_open_without_target_uses_single_obvious_object():
    game = Game(seed=4517)
    game.state.current_room = "front_gate"
    game.state.discovered_rooms.add("front_gate")
    game.state.inventory.append("groundskeeper_key")
    game.process("unlock gate")
    assert "ready" in game.process("open")


def test_featured_npc_assignment_is_valid():
    for seed in range(4500, 4550):
        game = Game(seed=seed)
        profile = FEATURED_NPCS[game.state.featured_npc_id]
        assert game.state.featured_npc_role in NPC_ROLE_DEFINITIONS
        assert (game.state.featured_npc_role, game.state.featured_npc_room) in valid_role_room_pairs(profile, game.state.hazard_room)


def test_featured_npc_talk_reveals_engine_controlled_clue():
    game = Game(seed=4517)
    game.state.featured_npc_id = "miss_fenn"
    game.state.featured_npc_room = "library"
    game.state.featured_npc_role = "clue_interpreter"
    game.state.current_room = "library"
    game.state.discovered_rooms.add("library")
    game.state.inventory.append("constellation_folio")
    with patch("game.engine.request_npc_response", return_value="Those four names belong to a lock, I think."):
        text = game.process("talk Miss Fenn")
    assert "Miss Fenn says" in text
    assert game.state.featured_npc_met is True
    assert game.state.featured_npc_revealed is True


def test_featured_npc_item_gate_grants_match_tin_once():
    game = Game(seed=4517)
    game.state.featured_npc_id = "mr_finch"
    game.state.featured_npc_room = "foyer"
    game.state.featured_npc_role = "item_gate"
    game.state.current_room = "foyer"
    game.state.discovered_rooms.add("foyer")
    with patch("game.engine.request_npc_response", return_value="Take these matches. The place has corners that answer better to a poor light."):
        first = game.process("talk Mr. Finch")
    assert "Mr. Finch says" in first
    assert "match_tin" in game.state.inventory
    with patch("game.engine.request_npc_response", return_value="I have already done what little I can in that line."):
        second = game.process("talk Mr. Finch")
    assert game.state.inventory.count("match_tin") == 1
    assert "Mr. Finch says" in second


def test_talk_parser_handles_character_plus_message_for_featured_npc():
    game = Game(seed=4517)
    game.state.featured_npc_id = "captain_vale"
    game.state.featured_npc_room = "foyer"
    game.state.featured_npc_role = "access_insight"
    game.state.current_room = "foyer"
    game.state.discovered_rooms.add("foyer")
    with patch("game.engine.request_npc_response", return_value="The gate still looks like the matter before all other matters."):
        text = game.process("talk Captain Vale What do you make of the gate?")
    assert "Captain Vale says" in text
    assert game.state.npc_history[-1]["player"] == "What do you make of the gate?"


def test_seeded_hazard_is_reproducible_and_midgame():
    game_a = Game(seed=4518)
    game_b = Game(seed=4518)
    assert game_a.state.hazard_type == game_b.state.hazard_type
    assert game_a.state.hazard_room == game_b.state.hazard_room
    assert game_a.state.hazard_room in {"workshop", "archive", "lift_landing"}


def test_workshop_hazard_warns_then_resolves_cleanly():
    game = Game(seed=4518)
    _to_room(game, "workshop")
    room_text = game.process("look")
    assert "chain hoist" in room_text
    warning = game.process("take ceramic fuse")
    assert "closer look at the bench" in warning
    assert "fuse" not in game.state.inventory
    resolved = game.process("examine bench")
    assert "left would keep clear" in resolved
    assert game.state.hazard_resolved is True
    assert game.process("take ceramic fuse").startswith("You take the ceramic fuse.")


def test_archive_hazard_warns_before_game_over_on_repeat():
    game = Game(seed=4519)
    _to_room(game, "archive")
    room_text = game.process("look")
    assert "ready to slide" in room_text
    first = game.process("take star lens")
    assert "Another careless tug might bring the whole table over" in first
    second = game.process("take star lens")
    assert "sealed room closes over the noise" in second
    assert game.state.running is False


def test_lift_hazard_blocks_once_then_allows_safe_passage():
    game = Game(seed=4517)
    _to_room(game, "lift_landing")
    game.state.flags["power_on"] = True
    game.state.flags["lift_oiled"] = True
    game.state.inventory.append("transit_token")
    room_text = game.process("look")
    assert "sprung inward" in room_text
    warning = game.process("go north")
    assert "Examining it would be wiser" in warning
    assert game.state.current_room == "lift_landing"
    resolved = game.process("examine gate")
    assert "fault is manageable" in resolved
    text = game.process("go north")
    assert "Dome Antechamber" in text
    assert game.state.current_room == "dome_antechamber"


def test_workshop_hazard_accepts_obvious_room_nouns():
    game = Game(seed=4518)
    _to_room(game, "workshop")
    text = game.process("examine hoist")
    assert "keep clear of it" in text
    assert game.state.hazard_resolved is True


def test_workshop_hazard_chain_alias_matches_same_resolution():
    game = Game(seed=4518)
    _to_room(game, "workshop")
    text = game.process("examine chain")
    assert "keep clear of it" in text
    assert game.state.hazard_resolved is True


def test_archive_hazard_accepts_leaning_stack_noun():
    game = Game(seed=4519)
    _to_room(game, "archive")
    text = game.process("examine stack")
    assert "safe way to reach the table" in text
    assert game.state.hazard_resolved is True


def test_lift_hazard_accepts_runner_noun():
    game = Game(seed=4517)
    _to_room(game, "lift_landing")
    text = game.process("examine runner")
    assert "fault is manageable" in text
    assert game.state.hazard_resolved is True


def test_hazard_room_hint_text_surfaces_obvious_nouns():
    game = Game(seed=4518)
    _to_room(game, "workshop")
    text = game.process("examine nonsense")
    assert "You might try" in text
    assert "bench" in text
    assert "hoist" in text
