import re
from typing import Dict

from pymorphy3 import MorphAnalyzer


morph = MorphAnalyzer()


def html_highlight_phrase_in_sentence(sentence: str, lemma_phrase: str) -> str:
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
    highlighted = re.sub(phrase_pattern, r'<strong style="color: green">\1</strong>', sentence, flags=re.IGNORECASE)

    return highlighted


def html_highlight_phrases_in_sentence(
        sentence: str,
        phrase_colors: Dict[str, str],
        default_color: str = "green"
) -> str:
    print(phrase_colors)
    """
    Выделяет в предложении несколько фраз разными цветами.

    Args:
        sentence: Исходное предложение
        phrase_colors: Словарь {фраза: цвет} (например, {"надо сделать": "red", "срочно": "blue"})
        default_color: Цвет по умолчанию, если не указан

    Returns:
        Предложение с выделенными фразами в HTML
    """
    # Сначала обрабатываем более длинные фразы, затем короткие
    sorted_phrases = sorted(phrase_colors.keys(), key=len, reverse=True)

    # Предварительно находим все слова в предложении
    words_in_sentence = re.findall(r'\w+', sentence)
    word_set = set(words_in_sentence)

    # Создаем список для хранения всех шаблонов и их цветов
    patterns_with_colors = []

    for phrase in sorted_phrases:
        color = phrase_colors.get(phrase, default_color)
        lemma_words = phrase.split()

        word_patterns = []
        for lemma_word in lemma_words:
            # Проверяем, есть ли лемма прямо в предложении
            if lemma_word in word_set:
                possible_forms = {lemma_word}
            else:
                # Ищем только среди слов, которые есть в предложении
                possible_forms = set()
                for word in word_set:
                    parsed = morph.parse(word)[0]
                    if parsed.normal_form == lemma_word:
                        possible_forms.add(word)

            # Если не нашли форм, используем саму лемму
            if not possible_forms:
                possible_forms = {lemma_word}

            word_pattern = r'(?:' + '|'.join(map(re.escape, possible_forms)) + r')'
            word_patterns.append(word_pattern)

        # Собираем полное регулярное выражение для фразы
        phrase_pattern = r'(\b' + r'[\s\-,;:ив]+'.join(word_patterns) + r'\b)'
        patterns_with_colors.append((phrase_pattern, color))

    # Применяем замены в порядке убывания длины фраз
    highlighted = sentence
    for pattern, color in patterns_with_colors:
        highlighted = re.sub(
            pattern,
            fr'<strong style="color: {color}">\1</strong>',
            highlighted,
            flags=re.IGNORECASE
        )

    return highlighted
