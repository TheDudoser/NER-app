import io
import sys
import threading
from ipymarkup import show_span_ascii_markup

import customtkinter

from .base_window import BaseWindow
from .error_dialog import ErrorDialog
from .utils import setup_keyboard_shortcuts
from .components import UIComponents
from ner.ner_model import NERModel


class AddTextWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Разметка нового текста", width=900, height=700)
        self.text_input = None
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

        # Затем загружаем модель в фоне
        threading.Thread(target=self.load_model, daemon=True).start()

    def render_text_input_and_process_btn(self):
        """Отображение ввода исходного текста и кнопки Разметить"""
        text_frame = customtkinter.CTkFrame(self)
        text_frame.pack(pady=20, padx=20, fill="both", expand=False)

        text_label = customtkinter.CTkLabel(text_frame, text="Введите текст для разметки:", font=("Arial", 14))
        text_label.pack(pady=10)

        # Создаем текстовое поле
        self.text_input = customtkinter.CTkTextbox(
            text_frame,
            font=("Arial", 12),
            wrap="word",
            height=200,
            state="normal",  # Убедитесь, что состояние "normal" для редактирования
            undo=True,
            maxundo=-1
        )
        self.text_input.pack(pady=10, padx=10, fill="both", expand=False)

        self.process_button = customtkinter.CTkButton(text_frame, text="Разметить", command=self.start_processing)
        self.process_button.pack(pady=20)

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

    # TODO: Тоже вынести
    def render_results_display(self):
        # Рамка для вывода результатов NER
        self.results_frame = customtkinter.CTkFrame(self)
        self.results_frame.pack(pady=20, padx=20, fill="both", expand=True)

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

    # TODO: Тоже вынести
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
            self.render_results_display()
            self.display_results(entities, text)

        except Exception as e:
            self.hide_loading()
            self.show_error(f"Ошибка: {str(e)}")
        finally:
            self.enable_ui()

    def display_results(self, entities, text):
        # Вывод сущностей в консоль (для отладки)
        for entity in entities:
            print(
                f"Сущность: {entity['word']:20} → Тип: {entity['entity_group']:15} (Точность: {entity['score']:.4f})")

        # Подготовка spans для ipymarkup
        spans = [(ent['start'], ent['end'], ent['entity_group']) for ent in entities]

        # Перехватываем вывод show_span_ascii_markup
        output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output  # Перенаправляем stdout

        # Генерируем ASCII-разметку
        show_span_ascii_markup(text, spans)

        sys.stdout = old_stdout  # Возвращаем stdout
        marked_text = output.getvalue()

        # Проверяем, что marked_text не пустой
        print()
        print("DEBUG - Marked Text:", repr(marked_text))  # Для отладки

        # Вставляем в CTkTextbox (предварительно разблокировав)
        self.results_output.configure(state="normal")  # Разблокируем
        self.results_output.delete("1.0", "end")  # Очищаем (если нужно)
        self.results_output.insert("end", marked_text)  # Вставляем
        self.results_output.configure(state="disabled")  # Блокируем

    def disable_ui(self):
        """Разблокирует элементы UI после обработки"""
        self.text_input.configure(state="disabled")
        self.process_button.configure(state="disabled")
        self.back_button.configure(state="disabled")

    def enable_ui(self):
        """Разблокирует элементы UI после обработки"""
        self.text_input.configure(state="normal")
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
