from typing import List, Sequence

from sqlmodel import Session, select

from src.database.models import Term
from src.analysis.analyser import Analyser
from src.models.dto import TermDTO
from src.models.phrase_type import PhraseType


class PhraseService:
    def __init__(self):
        self.phrase_extractor = Analyser()

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

    @staticmethod
    def get_terms_without_phrases(db: Session, dict_id: int) -> Sequence[Term]:
        return db.exec(
            select(Term)
            .where(Term.dictionary_id == dict_id)
            .where(Term.hidden == False)
            .where(Term.phrase_type != PhraseType.phrase)
        ).all()
