from types import SimpleNamespace

from game.audio import AudioConfig
from game.tk_app import DesktopAudioManager, DesktopGameSession, POST_WIN_PROMPT, centered_geometry


def make_args(seed=4517, debug=False, mute=True, audio_preset="normal"):
    return SimpleNamespace(seed=seed, debug=debug, mute=mute, audio_preset=audio_preset)


def make_audio():
    return DesktopAudioManager(AudioConfig(enabled=False))


def test_desktop_session_startup_includes_intro_and_status():
    session = DesktopGameSession(make_args(), audio_manager=make_audio())
    lines = session.startup_lines()
    assert "Run seed:" in lines[0]
    assert "Cliff Path" in lines[1]
    assert "help" in lines[2]
    assert lines[3].startswith("Audio:")
    session.shutdown()


def test_centered_geometry_places_window_in_screen_center():
    assert centered_geometry(1600, 1000, 1200, 760) == "1200x760+200+120"


def test_desktop_session_restart_creates_fresh_game():
    session = DesktopGameSession(make_args(seed=4517), audio_manager=make_audio())
    session.game.process("note Remember the archive code")
    session.game.state.won = True
    restart = session.handle_command("restart")
    assert restart.lines[0] == "> restart"
    assert restart.reset_transcript is True
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
