from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
SCORES_FILE = ROOT_DIR / "data" / "scores.json"


class Leaderboard:
    def __init__(self, path: Path = SCORES_FILE) -> None:
        self.path = path
        self.scores = self.load()

    def load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return {}

        try:
            with self.path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}

        return raw if isinstance(raw, dict) else {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.scores, file, ensure_ascii=False, indent=2)

    def award_round(self, winners: list[str], points: int) -> list[dict[str, Any]]:
        awarded = []
        for username in winners:
            awarded.append(self.add_points(username, points))
        self.save()
        return awarded

    def add_points(self, username: str, points: int) -> dict[str, Any]:
        key = username.strip() or "unknown"
        player = self.scores.setdefault(
            key,
            {
                "name": key,
                "points": 0,
                "correct_answers": 0,
                "rounds": 0,
                "last_seen": "",
            },
        )
        player["points"] = int(player.get("points", 0)) + int(points)
        player["correct_answers"] = int(player.get("correct_answers", 0)) + 1
        player["last_seen"] = datetime.now().isoformat(timespec="seconds")
        return player

    def record_participants(self, usernames: list[str]) -> None:
        for username in usernames:
            key = username.strip() or "unknown"
            player = self.scores.setdefault(
                key,
                {
                    "name": key,
                    "points": 0,
                    "correct_answers": 0,
                    "rounds": 0,
                    "last_seen": "",
                },
            )
            player["rounds"] = int(player.get("rounds", 0)) + 1
            player["last_seen"] = datetime.now().isoformat(timespec="seconds")
        self.save()

    def top(self, limit: int = 10) -> list[dict[str, Any]]:
        return sorted(
            self.scores.values(),
            key=lambda player: int(player.get("points", 0)),
            reverse=True,
        )[:limit]

    def reset(self) -> None:
        self.scores = {}
        self.save()
