import customtkinter as ct


class ErrorDialog(ct.CTkToplevel):
    def __init__(self, parent, title="Ошибка", message="Произошла ошибка"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)  # Делаем окно модальным

        # Центрирование относительно родительского окна
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 75
        self.geometry(f"+{x}+{y}")

        # Контент
        self.message_label = ct.CTkLabel(
            self,
            text=message,
            font=("Arial", 14),
            wraplength=380
        )
        self.message_label.pack(pady=20, padx=10)

        ok_btn = ct.CTkButton(
            self,
            text="OK",
            command=self.destroy,
            width=100
        )
        ok_btn.pack(pady=10)

        self.grab_set()  # Блокируем взаимодействие с родительским окном
