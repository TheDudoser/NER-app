import io
import os
import sys
import threading
from ipymarkup import show_span_ascii_markup

import customtkinter
from tkinter import filedialog

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

from .base_window import BaseWindow


class AddTextWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Разметка нового текста", width=900, height=700)
        self.text_input = None
        self.process_button = None
        self.loading_label = ''
        self.ner_pipeline = None

        self._setup_keyboard_shortcuts()

        # Сначала создаем элементы интерфейса
        self.render_text_input_and_process_btn()
        self.render_loading_indicator()
        self.show_loading("Загрузка модели...")
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

    def _setup_keyboard_shortcuts(self):
        """Настройка обработки горячих клавиш независимо от раскладки"""
        self.bind("<Control-KeyPress>", self._handle_keypress)
        self.bind("<Command-KeyPress>", self._handle_keypress)

    @staticmethod
    def _handle_keypress(event):
        """Обработчик горячих клавиш по keycode"""
        # Keycodes для основных операций
        key_actions = {
            67: '<<Copy>>',  # Ctrl+C
            86: '<<Paste>>',  # Ctrl+V
            88: '<<Cut>>',  # Ctrl+X
            90: '<<Undo>>',  # Ctrl+Z
            89: '<<Redo>>',  # Ctrl+Y
            65: '<<SelectAll>>'  # Ctrl+A
        }

        if event.keycode in key_actions:
            event.widget.event_generate(key_actions[event.keycode])
            return "break"  # Блокируем стандартное поведение

    def render_loading_indicator(self):
        # Фрейм для элементов загрузки
        self.loading_frame = customtkinter.CTkFrame(self)
        self.loading_label_widget = customtkinter.CTkLabel(  # Изменил имя переменной
            self.loading_frame,
            text="",  # Изначально пустой текст
            font=("Arial", 12)
        )
        self.loading_label_widget.pack(pady=5)

        self.model_loading_bar = customtkinter.CTkProgressBar(
            self.loading_frame,
            mode="indeterminate"
        )
        self.model_loading_bar.pack(pady=5, padx=20, fill="x")
        self.loading_frame.pack_forget()  # Скрываем изначально

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
        # model_name = "ai-forever/sbert_large_nlu_ru" # TODO: Она не обучена и поэтому извлекает всё подряд, нам это подходит?
        # model_name = "DeepPavlov/rubert-base-cased" # TODO: Тоже самое, не обучена
        model_name = "Davlan/bert-base-multilingual-cased-ner-hrl" # TODO: Обучена, но мало сущностей
        cache_dir = ".cache/ner_model"  # Папка для кэша

        try:
            # Создаем папку для кэша
            os.makedirs(cache_dir, exist_ok=True)

            # Проверяем, есть ли уже сохраненная модель
            if os.path.exists(os.path.join(cache_dir, "config.json")):
                print("🔄 Загрузка модели из локального кэша...")
                self.show_loading("Загрузка модели из кэша...")
                # Загружаем модель и токенизатор из кэша
                model = AutoModelForTokenClassification.from_pretrained(cache_dir)
                tokenizer = AutoTokenizer.from_pretrained(cache_dir)
            else:
                print("🌐 Скачивание модели из интернета...")
                self.show_loading("Скачивание модели...")
                # Загружаем модель и токенизатор и сохраняем в кэш
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model.save_pretrained(cache_dir)
                tokenizer.save_pretrained(cache_dir)

            # Универсальный способ загрузки (автоматически использует кэш)
            self.ner_pipeline = pipeline(
                "ner",
                model=model,
                aggregation_strategy="simple",
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )

            print(f"✅ Модель Загружена! Путь: {cache_dir}")
            self.hide_loading()
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            self.hide_loading()

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

    def process_text(self):
        try:
            text = self.text_input.get("1.0", "end-1c").strip()
            if not text:
                self.show_error("Введите текст для разметки!")
                return

            if not self.ner_pipeline:
                self.show_error("Модель ещё загружается...")
                return

            self.show_loading("Обработка текста...")

            # Передаём весь текст целиком (пайплайн сам разобьёт его на подходящие части)
            entities = self.ner_pipeline(text)

            self.hide_loading()

            # Если ещё не создано окно результатов - создаём
            if not hasattr(self, 'results_frame'):
                self.render_results_display()

            # Показываем красиво оформленные результаты
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

    def show_error(self, message):
        """Показывает сообщение об ошибке"""
        self.results_output.configure(state="normal")
        self.results_output.delete("1.0", "end")
        self.results_output.insert("end", f"Ошибка: {message}")
        self.results_output.configure(state="disabled")

    def clear_text_input(self):
        self.text_input.delete("1.0", "end")

    def upload_file(self):
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
        self.show_loading()
        self.disable_ui()
        self.process_text()
