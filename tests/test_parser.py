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
