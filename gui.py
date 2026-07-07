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
        self.live_status_label: ctk.CTkLabel | None = None
        self.quiz_question_label: ctk.CTkLabel | None = None
        self.live_status_text = "Nincs kapcsolat"
        self.current_view = "dashboard"
        self.timer_job: str | None = None

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
            ("Live Quiz", self.show_live),
            ("Beállítások", self.show_settings),
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

    def _set_live_status(self, message: str) -> None:
        self.live_status_text = message
        self._set_status(message)
        if self.live_status_label:
            color = "#22c55e" if message == "Csatlakozva" else "#f97316"
            self.live_status_label.configure(text=f"Állapot: {message}", text_color=color)

    def show_dashboard(self) -> None:
        self.current_view = "dashboard"
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
        self.current_view = "live"
        self.title.configure(text="Live Quiz")
        self._clear()
        self.vote_labels = {}

        username = self.settings.get("tiktok_username", "")
        top = ctk.CTkFrame(self.content)
        top.pack(fill="x", padx=18, pady=(16, 8))

        account = ctk.CTkLabel(
            top,
            text=f"TikTok fiók: @{username or 'nincs megadva'}",
            font=("Arial", 18, "bold"),
        )
        account.pack(side="left", padx=12, pady=12)

        self.live_status_label = ctk.CTkLabel(
            top,
            text=f"Állapot: {self.live_status_text}",
            font=("Arial", 16, "bold"),
        )
        self.live_status_label.pack(side="left", padx=18, pady=12)
        self._set_live_status(self.live_status_text)

        ctk.CTkButton(
            top,
            text="Csatlakozás",
            width=140,
            command=self.connect_live,
        ).pack(side="right", padx=8, pady=12)
        ctk.CTkButton(
            top,
            text="Bontás",
            width=100,
            command=self.disconnect_live,
        ).pack(side="right", padx=8, pady=12)

        body = ctk.CTkFrame(self.content)
        body.pack(fill="both", expand=True, padx=18, pady=8)

        left = ctk.CTkFrame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)

        right = ctk.CTkFrame(body, width=360)
        right.pack(side="right", fill="y", padx=(8, 0), pady=8)
        right.pack_propagate(False)

        ctk.CTkLabel(left, text="Live Chat", font=("Arial", 18, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
        self.chat_box = ctk.CTkTextbox(left, height=420)
        self.chat_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.chat_box.insert("end", "A live chat üzenetei itt jelennek meg.\n")

        ctk.CTkButton(
            right,
            text="Live Quiz indítása",
            height=42,
            command=self.start_vote_round,
        ).pack(fill="x", padx=12, pady=(12, 10))

        self.timer_label = ctk.CTkLabel(
            right,
            text="Idő: --",
            font=("Arial", 22, "bold"),
        )
        self.timer_label.pack(pady=(4, 10))

        question = self.engine.current_question
        question_text = question["kerdes"] if question else "Nincs aktív kérdés."
        self.quiz_question_label = ctk.CTkLabel(
            right,
            text=question_text,
            font=("Arial", 18, "bold"),
            wraplength=320,
            justify="left",
        )
        self.quiz_question_label.pack(fill="x", padx=12, pady=8)

        answers = question["valaszok"] if question else ["-", "-", "-", "-"]
        for index, letter in enumerate(LETTERS):
            ctk.CTkLabel(
                right,
                text=f"{letter}: {answers[index]}",
                font=("Arial", 14),
                anchor="w",
                wraplength=320,
            ).pack(fill="x", padx=12, pady=(4, 0))

        for letter in LETTERS:
            label = ctk.CTkLabel(
                right,
                text=f"{letter}: 0",
                font=("Arial", 22, "bold"),
                anchor="w",
            )
            label.pack(fill="x", padx=12, pady=3)
            self.vote_labels[letter] = label

        self.result_box = ctk.CTkTextbox(right, height=150)
        self.result_box.pack(fill="x", padx=12, pady=(10, 12))
        self._refresh_vote_labels()

    def show_settings(self) -> None:
        self.current_view = "settings"
        self.title.configure(text="Beállítások")
        self._clear()

        username_var = ctk.StringVar(value=str(self.settings.get("tiktok_username", "")))
        seconds_var = ctk.StringVar(value=str(self.settings.get("round_seconds", 30)))

        ctk.CTkLabel(self.content, text="TikTok felhasználónév", font=("Arial", 16)).pack(pady=(24, 4))
        username_entry = ctk.CTkEntry(self.content, textvariable=username_var, width=320)
        username_entry.pack(pady=4)

        ctk.CTkLabel(self.content, text="Kör hossza másodpercben", font=("Arial", 16)).pack(pady=(16, 4))
        seconds_entry = ctk.CTkEntry(self.content, textvariable=seconds_var, width=120)
        seconds_entry.pack(pady=4)

        settings_status = ctk.CTkLabel(
            self.content,
            text=f"Kapcsolat: {self.live_status_text}",
            font=("Arial", 15, "bold"),
        )
        settings_status.pack(pady=(14, 2))

        def save() -> bool:
            try:
                round_seconds = int(seconds_var.get() or 30)
            except ValueError:
                self._set_status("A kör hossza csak szám lehet")
                return False
            values = {
                "tiktok_username": username_var.get().strip().lstrip("@"),
                "round_seconds": round_seconds,
            }
            self.settings = self.settings_store.save(values)
            self.engine.round_seconds = int(self.settings["round_seconds"])
            self._set_status("Beállítások mentve")
            return True

        def save_and_connect() -> None:
            if save():
                self.connect_live()
            settings_status.configure(text=f"Kapcsolat: {self.live_status_text}")

        ctk.CTkButton(self.content, text="Mentés", command=save, width=160).pack(pady=(18, 6))
        ctk.CTkButton(self.content, text="Csatlakozás", command=save_and_connect, width=160).pack(pady=6)

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
        self._set_live_status("Nincs kapcsolat")

    def start_vote_round(self) -> None:
        if self.timer_job:
            self.app.after_cancel(self.timer_job)
            self.timer_job = None
        self.engine.round_seconds = int(self.settings.get("round_seconds", 30))
        question = self.engine.start_round()
        if question is None:
            self.engine.reset()
            question = self.engine.start_round()

        if question is None:
            self._set_status("Nincs elérhető kérdés")
            return

        if self.current_view != "live":
            self.show_live()
        elif self.quiz_question_label:
            self.quiz_question_label.configure(text=question["kerdes"])

        if self.result_box:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("end", "Szavazás elindult. A chatben A/B/C/D válaszokat fogadok.\n")
        self._refresh_vote_labels()
        self._set_status("Szavazás nyitva")
        self._tick_timer()

    def _tick_timer(self) -> None:
        if self.timer_label:
            self.timer_label.configure(text=f"Idő: {self.engine.seconds_left()}s")
        if self.engine.active and self.engine.seconds_left() > 0:
            self.timer_job = self.app.after(1000, self._tick_timer)
            return
        if self.engine.active:
            self._finish_vote_round()
        self.timer_job = None

    def _finish_vote_round(self) -> None:
        result = self.engine.finish_round()
        self._refresh_vote_labels(result["counts"])
        counts = result["counts"]
        message = (
            "Kör vége.\n"
            f"Helyes válasz: {result['correct']}\n"
            f"Szavazatok: A: {counts['A']} | B: {counts['B']} | C: {counts['C']} | D: {counts['D']}\n"
            f"Összesen: {result['total_votes']}\n"
        )
        if self.result_box:
            self.result_box.insert("end", message)
        self._set_status("Szavazás lezárva")

    def _process_live_events(self) -> None:
        while not self.events.empty():
            event_type, payload = self.events.get()
            if event_type == "status":
                status = str(payload)
                if status.startswith("Connected"):
                    status = "Csatlakozva"
                elif status.startswith("Disconnected") or status.startswith("Nincs kapcsolat"):
                    status = "Nincs kapcsolat"
                self._set_live_status(status)
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
                    self.chat_box.insert("end", f"[szavazat] {username}: {answer} ({result.message})\n")
                    self.chat_box.see("end")
        self.app.after(150, self._process_live_events)

    def _refresh_vote_labels(self, counts: dict[str, int] | None = None) -> None:
        if counts is None:
            counts = {letter: 0 for letter in LETTERS}
            for answer in self.engine.votes.values():
                counts[answer] += 1
        for letter, label in self.vote_labels.items():
            label.configure(text=f"{letter}: {counts.get(letter, 0)}")


def start() -> None:
    MustangStudio().run()
