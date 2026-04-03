from game.engine import Game
from game.persistence import load_game, resolve_save_path, save_game
from game.state import validate_starting_key_access


def _to_room(game: Game, room_id: str) -> None:
    game.state.current_room = room_id
    game.state.discovered_rooms.add(room_id)


def test_seeded_variation_is_reproducible():
    game_a = Game(seed=1337)
    game_b = Game(seed=1337)
    assert game_a.state.variation == game_b.state.variation
    assert game_a.state.hidden_items == game_b.state.hidden_items


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
    game.process("use oil flask on lift")
    game.process("go north")
    game.process("go north")
    game.process("use star lens on socket")
    expected = "set levers " + " ".join(str(v) for v in game.state.variation["alignment"])
    result = game.try_victory(expected)
    assert result is not None
    assert game.state.won is True


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
    assert text == "You can't take that."


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
        assert game.process("take groundskeeper key") == "You take the groundskeeper key."


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
        assert game.process("take token") == "You take the transit token."
