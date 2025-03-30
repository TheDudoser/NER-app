import customtkinter
from .add_text_window import AddTextWindow
from .text_work_window import TextWorkWindow


class MainMenu(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("NER APP - Главное меню")
        self.geometry("800x300")
        self.resizable(False, False)  # Запрещаем изменение размера

        # Создаем интерфейс
        self.create_widgets()

        # Центрируем после создания виджетов
        self.after(100, self.center_window)

    def center_window(self):
        """Центрирует главное окно на экране."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 3.5

        self.geometry(f"+{x}+{y}")

    def create_widgets(self):
        self.main_container = customtkinter.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        label_title = customtkinter.CTkLabel(
            self.main_container,
            text="Главное меню",
            font=("Arial", 24, "bold")
        )
        label_title.pack(pady=(20, 0))

        button_frame = customtkinter.CTkFrame(self.main_container)
        button_frame.pack(pady=20, padx=20, fill="both", expand=True)

        add_text_button = customtkinter.CTkButton(
            button_frame,
            text="Разметить новый текст",
            font=("Arial", 16),
            height=50,
            command=self.open_add_text_window
        )
        add_text_button.pack(pady=10, fill="x")

        text_work_button = customtkinter.CTkButton(
            button_frame,
            text="Перейти к размеченным текстам",
            font=("Arial", 16),
            height=50,
            command=self.open_text_work_window
        )
        text_work_button.pack(pady=10, fill="x")

    def open_add_text_window(self):
        self.withdraw()
        AddTextWindow(self).grab_set()

    def open_text_work_window(self):
        self.withdraw()
        TextWorkWindow(self).grab_set()
