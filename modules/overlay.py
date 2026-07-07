from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
OVERLAY_FILE = ROOT_DIR / "data" / "overlay_state.json"


class OverlayManager:
    def __init__(self, path: Path = OVERLAY_FILE) -> None:
        self.path = path
        self.enabled = True

    def publish(self, state: dict[str, Any]) -> None:
        if not self.enabled:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        self.publish(
            {
                "status": "idle",
                "question": None,
                "answers": [],
                "counts": {"A": 0, "B": 0, "C": 0, "D": 0},
                "seconds_left": 0,
                "leaderboard": [],
                "result": None,
            }
        )
