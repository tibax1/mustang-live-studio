import customtkinter as ctk


def start():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()

    app.title("🐎 Mustang Live Studio")
    app.geometry("1280x720")

    # Bal oldali menü
    menu = ctk.CTkFrame(app, width=250)
    menu.pack(side="left", fill="y")

    # Jobb oldali tartalom
    content = ctk.CTkFrame(app)
    content.pack(side="right", fill="both", expand=True)

    # Cím
    ctk.CTkLabel(
        menu,
        text="🐎 Mustang\nLive Studio",
        font=("Arial", 28, "bold")
    ).pack(pady=30)

    # Ideiglenes gombok
    ctk.CTkButton(menu, text="🎮 Quiz").pack(fill="x", padx=20, pady=8)
    ctk.CTkButton(menu, text="📺 TikTok Live").pack(fill="x", padx=20, pady=8)
    ctk.CTkButton(menu, text="🏆 Ranglista").pack(fill="x", padx=20, pady=8)
    ctk.CTkButton(menu, text="⚙️ Beállítások").pack(fill="x", padx=20, pady=8)

    # Fő terület
    ctk.CTkLabel(
        content,
        text="Üdvözöl a Mustang Live Studio!",
        font=("Arial", 32, "bold")
    ).pack(pady=100)

    app.mainloop()