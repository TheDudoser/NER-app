import customtkinter


class BaseWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, title, width=800, height=600):
        super().__init__(parent)
        self.geometry(f"{width}x{height}")
        self.raw_title = title
        self.title(f"NER APP - {title}")
        self.parent = parent
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()

        self.geometry(f"+{parent_x}+{parent_y}")

    def render_go_back_button(self):
        self.back_button = customtkinter.CTkButton(
            self,
            text="← Назад",
            width=30,
            height=30,
            command=self.go_back,
            fg_color="transparent",
            corner_radius=15,
        )
        self.back_button.place(x=10, y=10)

    def go_back(self):
        self.destroy()
        self.parent.deiconify()
