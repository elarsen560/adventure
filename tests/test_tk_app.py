from types import SimpleNamespace
from unittest.mock import patch

from game.audio import AudioConfig
from game.parser import parse_command
from game.tk_app import (
    ask_visual_path,
    DesktopAudioManager,
    DesktopGameSession,
    POST_WIN_PROMPT,
    DesktopVisualTarget,
    centered_geometry,
    npc_image_path,
    object_image_path,
    room_image_path,
    startup_cover_path,
    subsample_factor,
)


def make_args(seed=4517, debug=False, mute=True, audio_preset="normal"):
    return SimpleNamespace(seed=seed, debug=debug, mute=mute, audio_preset=audio_preset)


def make_audio():
    return DesktopAudioManager(AudioConfig(enabled=False))


def test_desktop_session_title_screen_text_stops_before_run_seed():
    session = DesktopGameSession(make_args(), audio_manager=make_audio())
    text = session.title_screen_text()
    assert text.startswith("ASTerfall Observatory")
    assert "Run seed:" not in text
    assert text.rstrip().endswith("the beacon may yet burn before the rocks claim another hull.")
    session.shutdown()


def test_centered_geometry_places_window_in_screen_center():
    assert centered_geometry(1600, 1000, 1200, 760) == "1200x760+200+120"


def test_startup_cover_path_uses_expected_repo_location():
    path = startup_cover_path()
    assert path is not None
    assert str(path).endswith("assets/images/startup/cover_v1.png")


def test_ask_visual_path_uses_expected_repo_location():
    path = ask_visual_path()
    assert path is not None
    assert str(path).endswith("assets/images/ui/ask_visual.png")


def test_room_image_path_uses_expected_repo_location():
    path = room_image_path("cliff_path")
    assert path is not None
    assert str(path).endswith("assets/images/rooms/cliff_path.png")


def test_npc_image_path_uses_expected_repo_location():
    path = npc_image_path("wren")
    assert path is not None
    assert str(path).endswith("assets/images/npc/wren.png")


def test_object_image_path_uses_expected_repo_location():
    path = object_image_path("archive door")
    assert path is not None
    assert str(path).endswith("assets/images/objects/archive_door.png")


def test_subsample_factor_scales_down_only_when_needed():
    assert subsample_factor(1600, 900, 800, 450) == 2
    assert subsample_factor(640, 400, 800, 450) == 1


def test_desktop_session_begin_gameplay_starts_with_seed_then_room():
    session = DesktopGameSession(make_args(), audio_manager=make_audio())
    lines = session.begin_gameplay()
    assert lines[0].startswith("Run seed: 4517")
    assert "Cliff Path" in lines[1]
    assert "help" in lines[2]
    assert lines[3].startswith("Audio:")
    session.shutdown()


def test_desktop_session_restart_creates_fresh_game():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.process("note Remember the archive code")
    session.game.state.won = True
    restart = session.handle_command("restart")
    assert restart.lines[0] == "> restart"
    assert restart.reset_transcript is True
    assert restart.lines[1].startswith("Run seed:")
    assert session.game.state.notes == []
    assert session.game.state.discovered_rooms == {"cliff_path"}
    session.shutdown()


def test_desktop_session_handles_post_win_quit_and_prompt():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.game.state.won = True
    prompt = session.handle_command("look")
    assert prompt.lines == ["> look", POST_WIN_PROMPT]
    quit_result = session.handle_command("quit")
    assert quit_result.should_close is True
    assert "leave the observatory" in quit_result.lines[-1]
    session.shutdown()


def test_desktop_session_quit_closes_during_normal_play():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    result = session.handle_command("quit")
    assert result.should_close is True
    assert "leave the observatory" in result.lines[-1]
    session.shutdown()


def test_desktop_session_updates_inventory_text_from_state():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.game.state.inventory.append("groundskeeper_key")
    assert "groundskeeper key" in session.inventory_text()
    session.shutdown()


def test_desktop_session_examine_wren_sets_npc_visual_focus():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "conservatory"
    result = session.handle_command("examine wren")
    assert result.lines[0] == "> examine wren"
    assert session.visual_target.kind == "npc"
    assert session.visual_target.target_id == "wren"
    session.shutdown()


def test_desktop_session_talk_alias_resolves_featured_npc_visual_focus():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.featured_npc_id = "miss_fenn"
    session.game.state.featured_npc_room = "library"
    session.game.state.current_room = "library"
    npc_id = session.resolve_visual_npc(parse_command("talk astronomer hello there"))
    assert npc_id == "miss_fenn"
    session.shutdown()


def test_desktop_session_non_npc_command_clears_visual_focus_back_to_room():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.visual_target = DesktopVisualTarget(kind="npc", target_id="wren")
    look = session.handle_command("look")
    assert look.lines[0] == "> look"
    assert session.visual_target.kind == "room"
    assert session.visual_target.target_id is None
    session.shutdown()


def test_desktop_session_examine_feature_sets_object_visual_focus():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "front_gate"
    result = session.handle_command("examine gate")
    assert result.lines[0] == "> examine gate"
    assert session.visual_target.kind == "object"
    assert session.visual_target.target_id == "gate"
    session.shutdown()


def test_desktop_session_take_item_sets_object_visual_focus():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "workshop"
    result = session.handle_command("take fuse")
    assert result.lines[0] == "> take fuse"
    assert session.visual_target.kind == "object"
    assert session.visual_target.target_id == "fuse"
    session.shutdown()


def test_desktop_session_unlock_gate_focuses_gate():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "front_gate"
    result = session.handle_command("unlock gate")
    assert result.lines[0] == "> unlock gate"
    assert session.visual_target.kind == "object"
    assert session.visual_target.target_id == "gate"
    session.shutdown()


def test_desktop_session_enter_code_focuses_archive_door():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "east_hall"
    result = session.handle_command("enter wrong code here")
    assert result.lines[0] == "> enter wrong code here"
    assert session.visual_target.kind == "object"
    assert session.visual_target.target_id == "archive door"
    session.shutdown()


def test_desktop_session_use_tool_on_stationary_target_prioritizes_target():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "generator_room"
    session.game.state.inventory.append("fuse")
    result = session.handle_command("use fuse on panel")
    assert result.lines[0] == "> use fuse on panel"
    assert session.visual_target.kind == "object"
    assert session.visual_target.target_id == "panel"
    session.shutdown()


def test_desktop_session_use_winding_key_on_wren_prioritizes_npc():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "conservatory"
    session.game.state.inventory.append("winding_key")
    result = session.handle_command("use winding key on wren")
    assert result.lines[0] == "> use winding key on wren"
    assert session.visual_target.kind == "npc"
    assert session.visual_target.target_id == "wren"
    session.shutdown()


def test_desktop_session_set_levers_focuses_levers():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "orrery_dome"
    result = session.handle_command("set levers 1 2 3")
    assert result.lines[0] == "> set levers 1 2 3"
    assert session.visual_target.kind == "object"
    assert session.visual_target.target_id == "levers"
    session.shutdown()


def test_desktop_session_room_change_overrides_temporary_object_focus():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.game.state.current_room = "west_hall"
    session.game.state.flags["secret_door_open"] = True
    result = session.handle_command("open painting")
    assert result.lines[0] == "> open painting"
    assert session.game.state.current_room == "keepers_quarters"
    assert session.visual_target.kind == "room"
    assert session.visual_target.target_id is None
    session.shutdown()


def test_desktop_session_ask_sets_ask_visual_focus():
    with patch("game.engine.companion_available", return_value=False):
        session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
        session.begin_gameplay()
        result = session.handle_command("ask")
        assert result.lines[0] == "> ask"
        assert session.visual_target.kind == "ask"
        assert session.visual_target.target_id is None
        session.shutdown()


def test_desktop_session_repeated_ask_keeps_ask_visual_focus():
    with patch("game.engine.companion_available", return_value=False):
        session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
        session.begin_gameplay()
        session.handle_command("ask")
        second = session.handle_command("ask What remains unresolved?")
        assert second.lines[0] == "> ask What remains unresolved?"
        assert session.visual_target.kind == "ask"
        session.shutdown()


def test_desktop_session_non_ask_command_clears_ask_visual_focus():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.begin_gameplay()
    session.visual_target = DesktopVisualTarget(kind="ask")
    look = session.handle_command("look")
    assert look.lines[0] == "> look"
    assert session.visual_target.kind == "room"
    assert session.visual_target.target_id is None
    session.shutdown()
