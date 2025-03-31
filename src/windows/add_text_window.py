import threading

import customtkinter

from ner import prepare_entities
from .base_window import BaseWindow
from .error_dialog import ErrorDialog
from .utils import setup_keyboard_shortcuts
from .components import UIComponents
from ner.ner_model import NERModel


class AddTextWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Разметка нового текста", width=900, height=700)
        self.text_input = None
        self.upload_button = None
        self.process_button = None
        self.results_frame = None
        self.results_output = None

        # model_name = "ai-forever/sbert_large_nlu_ru" # TODO: Она не обучена и поэтому извлекает всё подряд, нам это подходит?
        # model_name = "DeepPavlov/rubert-base-cased" # TODO: Тоже самое, не обучена
        model_name = "Davlan/bert-base-multilingual-cased-ner-hrl"  # TODO: Обучена, но мало сущностей
        cache_dir = ".cache/ner_model"  # Папка для кэша
        self.ner_model = NERModel(model_name, cache_dir)

        setup_keyboard_shortcuts(self)

        # Сначала создаем элементы интерфейса
        self.render_text_input_and_process_btn()
        self.render_loading_indicator()
        self.render_go_back_button()
        self.render_results_display()

        # Затем загружаем модель в фоне
        threading.Thread(target=self.load_model, daemon=True).start()

    def render_text_input_and_process_btn(self):
        """Отображение ввода исходного текста и кнопок"""
        text_frame = customtkinter.CTkFrame(self)
        text_frame.pack(pady=20, padx=20, fill="both", expand=False)

        # Верхняя панель только с кнопкой загрузки файла
        upload_panel = customtkinter.CTkFrame(text_frame, fg_color="transparent")
        upload_panel.pack(pady=(30,0), fill="x")

        # Кнопка загрузки файла с иконкой (центрированная)
        self.upload_button = customtkinter.CTkButton(
            upload_panel,
            text="",  # Без текста
            width=40,
            image=UIComponents.create_img_element('public/img/file_icon.png'),
            command=self.handle_file_upload,
        )
        self.upload_button.pack(side="left", padx=10)

        text_label = customtkinter.CTkLabel(upload_panel, text="Введите текст для разметки:", font=("Arial", 14))
        text_label.pack(side="left")

        # Создаем текстовое поле
        self.text_input = customtkinter.CTkTextbox(
            text_frame,
            font=("Arial", 12),
            wrap="word",
            height=200,
            state="normal",
            undo=True,
            maxundo=-1
        )
        self.text_input.pack(pady=10, padx=10, fill="both", expand=False)

        # Кнопка обработки снизу
        self.process_button = customtkinter.CTkButton(
            text_frame,
            text="Разметить",
            command=self.start_processing
        )
        self.process_button.pack(pady=(0, 10))

    def handle_file_upload(self):
        """Обрабатывает загрузку файла и вставляет его содержимое в текстовое поле"""
        file_content = UIComponents.upload_file()
        if file_content:
            # Очищаем текущее содержимое и вставляем текст из файла
            self.text_input.configure(state="normal")
            self.text_input.delete("1.0", "end")
            self.text_input.insert("1.0", file_content)
        else:
            self.show_error("Ошибка при загрузке файла")

    def render_loading_indicator(self):
        [
            self.loading_frame,
            self.loading_label_widget,
            self.model_loading_bar,
            self.loading_frame
        ] = UIComponents.create_loading_indicator(self)

    def show_loading(self, loading_label: str = ''):
        """Показать индикатор загрузки"""
        self.loading_label_widget.configure(text=loading_label)  # Обновляем текст лейбла
        self.loading_frame.pack(pady=10, padx=20, fill="x")
        self.model_loading_bar.start()

    def hide_loading(self):
        """Скрыть индикатор загрузки"""
        self.model_loading_bar.stop()
        self.loading_frame.pack_forget()

    def load_model(self):
        """Загрузка модели с кэшированием на диск"""
        if self.ner_model.is_model_cached:
            self.show_loading("Загрузка модели из кэша...")
        else:
            self.show_loading("Скачивание модели...")
        loaded_model = self.ner_model.load()

        if not loaded_model:
            self.show_error("Произошла ошибка во время загрузки модели")

        self.hide_loading()

    def render_results_display(self):
        # Рамка для вывода результатов NER
        self.results_frame = customtkinter.CTkFrame(self)
        self.results_frame.pack_forget()

        # Заголовок
        results_label = customtkinter.CTkLabel(self.results_frame, text="Результаты разметки:", font=("Arial", 14))
        results_label.pack(pady=10)

        # Текстовое поле для вывода результатов (можно заменить на более сложный виджет)
        self.results_output = customtkinter.CTkTextbox(
            self.results_frame,
            font=("Arial", 12),
            wrap="word",
            height=200,
            state="disabled"  # Сначала недоступно для редактирования
        )
        self.results_output.pack(pady=10, padx=10, fill="both", expand=True)

    def process_text(self):
        try:
            text = self.text_input.get("1.0", "end-1c").strip()
            if not text:
                self.show_error("Введите текст для разметки!")
                return

            if not self.ner_model.is_predict():
                self.show_error("Модель ещё загружается...")
                return

            self.show_loading("Обработка текста...")

            # Передаём весь текст целиком (пайплайн сам разобьёт его на подходящие части)
            entities = self.ner_model.predict(text)

            self.hide_loading()
            # self.render_results_display()
            self.display_results(entities, text)

        except Exception as e:
            self.hide_loading()
            self.show_error(f"Ошибка: {str(e)}")
        finally:
            self.enable_ui()

    def display_results(self, entities, text):
        marked_text = prepare_entities(entities, text)

        # Вставляем в CTkTextbox (предварительно разблокировав)
        self.results_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.results_output.configure(state="normal")  # Разблокируем
        self.results_output.delete("1.0", "end")  # Очищаем (если нужно)
        self.results_output.insert("end", marked_text)  # Вставляем
        self.results_output.configure(state="disabled")  # Блокируем

    def disable_ui(self):
        """Разблокирует элементы UI после обработки"""
        self.text_input.configure(state="disabled")
        self.upload_button.configure(state="disabled")
        self.process_button.configure(state="disabled")
        self.back_button.configure(state="disabled")

    def enable_ui(self):
        """Разблокирует элементы UI после обработки"""
        self.text_input.configure(state="normal")
        self.upload_button.configure(state="normal")
        self.process_button.configure(state="normal")
        self.back_button.configure(state="normal")

    def show_error(self, message: str):
        """Показывает сообщение об ошибке"""
        ErrorDialog(self, message=message)
        self.hide_loading()

    def start_processing(self):
        self.show_loading()
        self.disable_ui()
        self.process_text()
