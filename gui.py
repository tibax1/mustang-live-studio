import customtkinter as ctk


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

    ctk.CTkLabel(
        menu,
        text="🐎\nMustang\nLive Studio",
        font=("Arial", 28, "bold")
    ).pack(pady=25)

    gombok = [
        "🏠 Dashboard",
        "🎮 Quiz",
        "📺 TikTok Live",
        "🏆 Ranglista",
        "⚙️ Beállítások"
    ]

    for gomb in gombok:
        ctk.CTkButton(
            menu,
            text=gomb,
            height=42
        ).pack(fill="x", padx=15, pady=5)

    ctk.CTkLabel(
        header,
        text="Dashboard",
        font=("Arial",24,"bold")
    ).pack(pady=12)

    ctk.CTkLabel(
        content,
        text="Üdvözöl a Mustang Live Studio!",
        font=("Arial",32,"bold")
    ).pack(pady=40)

    ctk.CTkLabel(
        content,
        text="Ez lesz a központi vezérlőpult.",
        font=("Arial",18)
    ).pack()

    ctk.CTkLabel(
        status,
        text="Állapot: Készen áll | Verzió: 0.2",
        font=("Arial",12)
    ).pack(pady=5)

    app.mainloop()