from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.audio_assets import ensure_audio_assets


def main() -> None:
    paths = ensure_audio_assets(ROOT / "assets/audio")
    total = sum(len(group) for group in paths.values())
    print(f"Generated {total} audio files under assets/audio.")


if __name__ == "__main__":
    main()
