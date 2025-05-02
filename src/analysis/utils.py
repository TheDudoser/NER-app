from typing import List


def match_complex_pattern(pos_window: List[str], pattern: List) -> bool:
    """Проверка сложных шаблонов с вложенными структурами"""
    if len(pos_window) != len(pattern):
        return False

    for p, w in zip(pattern, pos_window):
        if isinstance(p, tuple):
            # Вложенный шаблон
            sub_len = len(p)
            if not any(
                    all(sp == sw or sp == '?' for sp, sw in zip(p, pos_window[i:i + sub_len]))
                    for i in range(len(pos_window) - sub_len + 1)
            ):
                return False
        elif p != w and p != '?':
            return False

    return True
