from tkinter import filedialog

import customtkinter
from PIL import Image

from src.windows.base_window import BaseWindow


class UIComponents:
    @staticmethod
    def create_loading_indicator(window: BaseWindow):
        # Фрейм для элементов загрузки
        loading_frame = customtkinter.CTkFrame(window)
        loading_label_widget = customtkinter.CTkLabel(  # Изменил имя переменной
            loading_frame,
            text="",  # Изначально пустой текст
            font=("Arial", 12)
        )
        loading_label_widget.pack(pady=5)

        model_loading_bar = customtkinter.CTkProgressBar(
            loading_frame,
            mode="indeterminate"
        )
        model_loading_bar.pack(pady=5, padx=20, fill="x")
        loading_frame.pack_forget()  # Скрываем изначально

        return [loading_frame, loading_label_widget, model_loading_bar, loading_frame]

    @staticmethod
    def upload_file() -> str:
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()
            except Exception as e:
                print(f"Ошибка при загрузке файла: {e}")

    @staticmethod
    def create_img_element(image_path=None):
        """Загружает иконку из файла или использует встроенную"""
        try:
            image = Image.open(image_path)
            return customtkinter.CTkImage(light_image=image, dark_image=image, size=(20, 20))
        except Exception as e:
            print(f"Ошибка загрузки иконки: {e}")
            return None
