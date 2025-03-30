import threading
import customtkinter
from tkinter import filedialog

import torch

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
        """Загрузка модели"""
        try:
            from transformers import pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model="sberbank-ai/ruBert-large",
                device=0 if torch.cuda.is_available() else -1,
                aggregation_strategy="simple"
            )
            print("Модель загружена!")
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

            # Разбиваем текст на предложения для прогресса
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            total = len(sentences)

            self.show_loading("Обработка текста...")
            print("Обработка текста...")
            results = self.ner_pipeline(sentences)
            print("Обработка завершена")
            self.hide_loading()
            self.render_results_display()

            # Показываем результаты
            self.display_results(results)

        except Exception as e:
            self.show_error(f"Ошибка: {str(e)}")

    # def display_results(self, entities):
    #     self.results_output.configure(state="normal")
    #     self.results_output.delete("1.0", "end")
    #
    #     self.results_output.insert("end", json.dumps(str(entities)))
    #
    #     self.results_output.configure(state="disabled")

    # def display_results(self, entities):
    #     self.results_output.configure(state="normal")
    #     self.results_output.delete("1.0", "end")
    #
    #     try:
    #         if not entities:
    #             self.results_output.insert("end", "Не найдено именованных сущностей")
    #             return
    #
    #         text = "Результаты распознавания сущностей:\n\n"
    #
    #         for i, sentence_entities in enumerate(entities, 1):
    #             text += f"=== Предложение {i} ===\n"
    #
    #             if not sentence_entities:
    #                 text += "  Не найдено сущностей\n\n"
    #                 continue
    #
    #             for entity in sentence_entities:
    #                 word = entity.get('word', '')
    #                 entity_type = entity.get('entity_group', 'N/A')
    #                 confidence = entity.get('score', 0)
    #                 start = entity.get('start', 0)
    #                 end = entity.get('end', 0)
    #
    #                 text += (
    #                     f"• Текст: {word}\n"
    #                     f"  Тип: {entity_type}\n"
    #                     f"  Уверенность: {confidence:.3f}\n"
    #                     f"  Позиция: {start}-{end}\n\n"
    #                 )
    #
    #             text += "\n"
    #
    #         self.results_output.insert("end", text)
    #
    #     except Exception as e:
    #         # Если что-то пошло не так, выводим оригинальные данные с форматированием
    #         self.results_output.insert(
    #             "end",
    #             json.dumps(entities, indent=2, ensure_ascii=False)
    #         )
    #         print(f"Ошибка форматирования результатов: {e}")
    #
    #     self.results_output.configure(state="disabled")

    def display_results(self, entities):
        self.results_output.configure(state="normal")
        self.results_output.delete("1.0", "end")

        try:
            if not entities or not any(entities):
                self.results_output.insert("end", "Не найдено именованных сущностей")
                return

            # Цвета для разных типов сущностей (только foreground)
            entity_colors = {
                "LABEL_0": "#FF6B6B",  # Красный
                "LABEL_1": "#4ECDC4",  # Голубой
                "LABEL_2": "#FFD166",  # Желтый
                "default": "#6B5B95"  # Фиолетовый
            }

            # Собираем текст с метками сущностей
            full_text = ""
            entity_positions = []  # Будем хранить позиции сущностей

            for i, sentence_entities in enumerate(entities):
                if not sentence_entities:
                    continue

                # Сортируем сущности по позиции начала
                sorted_entities = sorted(sentence_entities, key=lambda x: x['start'])

                sentence_text = ""
                last_end = 0

                for entity in sorted_entities:
                    # Текст до сущности
                    before_entity = sentence_entities[0]['word'][last_end:entity['start']]
                    sentence_text += before_entity

                    # Добавляем сущность с меткой
                    entity_text = entity['word']
                    entity_type = entity['entity_group']
                    score = entity['score']

                    # Сохраняем позиции для выделения
                    start_pos = len(full_text + sentence_text)
                    end_pos = start_pos + len(entity_text)

                    entity_positions.append({
                        'start': start_pos,
                        'end': end_pos,
                        'type': entity_type,
                        'score': score,
                        'text': entity_text
                    })

                    sentence_text += entity_text
                    last_end = entity['end']

                # Добавляем оставшийся текст
                sentence_text += sentence_entities[0]['word'][last_end:]
                full_text += f"Предложение {i + 1}:\n{sentence_text}\n\n"

            # Вставляем текст
            self.results_output.insert("end", full_text)

            # Применяем выделение
            self.highlight_entities(entity_positions, entity_colors)

        except Exception as e:
            self.results_output.insert("end", f"Ошибка: {str(e)}")

        self.results_output.configure(state="disabled")

    def highlight_entities(self, entities, colors):
        """Применяет цветовое выделение к сущностям"""
        for entity in entities:
            entity_type = entity['type']
            color = colors.get(entity_type, colors["default"])

            # Создаем тег для этого типа
            tag_name = f"tag_{entity_type}_{entity['start']}"
            self.results_output.tag_config(tag_name, foreground=color)

            # Рассчитываем позиции в текстовом поле
            start_pos = f"1.0+{entity['start']}c"
            end_pos = f"1.0+{entity['end']}c"

            # Применяем тег
            self.results_output.tag_add(tag_name, start_pos, end_pos)

            # Добавляем всплывающую подсказку
            self.results_output.tag_bind(
                tag_name,
                "<Enter>",
                lambda e, t=entity_type, s=entity['score']: self.show_tooltip(f"Тип: {t}\nУверенность: {s:.2f}")
            )
            self.results_output.tag_bind(tag_name, "<Leave>", lambda e: self.hide_tooltip())

    def show_tooltip(self, text):
        """Показывает всплывающую подсказку"""
        self.tooltip = customtkinter.CTkToplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry("+%d+%d" % (self.winfo_pointerx() + 10, self.winfo_pointery() + 10))
        label = customtkinter.CTkLabel(self.tooltip, text=text)
        label.pack()

    def hide_tooltip(self):
        """Скрывает всплывающую подсказку"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

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
