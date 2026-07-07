import customtkinter as ctk
import json
import random


class QuizModule:

    def __init__(self, app, content, title_label):

        self.app = app
        self.content = content
        self.title_label = title_label

        self.score = 0
        self.used_questions = []

    def clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def start(self):

        self.title_label.configure(text="🎮 Quiz")

        self.clear()

        with open("data/questions.json", "r", encoding="utf-8") as f:
            questions = json.load(f)

        available = [
            q for q in questions
            if q["kerdes"] not in self.used_questions
        ]

        if len(available) == 0:
            self.game_over()
            return

        question = random.choice(available)

        self.used_questions.append(question["kerdes"])

        ctk.CTkLabel(
            self.content,
            text=f"⭐ Pont: {self.score}",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            self.content,
            text=question["kerdes"],
            font=("Arial", 26, "bold"),
            wraplength=850
        ).pack(pady=30)

        result = ctk.CTkLabel(
            self.content,
            text="",
            font=("Arial", 20, "bold")
        )

        result.pack(pady=15)

        def answer(index):

            if index == question["helyes"]:

                self.score += 1

                result.configure(
                    text="✅ Helyes válasz!",
                    text_color="green"
                )

            else:

                correct = question["valaszok"][question["helyes"]]

                result.configure(
                    text=f"❌ Rossz! Helyes: {correct}",
                    text_color="red"
                )

            self.app.after(
                1500,
                self.start
            )

        for i, valasz in enumerate(question["valaszok"]):

            ctk.CTkButton(
                self.content,
                text=valasz,
                width=420,
                height=45,
                command=lambda x=i: answer(x)
            ).pack(pady=6)

    def game_over(self):

        self.clear()

        self.title_label.configure(text="🏆 Játék vége")

        ctk.CTkLabel(
            self.content,
            text="Minden kérdés elfogyott!",
            font=("Arial", 30, "bold")
        ).pack(pady=40)

        ctk.CTkLabel(
            self.content,
            text=f"Végső pontszám: {self.score}",
            font=("Arial", 24)
        ).pack(pady=20)

        def restart():

            self.score = 0
            self.used_questions.clear()

            self.start()

        ctk.CTkButton(
            self.content,
            text="🔄 Új játék",
            command=restart,
            width=220,
            height=45
        ).pack(pady=30)