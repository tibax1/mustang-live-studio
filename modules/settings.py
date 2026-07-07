from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT_DIR / "data" / "settings.json"


DEFAULT_SETTINGS: dict[str, Any] = {
    "tiktok_username": "",
    "round_seconds": 30,
    "points_correct": 100,
}


class SettingsStore:
    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self.path = path
        self.values = self.load()

    def load(self) -> dict[str, Any]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return DEFAULT_SETTINGS.copy()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError):
            raw = {}

        settings = DEFAULT_SETTINGS.copy()
        if isinstance(raw, dict):
            settings.update({key: raw[key] for key in settings if key in raw})
        settings["round_seconds"] = max(5, int(settings["round_seconds"]))
        settings["points_correct"] = max(1, int(settings["points_correct"]))
        return settings

    def save(self, values: dict[str, Any]) -> dict[str, Any]:
        self.values.update({key: values[key] for key in DEFAULT_SETTINGS if key in values})
        self.values["round_seconds"] = max(5, int(self.values["round_seconds"]))
        self.values["points_correct"] = max(1, int(self.values["points_correct"]))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.values, file, ensure_ascii=False, indent=2)
        return self.values
