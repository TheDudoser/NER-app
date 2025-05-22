import re
from functools import partial
from typing import List, Tuple
from pymorphy3 import MorphAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.analysis.utils import html_highlight_phrase_in_sentence
from src.database.models import Term


def lemma_analyzer_with_numbers(text: str, max_n: int) -> List[str]:
    morph = MorphAnalyzer()

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
                        parts = tok.split('-')
                        lemmas.append(
                            '-'.join(morph.parse(p)[0].normal_form for p in parts)
                        )
                    else:
                        lemmas.append(morph.parse(tok)[0].normal_form)
                ngrams.append(' '.join(lemmas))
    return ngrams


def extract_top_ngrams_with_tfidf(
        text: str,
        ngram_count: int = 3,
        top_k: int = 10000
) -> List[Tuple[str, float]]:
    # TODO: Надо подумать над разделением по бакетам
    #  чтобы более усреднённые результаты на разных выборках получать
    bound_lemma_analyzer = partial(lemma_analyzer_with_numbers, max_n=ngram_count)
    vectorizer = TfidfVectorizer(
        analyzer=bound_lemma_analyzer,
        use_idf=True
    )
    tfidf_matrix = vectorizer.fit_transform([text])
    features = vectorizer.get_feature_names_out()
    scores = np.array(tfidf_matrix.sum(axis=0)).flatten()
    top_idx = np.argsort(scores)[-top_k:][::-1]
    return [(features[i], float(scores[i])) for i in top_idx if scores[i] > 0]


def search_phrases_with_tfidf(
        query: str,
        phrases: list[Term],
        ngram_count: int = 3,
        top_k: int = 3
) -> List[Tuple[Term, float]]:
    """
    Функция для поиска по схожести с использованием TF-IDF
    :param query: Поисковой запрос
    :param phrases: Фразы типа Term, среди которых будет искаться query
    :param ngram_count: кол-во n-грамм
    :param top_k: Кол-во фраз в выдаче (результате)
    """
    # Создаем TF-IDF векторизатор с анализатором
    bound_lemma_analyzer = partial(lemma_analyzer_with_numbers, max_n=ngram_count)
    vectorizer = TfidfVectorizer(analyzer=bound_lemma_analyzer, use_idf=True)

    # Преобразуем фразы и запрос в TF-IDF векторы
    all_texts = [t.text for t in phrases] + [query]
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Вектор запроса - последняя строка матрицы
    query_vector = tfidf_matrix[-1]
    # Векторы фраз - все строки, кроме последней
    phrases_matrix = tfidf_matrix[:-1]

    # Вычисляем косинусное сходство между запросом и фразами
    similarities = cosine_similarity(query_vector, phrases_matrix)[0]

    # Сортируем результаты по убыванию схожести
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    return [(phrases[i], similarities[i]) for i in top_indices if similarities[i] > 0]


def search_sentences_in_text_with_tfidf(
        query: str,
        text: str,
        with_html_highlight_phrase=True,
        ngram_count: int = 3,
        top_k: int = 3
):
    bound_lemma_analyzer = partial(lemma_analyzer_with_numbers, max_n=ngram_count)
    lemma_query = bound_lemma_analyzer(text=query)[-1]

    # 1. Разбиваем текст на предложения
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

    # 2. Создаем TF-IDF векторизатор
    vectorizer = TfidfVectorizer(ngram_range=(1, ngram_count), stop_words=None)

    # 3. Векторизуем предложения и запрос
    tfidf_matrix = vectorizer.fit_transform(sentences + [query])
    sentence_vectors = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    # 4. Вычисляем косинусную схожесть
    similarities = cosine_similarity(query_vector, sentence_vectors).flatten()

    # 5. Получаем top_k предложений
    top_indices = similarities.argsort()[-top_k:][::-1]

    result_sentences = []
    for top in top_indices:
        lemma_sentences = bound_lemma_analyzer(text=sentences[top])
        if lemma_query in lemma_sentences:
            if with_html_highlight_phrase:
                result_sentences.append(
                    html_highlight_phrase_in_sentence(sentences[top], query)
                )
            else:
                result_sentences.append(sentences[top])

    return result_sentences
