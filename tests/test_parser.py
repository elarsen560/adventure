from game.parser import parse_command


def test_direction_shorthand_maps_to_go():
    command = parse_command("n")
    assert command.action == "go"
    assert command.target == "north"


def test_use_on_parses_tool_and_target():
    command = parse_command("use oil flask on the lift")
    assert command.action == "use"
    assert command.tool == "oil flask"
    assert command.target == "lift"


def test_talk_to_normalizes():
    command = parse_command("talk to Wren")
    assert command.action == "talk"
    assert command.target == "wren"


def test_enter_preserves_code_words():
    command = parse_command("enter heron ember crown tide")
    assert command.action == "enter"
    assert command.target == "heron ember crown tide"


def test_apply_alias_maps_to_use():
    command = parse_command("apply oil flask to the lift")
    assert command.action == "use"
    assert command.target == "lift"


def test_map_alias_maps_to_map_command():
    command = parse_command("m")
    assert command.action == "map"


def test_note_preserves_text_case():
    command = parse_command("note Check the east lift slot")
    assert command.action == "note"
    assert command.target == "Check the east lift slot"


def test_new_note_alias_maps_to_note():
    command = parse_command("new note Archive order: heron ember crown tide")
    assert command.action == "note"
    assert command.target == "Archive order: heron ember crown tide"


def test_read_notes_alias_maps_to_notes():
    command = parse_command("read notes")
    assert command.action == "notes"
