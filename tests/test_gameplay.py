from game.engine import Game
from game.persistence import load_game, resolve_save_path, save_game


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
    path = tmp_path / "save.json"
    save_game(game.state, str(path))
    loaded = load_game(str(path))
    assert loaded.seed == game.state.seed
    assert loaded.variation == game.state.variation
    assert loaded.current_room == game.state.current_room


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
    assert "look" in text
