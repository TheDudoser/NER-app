import re
from functools import partial
from typing import Dict, List, Tuple, Sequence

import numpy as np
import pymorphy3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.database.models import Term
from .consts import *


class Analyser:
    def __init__(self, ngram_count: int = 3):
        self.morph = pymorphy3.MorphAnalyzer()
        self.simple_vectorizer = TfidfVectorizer(
            ngram_range=(1, ngram_count),
            use_idf=True
        )
        self.vectorizer = TfidfVectorizer(
            analyzer=partial(self.lemma_analyzer_with_numbers, max_n=ngram_count),
            use_idf=True
        )

    def __get_pos(self, word: str) -> str | None:
        """Определение части речи с обработкой исключений"""
        parsed = self.morph.parse(word)[0]
        return parsed.tag.POS

    @staticmethod
    def __match_complex_pattern(pos_window: List[str], pattern: List) -> bool:
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
                    if Analyser.__match_complex_pattern(pos_pattern, pattern):
                        return pattern_type
        return None

    def lemma_analyzer_with_numbers(self, text: str, max_n: int = 3) -> List[str]:
        """Генерирует лемматизированные n-граммы из текста."""
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
                    lemmas = []
                    for tok in window:
                        if '-' in tok:
                            parts = [self.morph.parse(p)[0].normal_form for p in tok.split('-')]
                            lemmas.append('-'.join(parts))
                        else:
                            lemmas.append(self.morph.parse(tok)[0].normal_form)
                    ngrams.append(' '.join(lemmas))
        return ngrams

    def extract_top_ngrams_with_tfidf(
            self,
            text: str,
            top_k: int = 10000
    ) -> List[Tuple[str, float]]:
        """Извлекает топ n-грамм по TF-IDF."""
        if text == "":
            raise Exception("Empty text")

        tfidf_matrix = self.vectorizer.fit_transform([text])
        features = self.vectorizer.get_feature_names_out()
        scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()

        # Получаем индексы топ результатов
        top_idx = np.argsort(scores)[-top_k:][::-1]

        return [(features[i], float(scores[i])) for i in top_idx if scores[i] > 0]

    def analyze_text_with_stats(self, text: str) -> Dict:
        """Анализирует текст, извлекая ключевые фразы с их статистикой."""
        # Получаем топ n-грамм и сразу фильтруем их по шаблонам
        phrase_stats = [
            {
                'text': phrase,
                'type': pattern_type,
                'pattern_description': PATTERN_DESCRIPTIONS.get(pattern_type, "N/A"),
                'tfidf_score': tfidf,
                'length': len(phrase.split())
            }
            for phrase, tfidf in self.extract_top_ngrams_with_tfidf(text)
            if (pattern_type := self.__check_phrase_pattern(phrase))
        ]

        # Сортируем по убыванию TF-IDF и длине
        phrase_stats.sort(key=lambda x: (-x['tfidf_score'], -x['length']))

        # Собираем уникальные типы фраз
        unique_types = {p['type'] for p in phrase_stats}

        return {
            'phrases': phrase_stats,
            'total_phrases': len(phrase_stats),
            'unique_phrase_types': len(unique_types)
        }

    def search_phrases_with_tfidf(
            self,
            query: str,
            phrases: Sequence[Term],
            top_k: int = 3,
            threshold_similarity: float = 0.0,
    ) -> List[Tuple[Term, float]]:
        """
        Функция для поиска по схожести с использованием TF-IDF
        :param query: Поисковой запрос
        :param phrases: Фразы типа Term, среди которых будет искаться query
        :param top_k: Кол-во фраз в выдаче
        """
        if len(phrases) == 0:
            return []

        # Преобразуем фразы и запрос в TF-IDF векторы
        all_texts = [t.text for t in phrases] + [self.lemma_analyzer_with_numbers(text=query)[-1]]
        tfidf_matrix = self.simple_vectorizer.fit_transform(all_texts)

        # Вектор запроса - последняя строка матрицы
        query_vector = tfidf_matrix[-1]
        # Векторы фраз - все строки, кроме последней
        phrases_matrix = tfidf_matrix[:-1]

        # Вычисляем косинусное сходство между запросом и фразами
        similarities = cosine_similarity(query_vector, phrases_matrix)[0]

        # Сортируем результаты по убыванию схожести
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [(phrases[i], similarities[i]) for i in top_indices if similarities[i] > threshold_similarity]

    def search_batches_by_queries_with_tfidf(
            self,
            queries: List[str],
            batch_vectors,
            top_k: int = 3
    ) -> List[int]:
        """Возвращает список id batch, в которых встречались queries"""
        # Векторизуем каждую фразу отдельно
        queries_vector = self.simple_vectorizer.transform(queries)

        # Считаем схожесть каждой фразы с каждым предложением
        similarities = cosine_similarity(queries_vector, batch_vectors)

        # Агрегируем результаты (например, берём максимум или среднее)
        aggregated_similarities = np.max(similarities, axis=0)  # или np.mean

        # Выбираем top_k предложений
        top_indices = aggregated_similarities.argsort()[-top_k:][::-1]

        results = [idx for idx in top_indices if aggregated_similarities[idx] > 0]

        return results

    def simple_vectorize(self, docs: List[str]):
        if len(docs) != 0:
            return self.simple_vectorizer.fit_transform(docs)
        else:
            raise Exception("Empty docs")

    @staticmethod
    def get_sentences_by_text(text: str):
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

    def get_head_noun_lemma(self, phrase: str) -> str:
        """
        Ищет последнее слово с тегом NOUN, возвращает его нормальную форму.
        Если существительное не найдено, возвращает пустую строку.
        """
        words = phrase.split()
        for word in reversed(words):
            parsed = self.morph.parse(word)[0]
            if parsed.tag.POS == 'NOUN':
                return parsed.normal_form
        return ''
