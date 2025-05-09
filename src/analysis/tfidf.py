import re
from functools import partial
from typing import List, Tuple
from pymorphy3 import MorphAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

morph = MorphAnalyzer()


def lemma_analyzer_with_numbers(text: str, max_n: int) -> List[str]:
    tokens = re.findall(
        r"[A-Za-zА-Яа-яёЁ0-9]{2,}(?:-[A-Za-zА-Яа-яёЁ0-9]{2,})*|[^\w\s]",
        text,
        flags=re.UNICODE
    )
    ngrams = []
    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            window = tokens[i:i+n]
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
