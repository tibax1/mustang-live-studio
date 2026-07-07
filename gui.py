import customtkinter as ctk
from modules.quiz import QuizModule


def start():

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()

    app.title("🐎 Mustang Live Studio")
    app.geometry("1280x720")

    # ===== Bal menü =====
    menu = ctk.CTkFrame(app, width=250, corner_radius=0)
    menu.pack(side="left", fill="y")

    # ===== Fejléc =====
    header = ctk.CTkFrame(app, height=60)
    header.pack(side="top", fill="x")

    # ===== Tartalom =====
    content = ctk.CTkFrame(app)
    content.pack(fill="both", expand=True)

    # ===== Állapotsor =====
    status = ctk.CTkFrame(app, height=30)
    status.pack(side="bottom", fill="x")

    title = ctk.CTkLabel(
        header,
        text="Dashboard",
        font=("Arial", 24, "bold")
    )

    title.pack(pady=12)

    quiz = QuizModule(
        app,
        content,
        title
    )

    def clear():

        for widget in content.winfo_children():
            widget.destroy()

    def dashboard():

        title.configure(text="Dashboard")

        clear()

        ctk.CTkLabel(
            content,
            text="🐎 Mustang Live Studio",
            font=("Arial", 32, "bold")
        ).pack(pady=40)

        ctk.CTkLabel(
            content,
            text="Üdvözöl a Mustang Live Studio!",
            font=("Arial", 20)
        ).pack()

    ctk.CTkLabel(
        menu,
        text="🐎\nMustang\nLive Studio",
        font=("Arial", 28, "bold")
    ).pack(pady=25)

    ctk.CTkButton(
        menu,
        text="🏠 Dashboard",
        command=dashboard,
        height=42
    ).pack(fill="x", padx=15, pady=5)

    ctk.CTkButton(
        menu,
        text="🎮 Quiz",
        command=quiz.start,
        height=42
    ).pack(fill="x", padx=15, pady=5)

    ctk.CTkButton(
        menu,
        text="📺 TikTok Live",
        height=42
    ).pack(fill="x", padx=15, pady=5)

    ctk.CTkButton(
        menu,
        text="🏆 Ranglista",
        height=42
    ).pack(fill="x", padx=15, pady=5)

    ctk.CTkButton(
        menu,
        text="⚙️ Beállítások",
        height=42
    ).pack(fill="x", padx=15, pady=5)

    dashboard()

    ctk.CTkLabel(
        status,
        text="Állapot: Készen áll | Verzió: 0.3",
        font=("Arial", 12)
    ).pack(pady=5)

    app.mainloop()