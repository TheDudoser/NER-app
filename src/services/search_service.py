from typing import Any

from sqlmodel import Session

from src.services.phrase_service import PhraseService
from src.services.dictionary_service import DictionaryService
from src.analysis.analyser import Analyser
from src.analysis.consts import TYPE_COLOR
from src.analysis.utils import html_highlight_phrases_in_sentence

from src.models.phrase_type import PhraseType


class SearchService:
    @staticmethod
    def search_by_query(db: Session, query: str) -> list[dict[str, list[Any] | Any]]:
        analyser = Analyser()
        result = []
        if (query is not None) and (query != ""):
            for dictionary in DictionaryService.get_all_order_by_updated(db, 3):
                dict_entry = {
                    "dictionary": dictionary,
                    "terms": []
                }

                terms = PhraseService.get_terms_without_phrases(db, dictionary.id)
                terms_with_sims = analyser.search_phrases_with_tfidf(query=query, phrases=terms)

                for term, sim in terms_with_sims:
                    term_entry = {
                        "term": term,
                        "similarity": sim,
                        "sentences": []
                    }

                    # 2. Поиск термина во всех текстах словаря
                    for dict_analysis_result in dictionary.dictionary_analysis_results:
                        analysis_result = dict_analysis_result.analysis_result
                        if analysis_result.document.content == "":
                            continue

                        batches = analysis_result.document_batches
                        batch_vectors = analyser.simple_vectorize(batches)

                        if term.phrase_type != PhraseType.term:
                            connection_term_texts = [conn_term.from_term for conn_term in term.to_connections]
                        else:
                            connection_term_texts = [conn_term.to_term for conn_term in term.from_connections]

                        top_k = 3
                        sentence_ids = analyser.search_batches_by_queries_with_tfidf(
                            queries=[term.text],
                            batch_vectors=batch_vectors,
                            top_k=top_k
                        )
                        if len(sentence_ids) < top_k:
                            sentence_ids = sentence_ids + analyser.search_batches_by_queries_with_tfidf(
                                queries=[conn.text for conn in connection_term_texts],
                                batch_vectors=batch_vectors,
                                top_k=top_k
                            )

                        sentences = []
                        for idx in set(sentence_ids):
                            sentence = batches[idx]
                            # Сначала создаем словарь с цветами для фраз
                            phrase_colors = {
                                term.text: TYPE_COLOR[term.phrase_type]
                            }
                            # Добавляем соединения
                            phrase_colors.update({
                                conn.text: TYPE_COLOR[conn.phrase_type] for conn in connection_term_texts
                            })
                            sentence = html_highlight_phrases_in_sentence(
                                sentence,
                                phrase_colors
                            )

                            sentences.append(sentence)

                        term_entry["sentences"] = term_entry["sentences"] + sentences
                    dict_entry["terms"].append(term_entry)
                if len(dict_entry["terms"]) > 0:
                    result.append(dict_entry)

        return result
