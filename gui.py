from __future__ import annotations

import queue
from typing import Any

import customtkinter as ctk

from modules.game_engine import GameEngine, LETTERS
from modules.leaderboard import Leaderboard
from modules.overlay import OverlayManager
from modules.settings import SettingsStore
from modules.sounds import SoundManager
from modules.tiktok import TikTokModule


class MustangStudio:
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.settings_store = SettingsStore()
        self.settings = self.settings_store.values
        self.engine = GameEngine(
            round_seconds=int(self.settings["round_seconds"]),
            points_correct=int(self.settings.get("points_correct", 100)),
        )
        self.leaderboard = Leaderboard()
        self.overlay = OverlayManager()
        self.sounds = SoundManager(enabled=True)
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

        self.status = ctk.CTkLabel(self.app, text="Status: keszen all", anchor="w", height=28)
        self.status.pack(side="bottom", fill="x", padx=12)

        self.title = ctk.CTkLabel(self.header, text="Dashboard", font=("Arial", 24, "bold"))
        self.title.pack(pady=12)

        self.vote_labels: dict[str, ctk.CTkLabel] = {}
        self.timer_label: ctk.CTkLabel | None = None
        self.chat_box: ctk.CTkTextbox | None = None
        self.result_box: ctk.CTkTextbox | None = None
        self.live_status_label: ctk.CTkLabel | None = None
        self.quiz_question_label: ctk.CTkLabel | None = None
        self.leaderboard_box: ctk.CTkTextbox | None = None
        self.live_status_text = "Nincs kapcsolat"
        self.current_view = "dashboard"
        self.timer_job: str | None = None

        self._build_menu()
        self.show_dashboard()
        self.overlay.clear()
        self.app.after(150, self._process_live_events)

    def run(self) -> None:
        self.app.mainloop()

    def _build_menu(self) -> None:
        ctk.CTkLabel(self.menu, text="Mustang\nLive Studio", font=("Arial", 28, "bold")).pack(pady=25)

        items = [
            ("Dashboard", self.show_dashboard),
            ("Quiz kezelofelulet", self.show_live_quiz),
            ("Ranglista", self.show_leaderboard),
            ("Overlay / Hang", self.show_overlay_sound),
            ("Beallitasok", self.show_settings),
        ]
        for text, command in items:
            ctk.CTkButton(self.menu, text=text, command=command, height=42).pack(
                fill="x", padx=15, pady=5
            )

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
            self.live_status_label.configure(text=f"Allapot: {message}", text_color=color)

    def show_dashboard(self) -> None:
        self.current_view = "dashboard"
        self.title.configure(text="Dashboard")
        self._clear()

        ctk.CTkLabel(self.content, text="Mustang Live Studio", font=("Arial", 34, "bold")).pack(
            pady=(34, 8)
        )
        ctk.CTkLabel(self.content, text="TikTok Live chat quiz platform", font=("Arial", 18)).pack()

        stats = ctk.CTkFrame(self.content)
        stats.pack(fill="x", padx=28, pady=28)
        self._stat_card(stats, "Kapcsolat", self.live_status_text).pack(
            side="left", fill="x", expand=True, padx=8
        )
        self._stat_card(stats, "Jatekosok", str(len(self.leaderboard.scores))).pack(
            side="left", fill="x", expand=True, padx=8
        )
        self._stat_card(stats, "Kerdesek", str(len(self.engine.questions))).pack(
            side="left", fill="x", expand=True, padx=8
        )
        self._stat_card(stats, "Overlay fajl", str(self.overlay.path)).pack(
            side="left", fill="x", expand=True, padx=8
        )

        ctk.CTkLabel(self.content, text="Top jatekosok", font=("Arial", 20, "bold")).pack(pady=(8, 4))
        ctk.CTkLabel(
            self.content,
            text=self._format_leaderboard() or "Meg nincs pontozott jatekos.",
            font=("Arial", 15),
            justify="left",
        ).pack(pady=6)

    def _stat_card(self, parent: ctk.CTkFrame, title: str, value: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent)
        ctk.CTkLabel(frame, text=title, font=("Arial", 14)).pack(pady=(10, 2))
        ctk.CTkLabel(frame, text=value, font=("Arial", 15, "bold"), wraplength=220).pack(
            padx=12, pady=(0, 10)
        )
        return frame

    def show_live_quiz(self) -> None:
        self.current_view = "live"
        self.title.configure(text="Quiz kezelofelulet")
        self._clear()
        self.vote_labels = {}

        username = self.settings.get("tiktok_username", "")
        top = ctk.CTkFrame(self.content)
        top.pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            top,
            text=f"TikTok fiok: @{username or 'nincs megadva'}",
            font=("Arial", 18, "bold"),
        ).pack(side="left", padx=12, pady=12)

        self.live_status_label = ctk.CTkLabel(top, text="", font=("Arial", 16, "bold"))
        self.live_status_label.pack(side="left", padx=18, pady=12)
        self._set_live_status(self.live_status_text)

        ctk.CTkButton(top, text="Csatlakozas", width=140, command=self.connect_live).pack(
            side="right", padx=8, pady=12
        )
        ctk.CTkButton(top, text="Bontas", width=100, command=self.disconnect_live).pack(
            side="right", padx=8, pady=12
        )

        body = ctk.CTkFrame(self.content)
        body.pack(fill="both", expand=True, padx=18, pady=8)

        left = ctk.CTkFrame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)

        right = ctk.CTkFrame(body, width=380)
        right.pack(side="right", fill="y", padx=(8, 0), pady=8)
        right.pack_propagate(False)

        ctk.CTkLabel(left, text="Elo chat", font=("Arial", 18, "bold")).pack(
            anchor="w", padx=12, pady=(12, 6)
        )
        self.chat_box = ctk.CTkTextbox(left, height=420)
        self.chat_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.chat_box.insert("end", "A live chat uzenetei itt jelennek meg.\n")

        ctk.CTkButton(right, text="Live Quiz inditasa", height=42, command=self.start_vote_round).pack(
            fill="x", padx=12, pady=(12, 10)
        )

        self.timer_label = ctk.CTkLabel(right, text="Ido: --", font=("Arial", 22, "bold"))
        self.timer_label.pack(pady=(4, 10))

        question = self.engine.current_question
        question_text = question["kerdes"] if question else "Nincs aktiv kerdes."
        self.quiz_question_label = ctk.CTkLabel(
            right,
            text=question_text,
            font=("Arial", 18, "bold"),
            wraplength=340,
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
                wraplength=340,
            ).pack(fill="x", padx=12, pady=(4, 0))

        for letter in LETTERS:
            label = ctk.CTkLabel(right, text=f"{letter}: 0", font=("Arial", 22, "bold"), anchor="w")
            label.pack(fill="x", padx=12, pady=3)
            self.vote_labels[letter] = label

        self.result_box = ctk.CTkTextbox(right, height=140)
        self.result_box.pack(fill="x", padx=12, pady=(10, 12))
        self._refresh_vote_labels()
        self._publish_overlay("live")

    def show_leaderboard(self) -> None:
        self.current_view = "leaderboard"
        self.title.configure(text="Ranglista")
        self._clear()

        ctk.CTkLabel(self.content, text="Ranglista", font=("Arial", 28, "bold")).pack(pady=(24, 10))
        self.leaderboard_box = ctk.CTkTextbox(self.content, width=780, height=440)
        self.leaderboard_box.pack(pady=10)
        self._refresh_leaderboard_box()
        ctk.CTkButton(self.content, text="Frissites", width=160, command=self._refresh_leaderboard_box).pack(
            pady=8
        )

    def show_overlay_sound(self) -> None:
        self.current_view = "overlay"
        self.title.configure(text="Overlay / Hang")
        self._clear()

        ctk.CTkLabel(self.content, text="Overlay modul elokeszitve", font=("Arial", 24, "bold")).pack(
            pady=(30, 8)
        )
        ctk.CTkLabel(
            self.content,
            text=f"Overlay allapotfajl: {self.overlay.path}",
            font=("Arial", 15),
            wraplength=840,
        ).pack(pady=6)
        ctk.CTkLabel(
            self.content,
            text="Hangok: assets/sounds/start.wav, vote.wav, finish.wav",
            font=("Arial", 15),
        ).pack(pady=6)

        overlay_var = ctk.BooleanVar(value=self.overlay.enabled)
        sound_var = ctk.BooleanVar(value=self.sounds.enabled)

        def apply_options() -> None:
            self.overlay.enabled = bool(overlay_var.get())
            self.sounds.enabled = bool(sound_var.get())
            self._publish_overlay("settings")
            self._set_status("Overlay es hang beallitasok frissitve")

        ctk.CTkCheckBox(self.content, text="Overlay frissites engedelyezve", variable=overlay_var).pack(
            pady=8
        )
        ctk.CTkCheckBox(self.content, text="Hangjelzesek engedelyezve", variable=sound_var).pack(pady=8)
        ctk.CTkButton(self.content, text="Alkalmaz", command=apply_options, width=160).pack(pady=14)
        ctk.CTkButton(self.content, text="Teszt hang", command=lambda: self.sounds.play("vote"), width=160).pack(
            pady=4
        )

    def show_settings(self) -> None:
        self.current_view = "settings"
        self.title.configure(text="Beallitasok")
        self._clear()

        username_var = ctk.StringVar(value=str(self.settings.get("tiktok_username", "")))
        seconds_var = ctk.StringVar(value=str(self.settings.get("round_seconds", 30)))
        points_var = ctk.StringVar(value=str(self.settings.get("points_correct", 100)))

        ctk.CTkLabel(self.content, text="TikTok felhasznalonev", font=("Arial", 16)).pack(pady=(24, 4))
        ctk.CTkEntry(self.content, textvariable=username_var, width=320).pack(pady=4)

        ctk.CTkLabel(self.content, text="Kor hossza masodpercben", font=("Arial", 16)).pack(pady=(16, 4))
        ctk.CTkEntry(self.content, textvariable=seconds_var, width=120).pack(pady=4)

        ctk.CTkLabel(self.content, text="Pont helyes valaszonkent", font=("Arial", 16)).pack(pady=(16, 4))
        ctk.CTkEntry(self.content, textvariable=points_var, width=120).pack(pady=4)

        settings_status = ctk.CTkLabel(
            self.content,
            text=f"Kapcsolat: {self.live_status_text}",
            font=("Arial", 15, "bold"),
        )
        settings_status.pack(pady=(14, 2))

        def save() -> bool:
            try:
                round_seconds = int(seconds_var.get() or 30)
                points_correct = int(points_var.get() or 100)
            except ValueError:
                self._set_status("A kor hossza es a pontszam csak szam lehet")
                return False
            values = {
                "tiktok_username": username_var.get().strip().lstrip("@"),
                "round_seconds": round_seconds,
                "points_correct": points_correct,
            }
            self.settings = self.settings_store.save(values)
            self.engine.round_seconds = int(self.settings["round_seconds"])
            self.engine.points_correct = int(self.settings["points_correct"])
            self._set_status("Beallitasok mentve")
            return True

        def save_and_connect() -> None:
            if save():
                self.connect_live()
            settings_status.configure(text=f"Kapcsolat: {self.live_status_text}")

        ctk.CTkButton(self.content, text="Mentes", command=save, width=160).pack(pady=(18, 6))
        ctk.CTkButton(self.content, text="Csatlakozas", command=save_and_connect, width=160).pack(pady=6)

    def connect_live(self) -> None:
        username = str(self.settings.get("tiktok_username", "")).strip().lstrip("@")
        if not username:
            self._set_status("Add meg a TikTok felhasznalonevet")
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
        self._set_live_status("Kapcsolodas...")

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
        self.engine.points_correct = int(self.settings.get("points_correct", 100))
        question = self.engine.start_round()
        if question is None:
            self.engine.reset()
            question = self.engine.start_round()

        if question is None:
            self._set_status("Nincs elerheto kerdes")
            return

        if self.current_view != "live":
            self.show_live_quiz()
        elif self.quiz_question_label:
            self.quiz_question_label.configure(text=question["kerdes"])

        if self.result_box:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("end", "Szavazas elindult. A chatben A/B/C/D valaszokat fogadok.\n")
        self._refresh_vote_labels()
        self._publish_overlay("voting")
        self.sounds.play("start")
        self._set_status("Szavazas nyitva")
        self._tick_timer()

    def _tick_timer(self) -> None:
        if self.timer_label:
            self.timer_label.configure(text=f"Ido: {self.engine.seconds_left()}s")
        self._publish_overlay("voting")
        if self.engine.active and self.engine.seconds_left() > 0:
            self.timer_job = self.app.after(1000, self._tick_timer)
            return
        if self.engine.active:
            self._finish_vote_round()
        self.timer_job = None

    def _finish_vote_round(self) -> None:
        result = self.engine.finish_round()
        self.leaderboard.record_participants(self.engine.participants())
        self.leaderboard.award_round(result["winners"], int(result["points_per_winner"]))
        self._refresh_vote_labels(result["counts"])

        counts = result["counts"]
        winners = ", ".join(result["winners"]) if result["winners"] else "nincs"
        message = (
            "Kor vege.\n"
            f"Helyes valasz: {result['correct']} - {result['correct_text']}\n"
            f"Szavazatok: A: {counts['A']} | B: {counts['B']} | C: {counts['C']} | D: {counts['D']}\n"
            f"Osszesen: {result['total_votes']}\n"
            f"Pont/jatekos: {result['points_per_winner']}\n"
            f"Nyertesek: {winners}\n"
        )
        if self.result_box:
            self.result_box.insert("end", message)
        self._publish_overlay("result", result)
        self.sounds.play("finish")
        self._set_status("Szavazas lezarva")

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
                    self._publish_overlay("voting")
                    self.sounds.play("vote")
                if self.chat_box:
                    self.chat_box.insert("end", f"[szavazat] {username}: {answer} ({result.message})\n")
                    self.chat_box.see("end")
        self.app.after(150, self._process_live_events)

    def _refresh_vote_labels(self, counts: dict[str, int] | None = None) -> None:
        if counts is None:
            counts = self.engine.counts()
        for letter, label in self.vote_labels.items():
            label.configure(text=f"{letter}: {counts.get(letter, 0)}")

    def _refresh_leaderboard_box(self) -> None:
        if not self.leaderboard_box:
            return
        self.leaderboard_box.delete("1.0", "end")
        self.leaderboard_box.insert("end", self._format_leaderboard(limit=20) or "Meg nincs mentett eredmeny.\n")

    def _format_leaderboard(self, limit: int = 5) -> str:
        rows = []
        for index, player in enumerate(self.leaderboard.top(limit), start=1):
            rows.append(
                f"{index}. {player.get('name', 'unknown')} - "
                f"{player.get('points', 0)} pont "
                f"({player.get('correct_answers', 0)} helyes)"
            )
        return "\n".join(rows)

    def _publish_overlay(self, status: str, result: dict[str, Any] | None = None) -> None:
        self.overlay.publish(
            {
                "status": status,
                "question": self.engine.overlay_question(),
                "counts": self.engine.counts(),
                "seconds_left": self.engine.seconds_left(),
                "leaderboard": self.leaderboard.top(5),
                "result": result,
            }
        )


def start() -> None:
    MustangStudio().run()
