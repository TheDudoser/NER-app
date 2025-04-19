from typing import Dict

import pymorphy3

from .consts import *
from .tfidf import extract_top_ngrams_with_tfidf
from .utils import match_complex_pattern


class PhraseExtractor:
    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()

    def __get_pos(self, word: str) -> str | None:
        """Определение части речи с обработкой исключений"""
        parsed = self.morph.parse(word)[0]
        return parsed.tag.POS

    def __normalize_word(self, word: str) -> str:
        """Нормализация слова с обработкой исключений"""
        parsed = self.morph.parse(word)[0]
        return parsed.normal_form

    def __check_phrase_pattern(self, phrase: str) -> str | None:
        """
        Проверяет, соответствует ли фраза одному из POS-шаблонов.
        Возвращает тип шаблона или None.
        """
        words = phrase.split()
        pos_tags = [self.__get_pos(word) for word in words]
        pos_pattern = [POS_TAGS.get(tag, '?') for tag in pos_tags]

        for pattern_type, patterns in PATTERNS.items():
            for pattern in patterns:
                if isinstance(pattern, tuple):
                    if len(pos_pattern) == len(pattern) and all(
                            p == w or p == '?' for p, w in zip(pattern, pos_pattern)
                    ):
                        return pattern_type
                else:
                    if match_complex_pattern(pos_pattern, pattern):
                        return pattern_type
        return None

    def analyze_text_with_stats(self, text: str) -> Dict:
        # Шаг 1: Извлекаем топ-n n-грамм по TF-IDF
        top_ngrams = extract_top_ngrams_with_tfidf(text)

        # Шаг 2: Фильтруем их по POS-шаблонам
        phrase_stats = []
        for phrase, tfidf in top_ngrams:
            pattern_type = self.__check_phrase_pattern(phrase)
            if not pattern_type:
                continue

            phrase_stats.append({
                'phrase': phrase,
                'pattern_type': pattern_type,
                'pattern_description': PATTERN_DESCRIPTIONS.get(pattern_type, "N/A"),
                'tfidf_score': tfidf,
                'length': len(phrase.split())
            })

        # Шаг 3: Сортируем по TF-IDF и длине
        phrase_stats.sort(key=lambda x: (-x['tfidf_score'], -x['length']))

        return {
            'phrases': phrase_stats,
            'total_phrases': len(phrase_stats),
            'unique_patterns': len({p['pattern_type'] for p in phrase_stats})
        }
