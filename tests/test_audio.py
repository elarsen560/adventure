from __future__ import annotations

from unittest.mock import patch

from game.audio_assets import ensure_audio_assets
from game.audio import AudioConfig, AudioManager, CROSSFADE_MS, ambient_key_for_state
from game.engine import Game


class FakeAudio:
    def __init__(self):
        self.updates = []
        self.sfx = []

    def update_for_state(self, state) -> None:
        self.updates.append((state.current_room, dict(state.flags)))

    def play_sfx(self, name: str) -> None:
        self.sfx.append(name)


class FakeChannel:
    def __init__(self):
        self.calls = []
        self.volume = None

    def play(self, sound, loops=0, fade_ms=0):
        self.calls.append(("play", sound, loops, fade_ms))

    def stop(self):
        self.calls.append(("stop",))

    def fadeout(self, ms):
        self.calls.append(("fadeout", ms))

    def set_volume(self, value):
        self.volume = value
        self.calls.append(("set_volume", value))


class FakePygame:
    class mixer:
        class music:
            @staticmethod
            def set_volume(value):
                return None

        @staticmethod
        def Sound(path):
            return path


def test_audio_manager_falls_back_when_pygame_import_fails():
    manager = AudioManager(AudioConfig())
    with patch("importlib.import_module", side_effect=ImportError("no pygame")):
        assert manager.initialize() is False
    assert manager.available is False
    assert manager.failed is True


def test_ensure_audio_assets_generates_missing_files(tmp_path):
    paths = ensure_audio_assets(tmp_path / "audio")
    assert paths["music"]["main_theme"].exists()
    assert paths["ambient"]["cliff_path"].exists()
    assert paths["sfx"]["pickup"].exists()
    assert (tmp_path / "audio" / "ASSET_MANIFEST.json").exists()


def test_ambient_key_uses_stateful_variants():
    game = Game(seed=4517)
    game.state.current_room = "generator_room"
    assert ambient_key_for_state(game.state) == "generator_room_idle"
    game.state.flags["power_on"] = True
    assert ambient_key_for_state(game.state) == "generator_room_powered"
    game.state.current_room = "pump_room"
    assert ambient_key_for_state(game.state) == "pump_room_idle"
    game.state.flags["pump_drained"] = True
    assert ambient_key_for_state(game.state) == "pump_room_active"


def test_game_syncs_audio_after_room_change():
    fake = FakeAudio()
    game = Game(seed=4517, audio_manager=fake)
    game.process("go south")
    assert fake.updates[-1][0] == "sea_cave"


def test_game_plays_pickup_sfx_on_successful_take():
    fake = FakeAudio()
    game = Game(seed=4517, audio_manager=fake)
    game.state.current_room = "courtyard"
    game.state.discovered_rooms.add("courtyard")
    game.process("take brass handwheel")
    assert "pickup" in fake.sfx


def test_game_plays_power_restore_sfx_when_fuse_is_used():
    fake = FakeAudio()
    game = Game(seed=4517, audio_manager=fake)
    game.state.current_room = "generator_room"
    game.state.discovered_rooms.add("generator_room")
    game.state.inventory.append("fuse")
    game.process("use ceramic fuse on panel")
    assert "fuse_insert" in fake.sfx
    assert "power_restore" in fake.sfx


def test_audio_manager_crossfades_between_ambient_channels(tmp_path):
    manager = AudioManager(AudioConfig(root=tmp_path / "audio"))
    manager.paths = ensure_audio_assets(tmp_path / "audio")
    manager.available = True
    manager.config.ambient_enabled = True
    manager._pygame = FakePygame()
    channel_a = FakeChannel()
    channel_b = FakeChannel()
    manager._ambient_channels = [channel_a, channel_b]

    manager.play_ambient("cliff_path")
    assert manager.current_ambient == "cliff_path"
    assert manager._active_ambient_index == 0
    assert any(call[0] == "play" and call[2:] == (-1, 0) for call in channel_a.calls)

    first_call_count = len(channel_a.calls) + len(channel_b.calls)
    manager.play_ambient("cliff_path")
    assert len(channel_a.calls) + len(channel_b.calls) == first_call_count

    manager.play_ambient("sea_cave")
    assert manager.current_ambient == "sea_cave"
    assert manager._active_ambient_index == 1
    assert ("stop",) in channel_b.calls
    assert any(call[0] == "play" and call[2:] == (-1, CROSSFADE_MS) for call in channel_b.calls)
    assert ("fadeout", CROSSFADE_MS) in channel_a.calls
