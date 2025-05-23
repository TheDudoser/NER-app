from typing import List

from src.analysis.phrase_extractor import PhraseExtractor
from src.models.dto import TermDTO
from src.models.phrase_type import PhraseType


class PhraseService:
    def __init__(self):
        self.phrase_extractor = PhraseExtractor()

    def get_terms_by_analysis_data(self, analysis_data) -> List[TermDTO]:
        phrases = [
            TermDTO(
                id=idx,
                text=phrase["text"],
                type=phrase["type"],
                phrase_type=PhraseType.phrase,
                tfidf=phrase["tfidf_score"],
                head_noun=self.phrase_extractor.get_head_noun_lemma(phrase['text']),
            )
            for idx, phrase in enumerate(analysis_data["phrases"])
        ]

        # Сортируем: сначала по head_noun, потом по тексту для стабильности
        phrases.sort(key=lambda x: (x.head_noun, x.text))

        return phrases
