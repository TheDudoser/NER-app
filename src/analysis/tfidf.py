import re
from typing import List, Tuple
from pymorphy3 import MorphAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

morph = MorphAnalyzer()


def lemma_analyzer(text: str) -> List[str]:
    # 1) разбиваем на слова и знаки препинания
    tokens = re.findall(r'\w+|[^\w\s]', text, flags=re.UNICODE)
    max_n = 3
    ngrams: List[str] = []

    # 2) скользящим окном строим n-граммы, пропуская окна с любым не-алфавитным токеном
    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            window = tokens[i:i + n]
            if all(tok.isalpha() for tok in window):
                # 3) лемматизируем каждое слово в окне
                lemmas = [morph.parse(tok)[0].normal_form for tok in window]
                ngrams.append(' '.join(lemmas))
    return ngrams


def extract_top_ngrams_with_tfidf(
        text: str,
        ngram_range: Tuple[int, int] = (1, 3),
        top_k: int = 10000
) -> List[Tuple[str, float]]:
    vectorizer = TfidfVectorizer(
        analyzer=lemma_analyzer,  # весь разбор + лемматизация здесь
        ngram_range=ngram_range,
        use_idf=True
    )
    tfidf_matrix = vectorizer.fit_transform([text])
    features = vectorizer.get_feature_names_out()
    scores = np.array(tfidf_matrix.sum(axis=0)).flatten()
    top_idx = np.argsort(scores)[-top_k:][::-1]
    return [(features[i], float(scores[i])) for i in top_idx if scores[i] > 0]
