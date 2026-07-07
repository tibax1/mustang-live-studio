import customtkinter as ctk


class MustangApp:

    def __init__(self):

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window = ctk.CTk()

        self.window.title("🐎 Mustang Live Studio")
        self.window.geometry("1280x720")

        self.menu = ctk.CTkFrame(self.window, width=250)
        self.menu.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(self.window)
        self.content.pack(side="right", fill="both", expand=True)

    def run(self):
        self.window.mainloop()