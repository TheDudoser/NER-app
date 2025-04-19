from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from src.analysis.utils import preprocess_text


def extract_top_ngrams_with_tfidf(
        text: str,
        ngram_range: Tuple[int, int] = (1, 3),
        top_k: int = 100
) -> List[Tuple[str, float]]:
    """
    Извлекает топ-n n-грамм текста с наибольшим TF-IDF.
    Возвращает список кортежей (фраза, tfidf_score).
    """
    vectorizer = TfidfVectorizer(
        tokenizer=preprocess_text,
        ngram_range=ngram_range,
        use_idf=True
    )

    tfidf_matrix = vectorizer.fit_transform([text])
    features = vectorizer.get_feature_names_out()
    scores = np.array(tfidf_matrix.sum(axis=0)).flatten()

    # Сортируем n-граммы по TF-IDF
    top_indices = np.argsort(scores)[-top_k:][::-1]
    return [(features[i], scores[i]) for i in top_indices if scores[i] > 0]
