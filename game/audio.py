from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path

from game.audio_assets import ensure_audio_assets


def _env_enabled(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "off", "no"}


@dataclass
class AudioConfig:
    enabled: bool = True
    music_enabled: bool = True
    ambient_enabled: bool = True
    sfx_enabled: bool = True
    preset: str = "normal"
    root: Path = Path("assets/audio")

    @classmethod
    def from_runtime(cls, *, mute: bool = False, preset: str = "normal") -> "AudioConfig":
        enabled = not mute and _env_enabled("ASTERFALL_AUDIO", True)
        return cls(
            enabled=enabled,
            music_enabled=enabled and _env_enabled("ASTERFALL_MUSIC", True),
            ambient_enabled=enabled and _env_enabled("ASTERFALL_AMBIENT", True),
            sfx_enabled=enabled and _env_enabled("ASTERFALL_SFX", True),
            preset=os.environ.get("ASTERFALL_AUDIO_PRESET", preset),
        )


class AudioManager:
    def __init__(self, config: AudioConfig | None = None):
        self.config = config or AudioConfig()
        self.available = False
        self.failed = False
        self.paths: dict[str, dict[str, Path]] = {}
        self.current_music = None
        self.current_ambient = None
        self._pygame = None
        self._ambient_channel = None
        self._sfx_channel = None

    def initialize(self) -> bool:
        if not self.config.enabled:
            return False
        try:
            self.paths = ensure_audio_assets(self.config.root)
            pygame = importlib.import_module("pygame")
            pygame.mixer.pre_init(22050, -16, 1, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)
            self._pygame = pygame
            self._ambient_channel = pygame.mixer.Channel(1)
            self._sfx_channel = pygame.mixer.Channel(2)
            self._apply_volumes()
            self.available = True
            return True
        except Exception:
            self.failed = True
            self.available = False
            return False

    def shutdown(self) -> None:
        if not self.available or self._pygame is None:
            return
        try:
            self._pygame.mixer.music.stop()
            self._ambient_channel.stop()
            self._sfx_channel.stop()
            self._pygame.mixer.quit()
        except Exception:
            pass
        self.available = False

    def start_session(self, state) -> None:
        if not self.available:
            return
        self.play_music("main_theme")
        self.update_for_state(state)

    def update_for_state(self, state) -> None:
        if not self.available:
            return
        ambient_key = ambient_key_for_state(state)
        if self.config.ambient_enabled:
            self.play_ambient(ambient_key)
        elif self._ambient_channel:
            self._ambient_channel.stop()

    def play_music(self, name: str) -> None:
        if not self.available or not self.config.music_enabled:
            return
        if self.current_music == name:
            return
        path = self.paths.get("music", {}).get(name)
        if not path or not path.exists():
            return
        try:
            self._pygame.mixer.music.load(str(path))
            self._pygame.mixer.music.play(-1)
            self.current_music = name
        except Exception:
            self.failed = True
            self.available = False

    def play_ambient(self, name: str) -> None:
        if not self.available or not self.config.ambient_enabled or self._ambient_channel is None:
            return
        if self.current_ambient == name:
            return
        path = self.paths.get("ambient", {}).get(name)
        if not path or not path.exists():
            return
        try:
            sound = self._pygame.mixer.Sound(str(path))
            self._ambient_channel.play(sound, loops=-1)
            self.current_ambient = name
        except Exception:
            self.failed = True
            self.available = False

    def play_sfx(self, name: str) -> None:
        if not self.available or not self.config.sfx_enabled or self._sfx_channel is None:
            return
        path = self.paths.get("sfx", {}).get(name)
        if not path or not path.exists():
            return
        try:
            sound = self._pygame.mixer.Sound(str(path))
            self._sfx_channel.play(sound)
        except Exception:
            pass

    def status_line(self) -> str:
        if not self.config.enabled:
            return "Audio: off."
        if self.available:
            return f"Audio: on ({self.config.preset})."
        return "Audio: unavailable; continuing silently."

    def _apply_volumes(self) -> None:
        if self._pygame is None:
            return
        preset = self.config.preset if self.config.preset in {"low", "normal"} else "normal"
        if preset == "low":
            music, ambient, sfx = 0.18, 0.12, 0.22
        else:
            music, ambient, sfx = 0.32, 0.22, 0.40
        self._pygame.mixer.music.set_volume(music if self.config.music_enabled else 0.0)
        if self._ambient_channel is not None:
            self._ambient_channel.set_volume(ambient if self.config.ambient_enabled else 0.0)
        if self._sfx_channel is not None:
            self._sfx_channel.set_volume(sfx if self.config.sfx_enabled else 0.0)


def ambient_key_for_state(state) -> str:
    room = state.current_room
    if room == "generator_room":
        return "generator_room_powered" if state.flags.get("power_on") else "generator_room_idle"
    if room == "pump_room":
        return "pump_room_active" if state.flags.get("pump_drained") else "pump_room_idle"
    if room == "lift_landing":
        return "lift_landing_powered" if state.flags.get("power_on") else "lift_landing_idle"
    if room == "orrery_dome":
        return "orrery_dome_energized" if state.flags.get("power_on") or state.flags.get("lens_installed") else "orrery_dome_idle"
    return room

