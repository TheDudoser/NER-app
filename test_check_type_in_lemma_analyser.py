from functools import partial

import numpy as np
from pymorphy3 import MorphAnalyzer
import re
from typing import List, Dict, Tuple, Callable

from sklearn.feature_extraction.text import TfidfVectorizer

morph = MorphAnalyzer()
PHRASE_RULES: Dict[str, Dict[str, Callable[[List[str]], bool]]] = {
    "однословное": {
        "condition": lambda words: (
                len(words) == 1 and
                'NOUN' == morph.parse(words[0])[0].tag.POS
        )
    },
    "адъективное": {
        "condition": lambda words: (
                len(words) == 2 and
                'ADJF' in [morph.parse(word)[0].tag.POS for word in words] and
                'NOUN' in [morph.parse(word)[0].tag.POS for word in words]
        )
    },
    "генитивное": {
        "condition": lambda words: (
                len(words) == 2 and
                [morph.parse(word)[0].tag.POS for word in words].count('NOUN') == 2 and
                morph.parse(words[1])[0].tag.case in ['nomn', 'accs'] and
                'gent' == morph.parse(words[0])[0].tag.case
        )
    },
    "адъективное_многословное": {
        "condition": lambda words: (
                len(words) == 3 and
                [morph.parse(word)[0].tag.POS for word in words[:-1]].count('ADJF') == 2 and
                'NOUN' == morph.parse(words[-1])[0].tag.POS
        )
    },
    "генитивное_многословное": {
        "condition": lambda words: (
                len(words) == 3 and
                [morph.parse(word)[0].tag.POS for word in words].count('NOUN') == 3 and
                [morph.parse(word)[0].tag.case for word in words].count('gent') == 2 and
                set([morph.parse(word)[0].tag.case for word in words]).intersection({'nomn', 'accs'})
        )
    },
    "адъективно-генитивное": {
        "condition": lambda words: (
                len(words) == 3 and
                'NOUN' in morph.parse(words[0])[0].tag and
                'ADJF' in morph.parse(words[1])[0].tag and
                'NOUN' in morph.parse(words[2])[0].tag and
                morph.parse(words[1])[0].tag.case == 'gent' and
                morph.parse(words[2])[0].tag.case == 'gent'
        )
    },
    "генитивно-адъективное": {
        "condition": lambda words: (
                len(words) == 3 and
                'ADJF' in morph.parse(words[0])[0].tag and
                'NOUN' in morph.parse(words[1])[0].tag and
                'NOUN' in morph.parse(words[2])[0].tag and
                morph.parse(words[2])[0].tag.case == 'gent'
        )
    }
}


# Константы с правилами проверки типов словосочетаний


def check_phrase_type(window: List[str]) -> str | None:
    """Определяет тип словосочетания по заданным правилам."""
    for phrase_type, rule in PHRASE_RULES.items():
        if rule["condition"](window):
            return phrase_type
    return None


def lemma_analyzer(text: str, max_n: int = 3) -> List[Tuple[str, str]]:
    """Генерирует лемматизированные n-граммы из текста с проверкой типа словосочетания."""
    tokens = re.findall(
        r"[A-Za-zА-Яа-яёЁ0-9]{2,}(?:-[A-Za-zА-Яа-яёЁ0-9]{2,})*|[^\w\s]",
        text,
        flags=re.UNICODE
    )

    ngrams = []
    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            window = tokens[i:i + n]
            if all(re.fullmatch(r"[A-Za-zА-Яа-яёЁ0-9-]+", tok) for tok in window):
                # Проверяем тип словосочетания
                phrase_type = check_phrase_type(window)
                if phrase_type is None:
                    continue

                lemmas = []
                for tok in window:
                    lemmas.append(morph.parse(tok)[0].normal_form)
                ngrams.append((phrase_type, ' '.join(lemmas)))
    return ngrams


with open("text_examples/pdd.txt", "r") as file:
    text = file.read().encode("utf-8")

vectorizer = TfidfVectorizer(
    analyzer=partial(lemma_analyzer, max_n=3),
    use_idf=True
)
tfidf_matrix = vectorizer.fit_transform([text])
features = vectorizer.get_feature_names_out()
scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()

# Получаем индексы топ результатов
top_idx = np.argsort(scores)[-10000:][::-1]

print(
    [(features[i], float(scores[i])) for i in top_idx if scores[i] > 0]
)
