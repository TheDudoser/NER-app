from src.windows.base_window import BaseWindow


def setup_keyboard_shortcuts(window: BaseWindow):
    window.bind("<Control-KeyPress>", __handle_keypress)
    window.bind("<Command-KeyPress>", __handle_keypress)


def __handle_keypress(event):
    key_actions = {
        67: '<<Copy>>', 86: '<<Paste>>',
        88: '<<Cut>>', 90: '<<Undo>>',
        89: '<<Redo>>', 65: '<<SelectAll>>'
    }
    if event.keycode in key_actions:
        event.widget.event_generate(key_actions[event.keycode])
        return "break"
