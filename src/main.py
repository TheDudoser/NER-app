from src.windows.main_menu import MainMenu


import customtkinter as ctk

# Настройка темы (до создания окна)
ctk.set_appearance_mode("Dark")


def run_app():
    app = MainMenu()
    app.mainloop()


if __name__ == "__main__":
    run_app()
