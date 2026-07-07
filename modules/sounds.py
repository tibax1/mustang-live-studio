from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SOUNDS_DIR = ROOT_DIR / "assets" / "sounds"


class SoundManager:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def play(self, name: str) -> None:
        if not self.enabled:
            return

        sound_file = SOUNDS_DIR / f"{name}.wav"
        if not sound_file.exists():
            return

        if sys.platform.startswith("win"):
            import winsound

            winsound.PlaySound(str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
