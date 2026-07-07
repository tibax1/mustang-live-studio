from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = ROOT_DIR / "data" / "questions.json"
LETTERS = ("A", "B", "C", "D")


@dataclass
class VoteResult:
    accepted: bool
    message: str
    username: str = ""
    answer: str = ""


class GameEngine:
    def __init__(self, round_seconds: int = 30, points_correct: int = 100) -> None:
        self.round_seconds = round_seconds
        self.points_correct = points_correct
        self.questions = self._load_questions()
        self.used_questions: set[str] = set()
        self.current_question: dict[str, Any] | None = None
        self.votes: dict[str, str] = {}
        self.started_at = 0.0
        self.active = False

    def start_round(self) -> dict[str, Any] | None:
        available = [
            question
            for question in self.questions
            if question["kerdes"] not in self.used_questions
        ]
        if not available:
            self.active = False
            self.current_question = None
            return None

        self.current_question = random.choice(available)
        self.used_questions.add(self.current_question["kerdes"])
        self.votes = {}
        self.started_at = monotonic()
        self.active = True
        return self.current_question

    def submit_vote(self, username: str, comment: str) -> VoteResult:
        answer = self._normalize_answer(comment)
        player = username.strip() or "unknown"

        if not self.active:
            return VoteResult(False, "No active vote.", player, answer)
        if self.seconds_left() <= 0:
            self.active = False
            return VoteResult(False, "Voting is already closed.", player, answer)
        if answer not in LETTERS:
            return VoteResult(False, "Comment is not an A/B/C/D vote.", player, answer)
        if player in self.votes:
            return VoteResult(False, "Viewer already voted in this round.", player, answer)

        self.votes[player] = answer
        return VoteResult(True, f"Vote accepted: {answer}", player, answer)

    def finish_round(self) -> dict[str, Any]:
        self.active = False
        counts = {letter: 0 for letter in LETTERS}
        for answer in self.votes.values():
            counts[answer] += 1

        correct_letter = None
        winners: list[str] = []
        if self.current_question:
            correct_letter = LETTERS[int(self.current_question["helyes"])]
            winners = [
                username
                for username, answer in self.votes.items()
                if answer == correct_letter
            ]

        return {
            "question": self.current_question,
            "counts": counts,
            "total_votes": len(self.votes),
            "correct": correct_letter,
            "correct_text": self.correct_answer_text(),
            "winners": winners,
            "points_per_winner": self.points_correct,
        }

    def counts(self) -> dict[str, int]:
        counts = {letter: 0 for letter in LETTERS}
        for answer in self.votes.values():
            counts[answer] += 1
        return counts

    def participants(self) -> list[str]:
        return list(self.votes.keys())

    def correct_answer_text(self) -> str:
        if not self.current_question:
            return ""
        correct_index = int(self.current_question["helyes"])
        return str(self.current_question["valaszok"][correct_index])

    def overlay_question(self) -> dict[str, Any] | None:
        if not self.current_question:
            return None
        return {
            "text": self.current_question["kerdes"],
            "answers": [
                {"letter": letter, "text": self.current_question["valaszok"][index]}
                for index, letter in enumerate(LETTERS)
            ],
        }

    def seconds_left(self) -> int:
        if not self.active:
            return 0
        elapsed = int(monotonic() - self.started_at)
        return max(0, self.round_seconds - elapsed)

    def reset(self) -> None:
        self.used_questions.clear()
        self.current_question = None
        self.votes = {}
        self.active = False

    def _load_questions(self) -> list[dict[str, Any]]:
        if not QUESTIONS_FILE.exists():
            return []

        with QUESTIONS_FILE.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        if not isinstance(raw, list):
            return []
        return [question for question in raw if self._valid_question(question)]

    def _valid_question(self, question: Any) -> bool:
        if not isinstance(question, dict):
            return False
        answers = question.get("valaszok")
        correct = question.get("helyes")
        return (
            isinstance(question.get("kerdes"), str)
            and isinstance(answers, list)
            and len(answers) == 4
            and isinstance(correct, int)
            and 0 <= correct < 4
        )

    def _normalize_answer(self, comment: str) -> str:
        text = comment.strip().upper()
        return text if text in LETTERS else ""
