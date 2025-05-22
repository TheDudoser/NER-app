import re
from typing import List

from pymorphy3 import MorphAnalyzer


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


def html_highlight_phrase_in_sentence(sentence: str, lemma_phrase: str) -> str:
    morph = MorphAnalyzer()

    # Разбиваем лемматизированную фразу на слова
    lemma_words = lemma_phrase.split()

    # Для каждого слова во фразе находим все возможные формы в предложении
    word_patterns = []
    for lemma_word in lemma_words:
        # Находим все словоформы в предложении, соответствующие лемме
        possible_forms = set()
        for word in re.findall(r'\w+', sentence):
            parsed = morph.parse(word)[0]
            if parsed.normal_form == lemma_word:
                possible_forms.add(word)

        # Если не нашли форм, используем саму лемму (на случай, если она есть в тексте)
        if not possible_forms:
            possible_forms.add(lemma_word)

        # Создаем часть регулярного выражения для этого слова
        word_pattern = r'(?:' + '|'.join(re.escape(form) for form in possible_forms) + r')'
        word_patterns.append(word_pattern)

    # Собираем полное регулярное выражение для фразы
    # Учитываем возможные пробелы и знаки препинания между словами
    phrase_pattern = r'(\b' + r'[\s\-,;:]+'.join(word_patterns) + r'\b)'

    # Добавляем выделение тегом strong
    highlighted = re.sub(phrase_pattern, r'<strong>\1</strong>', sentence, flags=re.IGNORECASE)

    return highlighted
