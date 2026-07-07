from __future__ import annotations

import queue
from typing import Any

import customtkinter as ctk

from modules.game_engine import GameEngine, LETTERS
from modules.settings import SettingsStore
from modules.tiktok import TikTokModule


class MustangStudio:
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.settings_store = SettingsStore()
        self.settings = self.settings_store.values
        self.engine = GameEngine(round_seconds=int(self.settings["round_seconds"]))
        self.live: TikTokModule | None = None
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()

        self.app = ctk.CTk()
        self.app.title("Mustang Live Studio")
        self.app.geometry("1280x720")

        self.menu = ctk.CTkFrame(self.app, width=250, corner_radius=0)
        self.menu.pack(side="left", fill="y")

        self.header = ctk.CTkFrame(self.app, height=60)
        self.header.pack(side="top", fill="x")

        self.content = ctk.CTkFrame(self.app)
        self.content.pack(fill="both", expand=True)

        self.status = ctk.CTkLabel(
            self.app,
            text="Status: Ready",
            anchor="w",
            height=28,
        )
        self.status.pack(side="bottom", fill="x", padx=12)

        self.title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=("Arial", 24, "bold"),
        )
        self.title.pack(pady=12)

        self.vote_labels: dict[str, ctk.CTkLabel] = {}
        self.timer_label: ctk.CTkLabel | None = None
        self.chat_box: ctk.CTkTextbox | None = None
        self.result_box: ctk.CTkTextbox | None = None

        self._build_menu()
        self.show_dashboard()
        self.app.after(150, self._process_live_events)

    def run(self) -> None:
        self.app.mainloop()

    def _build_menu(self) -> None:
        ctk.CTkLabel(
            self.menu,
            text="Mustang\nLive Studio",
            font=("Arial", 28, "bold"),
        ).pack(pady=25)

        items = [
            ("Dashboard", self.show_dashboard),
            ("TikTok Live", self.show_live),
            ("Chat Quiz", self.show_quiz),
            ("Settings", self.show_settings),
        ]
        for text, command in items:
            ctk.CTkButton(
                self.menu,
                text=text,
                command=command,
                height=42,
            ).pack(fill="x", padx=15, pady=5)

    def _clear(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _set_status(self, message: str) -> None:
        self.status.configure(text=f"Status: {message}")

    def show_dashboard(self) -> None:
        self.title.configure(text="Dashboard")
        self._clear()
        ctk.CTkLabel(
            self.content,
            text="Mustang Live Studio",
            font=("Arial", 34, "bold"),
        ).pack(pady=(50, 12))
        ctk.CTkLabel(
            self.content,
            text="TikTok Live chat quiz platform",
            font=("Arial", 18),
        ).pack()

    def show_live(self) -> None:
        self.title.configure(text="TikTok Live")
        self._clear()

        username = self.settings.get("tiktok_username", "")
        ctk.CTkLabel(
            self.content,
            text=f"Configured account: @{username or 'not set'}",
            font=("Arial", 20, "bold"),
        ).pack(pady=16)

        ctk.CTkButton(
            self.content,
            text="Connect",
            width=180,
            command=self.connect_live,
        ).pack(pady=6)
        ctk.CTkButton(
            self.content,
            text="Disconnect",
            width=180,
            command=self.disconnect_live,
        ).pack(pady=6)

        self.chat_box = ctk.CTkTextbox(self.content, width=820, height=390)
        self.chat_box.pack(pady=18)
        self.chat_box.insert("end", "Live comments will appear here.\n")

    def show_quiz(self) -> None:
        self.title.configure(text="Chat Quiz")
        self._clear()
        self.vote_labels = {}

        self.timer_label = ctk.CTkLabel(
            self.content,
            text="Timer: --",
            font=("Arial", 22, "bold"),
        )
        self.timer_label.pack(pady=(18, 8))

        question = self.engine.current_question
        question_text = question["kerdes"] if question else "No active question."
        ctk.CTkLabel(
            self.content,
            text=question_text,
            font=("Arial", 26, "bold"),
            wraplength=850,
        ).pack(pady=16)

        for letter in LETTERS:
            label = ctk.CTkLabel(
                self.content,
                text=f"{letter}: 0 votes",
                font=("Arial", 18),
            )
            label.pack(pady=4)
            self.vote_labels[letter] = label

        ctk.CTkButton(
            self.content,
            text="Start 30s Vote",
            width=180,
            command=self.start_vote_round,
        ).pack(pady=16)

        self.result_box = ctk.CTkTextbox(self.content, width=820, height=160)
        self.result_box.pack(pady=8)

    def show_settings(self) -> None:
        self.title.configure(text="Settings")
        self._clear()

        username_var = ctk.StringVar(value=str(self.settings.get("tiktok_username", "")))
        seconds_var = ctk.StringVar(value=str(self.settings.get("round_seconds", 30)))

        ctk.CTkLabel(self.content, text="TikTok username", font=("Arial", 16)).pack(pady=(24, 4))
        username_entry = ctk.CTkEntry(self.content, textvariable=username_var, width=320)
        username_entry.pack(pady=4)

        ctk.CTkLabel(self.content, text="Round seconds", font=("Arial", 16)).pack(pady=(16, 4))
        seconds_entry = ctk.CTkEntry(self.content, textvariable=seconds_var, width=120)
        seconds_entry.pack(pady=4)

        def save() -> None:
            values = {
                "tiktok_username": username_var.get().strip().lstrip("@"),
                "round_seconds": int(seconds_var.get() or 30),
            }
            self.settings = self.settings_store.save(values)
            self.engine.round_seconds = int(self.settings["round_seconds"])
            self._set_status("Settings saved")

        ctk.CTkButton(self.content, text="Save", command=save, width=160).pack(pady=18)

    def connect_live(self) -> None:
        username = str(self.settings.get("tiktok_username", "")).strip().lstrip("@")
        if not username:
            self._set_status("Set a TikTok username first")
            return

        if self.live:
            self.live.stop()

        self.live = TikTokModule(
            username=username,
            on_comment=lambda user, comment: self.events.put(("comment", (user, comment))),
            on_vote=lambda user, answer: self.events.put(("vote", (user, answer))),
            on_status=lambda message: self.events.put(("status", message)),
        )
        self.live.start()

    def disconnect_live(self) -> None:
        if self.live:
            self.live.stop()
            self.live = None
        self._set_status("Disconnected")

    def start_vote_round(self) -> None:
        self.engine.round_seconds = int(self.settings.get("round_seconds", 30))
        question = self.engine.start_round()
        if question is None:
            self.engine.reset()
            question = self.engine.start_round()

        self.show_quiz()
        self._set_status("Voting is open")
        self._tick_timer()

    def _tick_timer(self) -> None:
        if self.timer_label:
            self.timer_label.configure(text=f"Timer: {self.engine.seconds_left()}s")
        if self.engine.active and self.engine.seconds_left() > 0:
            self.app.after(1000, self._tick_timer)
            return
        if self.engine.active:
            self._finish_vote_round()

    def _finish_vote_round(self) -> None:
        result = self.engine.finish_round()
        self._refresh_vote_labels(result["counts"])
        winners = ", ".join(result["winners"]) if result["winners"] else "none"
        message = (
            f"Voting closed.\n"
            f"Total votes: {result['total_votes']}\n"
            f"Correct answer: {result['correct']}\n"
            f"Winners: {winners}\n"
        )
        if self.result_box:
            self.result_box.insert("end", message)
        self._set_status("Voting closed")

    def _process_live_events(self) -> None:
        while not self.events.empty():
            event_type, payload = self.events.get()
            if event_type == "status":
                self._set_status(str(payload))
            elif event_type == "comment":
                username, comment = payload
                if self.chat_box:
                    self.chat_box.insert("end", f"{username}: {comment}\n")
                    self.chat_box.see("end")
            elif event_type == "vote":
                username, answer = payload
                result = self.engine.submit_vote(username, answer)
                if result.accepted:
                    self._refresh_vote_labels()
                if self.chat_box:
                    self.chat_box.insert("end", f"[vote] {username}: {answer} ({result.message})\n")
                    self.chat_box.see("end")
        self.app.after(150, self._process_live_events)

    def _refresh_vote_labels(self, counts: dict[str, int] | None = None) -> None:
        if counts is None:
            counts = {letter: 0 for letter in LETTERS}
            for answer in self.engine.votes.values():
                counts[answer] += 1
        for letter, label in self.vote_labels.items():
            label.configure(text=f"{letter}: {counts.get(letter, 0)} votes")


def start() -> None:
    MustangStudio().run()
