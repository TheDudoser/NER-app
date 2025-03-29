import customtkinter
from tkinter import filedialog
import threading
import time

# System settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


class BaseWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, title, width=800, height=600):
        super().__init__(parent)
        self.geometry(f"{width}x{height}")
        self.raw_title = title
        self.title(f"NER APP - {title}")
        self.parent = parent

        self.center_window()

    def center_window(self):
        """
        Центрирует окно относительно родительского окна.
        """
        self.update_idletasks()  # Обновить геометрию окна
        parent_width = self.parent.winfo_width()  # Ширина родительского окна
        parent_height = self.parent.winfo_height()  # Высота родительского окна
        parent_x = self.parent.winfo_x()  # Позиция X родительского окна
        parent_y = self.parent.winfo_y()  # Позиция Y родительского окна

        # Вычисляем позицию для нового окна
        window_width = self.winfo_width()  # Ширина нового окна
        window_height = self.winfo_height()  # Высота нового окна
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        # Устанавливаем позицию нового окна
        self.geometry(f"+{x}+{y}")

    def render_go_back_button(self):
        # Кнопка "Назад" в виде стрелочки
        self.back_button = customtkinter.CTkButton(
            self,
            text="← Назад",
            width=30,
            height=30,
            command=self.go_back,
            fg_color="transparent",  # Прозрачный фон
            corner_radius=15,  # Закругленные углы
        )
        self.back_button.place(x=10, y=10)

    def go_back(self):
        self.destroy()  # Закрыть текущее окно
        self.parent.deiconify()  # Показать родительское окно


class MainMenu(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("NER APP - Главное меню")

        # Центрируем окно при создании
        self.center_window()

        # Создаем главный контейнер для элементов
        self.main_container = customtkinter.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок главного меню
        label_title = customtkinter.CTkLabel(
            self.main_container,
            text="Главное меню",
            font=("Arial", 24, "bold")  # Увеличиваем шрифт и делаем его жирным
        )
        label_title.pack(pady=(20, 40))  # Отступ сверху и снизу

        # Создаем контейнер для кнопок
        button_frame = customtkinter.CTkFrame(self.main_container)
        button_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Кнопка "Разметить новый текст"
        add_text_button = customtkinter.CTkButton(
            button_frame,
            text="Разметить новый текст",
            font=("Arial", 16),
            height=50,  # Увеличиваем высоту кнопки
            command=self.open_add_text_window
        )
        add_text_button.pack(pady=10, fill="x")  # Растягиваем кнопку по ширине

        # Кнопка "Перейти к размеченным текстам"
        text_work_button = customtkinter.CTkButton(
            button_frame,
            text="Перейти к размеченным текстам",
            font=("Arial", 16),
            height=50,
            command=self.open_text_work_window
        )
        text_work_button.pack(pady=10, fill="x")

        # Кнопка "Выход"
        exit_button = customtkinter.CTkButton(
            button_frame,
            text="Выход",
            font=("Arial", 16),
            height=50,
            fg_color="#d9534f",  # Красный цвет для кнопки выхода
            hover_color="#c9302c",  # Темно-красный при наведении
            command=self.destroy  # Закрыть приложение
        )
        exit_button.pack(pady=10, fill="x")

    def center_window(self):
        """
        Центрирует окно на экране.
        """
        self.update_idletasks()  # Обновить геометрию окна

        # Получаем размеры экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Получаем размеры окна
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # Вычисляем позицию для центрирования окна
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Устанавливаем позицию окна
        self.geometry(f"+{x}+{y}")

    def open_add_text_window(self):
        self.withdraw()  # Скрыть главное меню
        add_text_window = AddTextWindow(self)  # Открыть окно добавления текста
        add_text_window.grab_set()  # Установить фокус на новое окно

    def open_text_work_window(self):
        self.withdraw()  # Скрыть главное меню
        text_work_window = TextWorkWindow(self)  # Открыть окно работы с текстами
        text_work_window.grab_set()  # Установить фокус на новое окно


class AddTextWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Разметка нового текста", width=900, height=500)

        self.render_text_input_and_process_btn()
        self.render_loading_indicator()
        self.render_go_back_button()

    def render_text_input_and_process_btn(self):
        # Создаем рамку для текстового поля
        text_frame = customtkinter.CTkFrame(self)
        text_frame.pack(pady=20, padx=20, fill="both", expand=False)

        # Заголовок для текстового поля
        text_label = customtkinter.CTkLabel(text_frame, text="Введите текст для разметки:", font=("Arial", 14))
        text_label.pack(pady=10)

        # Текстовое поле для ввода текста
        self.text_input = customtkinter.CTkTextbox(text_frame, font=("Arial", 12), wrap="word", height=200)
        self.text_input.pack(pady=10, padx=10, fill="both", expand=False)

        # Кнопка для очистки текстового поля
        self.clear_button = customtkinter.CTkButton(text_frame, text="Очистить", command=self.clear_text_input)
        self.clear_button.pack(pady=10)

        # Кнопка для запуска процесса разметки
        self.process_button = customtkinter.CTkButton(text_frame, text="Начать разметку", command=self.start_processing)
        self.process_button.pack(pady=20)

    def render_loading_indicator(self):
        # Индикатор загрузки
        self.loading_indicator = customtkinter.CTkProgressBar(self, mode="determinate")
        self.loading_indicator.pack(pady=10, padx=20, fill="x")
        self.loading_indicator.stop()  # Изначально скрыт

    def clear_text_input(self):
        # Очистка текстового поля
        self.text_input.delete("1.0", "end")

    def upload_file(self):
        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_input.delete("1.0", "end")
                    self.text_input.insert("1.0", content)
            except Exception as e:
                print(f"Ошибка при загрузке файла: {e}")

    def start_processing(self):
        # Запуск процесса разметки в отдельном потоке
        self.loading_indicator.start()  # Показываем индикатор загрузки
        # Блокируем элементы
        self.text_input.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.process_button.configure(state="disabled")
        self.back_button.configure(state="disabled")

        # Запуск процесса в отдельном потоке
        threading.Thread(target=self.process_text, daemon=True).start()

    def process_text(self):
        # Заглушка для имитации процесса разметки
        time.sleep(5)  # Имитация долгого процесса

        # Завершение процесса
        self.loading_indicator.stop()  # Останавливаем индикатор загрузки
        # Разблокируем элементы
        self.text_input.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.process_button.configure(state="normal")
        self.back_button.configure(state="normal")

        print("Разметка завершена!")


class TextWorkWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Размеченная коллекция текстов")

        self.render_go_back_button()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
