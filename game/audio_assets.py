from __future__ import annotations

import json
import math
import random
import struct
import wave
from functools import lru_cache
from pathlib import Path


SAMPLE_RATE = 22050
DEFAULT_DURATION = 6.0


MUSIC_SPECS = {
    "main_theme": {
        "duration": 24.0,
        "tones": [(110.0, 0.14), (165.0, 0.06), (220.0, 0.03)],
        "pulse": {"notes": [220.0, 262.0, 196.0, 175.0], "step": 0.75, "volume": 0.045},
        "noise": 0.004,
    }
}


AMBIENT_SPECS = {
    "cliff_path": {"noise": 0.16, "drone": [(180.0, 0.03)], "gust": 0.10, "drip": 0.0, "metal": 0.0},
    "front_gate": {"noise": 0.14, "drone": [(155.0, 0.03)], "gust": 0.08, "drip": 0.0, "metal": 0.06},
    "courtyard": {"noise": 0.13, "drone": [(145.0, 0.025)], "gust": 0.07, "drip": 0.0, "metal": 0.03},
    "foyer": {"noise": 0.05, "drone": [(98.0, 0.06), (147.0, 0.02)], "gust": 0.01, "drip": 0.0, "metal": 0.0},
    "west_hall": {"noise": 0.09, "drone": [(130.0, 0.03)], "gust": 0.05, "drip": 0.0, "metal": 0.04},
    "east_hall": {"noise": 0.06, "drone": [(92.0, 0.07), (184.0, 0.02)], "gust": 0.01, "drip": 0.0, "metal": 0.01},
    "library": {"noise": 0.03, "drone": [(110.0, 0.03)], "gust": 0.0, "drip": 0.0, "metal": 0.0},
    "workshop": {"noise": 0.05, "drone": [(120.0, 0.03)], "gust": 0.01, "drip": 0.0, "metal": 0.03},
    "generator_room_idle": {"noise": 0.05, "drone": [(70.0, 0.04), (140.0, 0.01)], "gust": 0.0, "drip": 0.0, "metal": 0.01},
    "generator_room_powered": {"noise": 0.04, "drone": [(70.0, 0.09), (140.0, 0.03), (210.0, 0.01)], "gust": 0.0, "drip": 0.0, "metal": 0.01},
    "pump_room_idle": {"noise": 0.07, "drone": [(84.0, 0.04)], "gust": 0.0, "drip": 0.05, "metal": 0.0},
    "pump_room_active": {"noise": 0.06, "drone": [(84.0, 0.08), (126.0, 0.02)], "gust": 0.0, "drip": 0.03, "metal": 0.01},
    "conservatory": {"noise": 0.04, "drone": [(156.0, 0.02)], "gust": 0.01, "drip": 0.05, "metal": 0.0},
    "archive": {"noise": 0.02, "drone": [(100.0, 0.025)], "gust": 0.0, "drip": 0.0, "metal": 0.0},
    "lift_landing_idle": {"noise": 0.05, "drone": [(78.0, 0.05), (156.0, 0.015)], "gust": 0.0, "drip": 0.0, "metal": 0.04},
    "lift_landing_powered": {"noise": 0.05, "drone": [(78.0, 0.06), (156.0, 0.02), (234.0, 0.008)], "gust": 0.0, "drip": 0.0, "metal": 0.05},
    "dome_antechamber": {"noise": 0.03, "drone": [(73.42, 0.05), (146.84, 0.018)], "gust": 0.0, "drip": 0.0, "metal": 0.01},
    "orrery_dome_idle": {"noise": 0.03, "drone": [(65.4, 0.05), (98.0, 0.02)], "gust": 0.0, "drip": 0.0, "metal": 0.0},
    "orrery_dome_energized": {"noise": 0.02, "drone": [(65.4, 0.05), (98.0, 0.02), (261.63, 0.02)], "gust": 0.0, "drip": 0.0, "metal": 0.0},
    "sea_cave": {"noise": 0.09, "drone": [(98.0, 0.02)], "gust": 0.03, "drip": 0.05, "metal": 0.0},
    "keepers_quarters": {"noise": 0.02, "drone": [(116.54, 0.02)], "gust": 0.0, "drip": 0.0, "metal": 0.0},
}


SFX_SPECS = {
    "pickup": {"duration": 0.16, "notes": [587.33, 783.99], "decay": 4.0, "volume": 0.18},
    "gate_unlock": {"duration": 0.65, "notes": [196.0, 130.81], "decay": 2.8, "volume": 0.22, "noise": 0.03},
    "door_unseal": {"duration": 0.8, "notes": [174.61, 130.81], "decay": 2.2, "volume": 0.22, "noise": 0.02},
    "fuse_insert": {"duration": 0.28, "notes": [392.0], "decay": 5.0, "volume": 0.16},
    "power_restore": {"duration": 1.0, "notes": [98.0, 147.0, 220.0], "decay": 1.8, "volume": 0.22, "noise": 0.02},
    "handwheel_crank": {"duration": 0.85, "notes": [164.81, 130.81], "decay": 2.0, "volume": 0.20, "noise": 0.02},
    "lift_token": {"duration": 0.25, "notes": [880.0, 1174.66], "decay": 6.0, "volume": 0.15},
    "lift_lubricate": {"duration": 0.35, "notes": [246.94], "decay": 3.5, "volume": 0.16, "noise": 0.01},
    "lift_travel": {"duration": 1.2, "notes": [98.0, 110.0, 123.47], "decay": 1.6, "volume": 0.18, "noise": 0.02},
    "lens_seat": {"duration": 0.8, "notes": [392.0, 523.25, 659.25], "decay": 2.4, "volume": 0.18},
    "dawn_signal": {"duration": 1.8, "notes": [261.63, 392.0, 523.25, 783.99], "decay": 1.2, "volume": 0.22},
    "failure_click": {"duration": 0.18, "notes": [220.0], "decay": 7.0, "volume": 0.12, "noise": 0.02},
}


def asset_paths(root: Path | str = "assets/audio") -> dict[str, dict[str, Path]]:
    base = Path(root)
    return {
        "music": {name: base / "music" / f"{name}.wav" for name in MUSIC_SPECS},
        "ambient": {name: base / "ambient" / f"{name}.wav" for name in AMBIENT_SPECS},
        "sfx": {name: base / "sfx" / f"{name}.wav" for name in SFX_SPECS},
    }


def ensure_audio_assets(root: Path | str = "assets/audio") -> dict[str, dict[str, Path]]:
    paths = asset_paths(root)
    for group in paths.values():
        for path in group.values():
            path.parent.mkdir(parents=True, exist_ok=True)

    for name, spec in MUSIC_SPECS.items():
        path = paths["music"][name]
        if not path.exists():
            _write_wave(path, _render_music(name, spec))

    for name, spec in AMBIENT_SPECS.items():
        path = paths["ambient"][name]
        if not path.exists():
            _write_wave(path, _render_ambient(name, spec))

    for name, spec in SFX_SPECS.items():
        path = paths["sfx"][name]
        if not path.exists():
            _write_wave(path, _render_sfx(name, spec))

    manifest = {
        "generated": True,
        "generator": "game/audio_assets.py",
        "music": sorted(paths["music"]),
        "ambient": sorted(paths["ambient"]),
        "sfx": sorted(paths["sfx"]),
        "license": "Generated locally for this project; no third-party audio sources used in this initial pass.",
    }
    manifest_path = Path(root) / "ASSET_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return paths


def _seeded_rng(name: str) -> random.Random:
    seed = 0
    for char in name:
        seed = (seed * 131 + ord(char)) % (2**32)
    return random.Random(seed)


def _write_wave(path: Path, samples: list[float]) -> None:
    frames = bytearray()
    for sample in samples:
        clipped = max(-1.0, min(1.0, sample))
        frames.extend(struct.pack("<h", int(clipped * 32767)))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(frames))


def _render_music(name: str, spec: dict) -> list[float]:
    duration = spec["duration"]
    total = int(SAMPLE_RATE * duration)
    pulse = spec["pulse"]
    step = pulse["step"]
    notes = pulse["notes"]
    samples: list[float] = []
    for index in range(total):
        t = index / SAMPLE_RATE
        sample = 0.0
        cycle = (t % duration) / duration
        swell = 0.84 + 0.16 * math.sin(2 * math.pi * cycle)
        for freq, volume in spec["tones"]:
            sample += math.sin(2 * math.pi * freq * t) * volume * swell
        note = notes[int(t / step) % len(notes)]
        phase = (t % step) / step
        envelope = 0.5 * (1.0 + math.cos(2 * math.pi * phase))
        sample += math.sin(2 * math.pi * note * t) * pulse["volume"] * envelope
        sample += math.sin(2 * math.pi * (note / 2.0) * t) * pulse["volume"] * 0.20 * envelope
        sample += math.sin(2 * math.pi * (note * 1.5) * t) * pulse["volume"] * 0.05 * envelope
        sample += _interpolated_noise(f"{name}:air", index, 6000) * spec["noise"]
        samples.append(sample * 0.7)
    return _match_peak(_loop_crossfade(samples, 1.2), 0.26)


def _render_ambient(name: str, spec: dict) -> list[float]:
    duration = DEFAULT_DURATION
    total = int(SAMPLE_RATE * duration)
    rng = _seeded_rng(name)
    drip_events = _event_positions(rng, duration, 4 if spec["drip"] else 0)
    metal_events = _event_positions(rng, duration, 3 if spec["metal"] else 0)
    samples: list[float] = []
    air_state = 0.0
    gust_state = 0.0
    for index in range(total):
        t = index / SAMPLE_RATE
        raw_air = _ambient_air_noise(name, index)
        air_state = air_state * 0.992 + raw_air * 0.008
        sample = air_state * spec["noise"] * 0.9
        if spec["gust"]:
            raw_gust = _ambient_gust_noise(name, index)
            gust_state = gust_state * 0.985 + raw_gust * 0.015
            sample += gust_state * spec["gust"] * _gust_envelope(name, index)
        for freq, volume in spec["drone"]:
            wobble = 1.0 + 0.002 * math.sin(2 * math.pi * 0.07 * t)
            sample += math.sin(2 * math.pi * freq * wobble * t) * volume
        for event_time in drip_events:
            sample += _percussive_hit(t, event_time, 880.0, spec["drip"], decay=18.0)
        for event_time in metal_events:
            sample += _percussive_hit(t, event_time, 520.0, spec["metal"] * 0.7, decay=11.0)
            sample += _percussive_hit(t, event_time, 780.0, spec["metal"] * 0.32, decay=15.0)
        samples.append(sample * 0.82)
    return _match_peak(_loop_crossfade(samples, 0.5), 0.22)


def _render_sfx(name: str, spec: dict) -> list[float]:
    duration = spec["duration"]
    total = int(SAMPLE_RATE * duration)
    notes = spec["notes"]
    noise = spec.get("noise", 0.0)
    samples: list[float] = []
    for index in range(total):
        t = index / SAMPLE_RATE
        decay = math.exp(-spec["decay"] * t)
        sample = 0.0
        for note_index, freq in enumerate(notes):
            delay = note_index * 0.05
            if t >= delay:
                local_t = t - delay
                local_decay = math.exp(-spec["decay"] * local_t)
                sample += math.sin(2 * math.pi * freq * local_t) * spec["volume"] * local_decay
        sample += _noise_value(name, index, window=90) * noise * decay
        samples.append(sample)
    return _match_peak(_fade_edges(samples, 0.02), 0.78)


def _noise_value(name: str, index: int, window: int) -> float:
    bucket = index // max(1, window)
    return _bucket_noise(name, bucket)


@lru_cache(maxsize=None)
def _bucket_noise(name: str, bucket: int) -> float:
    value = 2166136261
    for char in f"{name}:{bucket}":
        value ^= ord(char)
        value = (value * 16777619) % (2**32)
    return (value / (2**32 - 1)) * 2.0 - 1.0


def _interpolated_noise(name: str, index: int, window: int) -> float:
    window = max(1, window)
    left = index // window
    fraction = (index % window) / window
    right = left + 1
    a = _noise_value(name, left * window, window)
    b = _noise_value(name, right * window, window)
    smooth = fraction * fraction * (3.0 - 2.0 * fraction)
    return a * (1.0 - smooth) + b * smooth


def _ambient_air_noise(name: str, index: int) -> float:
    low = _interpolated_noise(f"{name}:air:low", index, 2800)
    mid = _interpolated_noise(f"{name}:air:mid", index, 950)
    soft = _interpolated_noise(f"{name}:air:soft", index, 420)
    return low * 0.62 + mid * 0.28 + soft * 0.10


def _ambient_gust_noise(name: str, index: int) -> float:
    body = _interpolated_noise(f"{name}:gust:body", index, 5200)
    edge = _interpolated_noise(f"{name}:gust:edge", index, 1800)
    return body * 0.78 + edge * 0.22


def _gust_envelope(name: str, index: int) -> float:
    slow = (_interpolated_noise(f"{name}:gust:env", index, 12000) + 1.0) * 0.5
    very_slow = (_interpolated_noise(f"{name}:gust:slow", index, 24000) + 1.0) * 0.5
    return 0.22 + slow * 0.48 + very_slow * 0.18


def _event_positions(rng: random.Random, duration: float, count: int) -> list[float]:
    if count <= 0:
        return []
    positions = sorted(rng.uniform(0.4, max(0.41, duration - 0.4)) for _ in range(count))
    return positions


def _percussive_hit(time_value: float, event_time: float, frequency: float, volume: float, *, decay: float) -> float:
    if volume <= 0.0 or time_value < event_time:
        return 0.0
    local_t = time_value - event_time
    return math.sin(2 * math.pi * frequency * local_t) * volume * math.exp(-decay * local_t)


def _fade_edges(samples: list[float], seconds: float) -> list[float]:
    edge = max(1, int(SAMPLE_RATE * seconds))
    total = len(samples)
    for index in range(min(edge, total // 2)):
        factor = index / edge
        samples[index] *= factor
        samples[total - index - 1] *= factor
    return samples


def _loop_crossfade(samples: list[float], seconds: float) -> list[float]:
    overlap = max(1, int(SAMPLE_RATE * seconds))
    overlap = min(overlap, len(samples) // 3)
    if overlap <= 1:
        return samples
    head = samples[:overlap]
    for index in range(overlap):
        mix = index / (overlap - 1)
        smooth = mix * mix * (3.0 - 2.0 * mix)
        tail_index = len(samples) - overlap + index
        samples[tail_index] = samples[tail_index] * (1.0 - smooth) + head[index] * smooth
    return samples


def _match_peak(samples: list[float], target_peak: float) -> list[float]:
    peak = max(abs(sample) for sample in samples) if samples else 0.0
    if peak <= 0.0:
        return samples
    scale = min(1.0, target_peak / peak)
    return [sample * scale for sample in samples]
