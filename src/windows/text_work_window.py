from .base_window import BaseWindow


class TextWorkWindow(BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Размеченная коллекция текстов")
        self.render_go_back_button()
