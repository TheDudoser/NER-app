from collections import defaultdict
from typing import Any, List, Dict

from sqlmodel import Session

from src.services.phrase_service import PhraseService
from src.services.dictionary_service import DictionaryService
from src.analysis.analyser import Analyser
from src.analysis.consts import TYPE_COLOR
from src.analysis.utils import html_highlight_phrases_in_sentence

from src.models.phrase_type import PhraseType


class SearchService:
    @staticmethod
    def search_by_query(db: Session, query: str, dict_limit: int = 3, sentences_limit: int = 3) -> list[dict[str, list[Any] | Any]]:
        analyser = Analyser()
        result = []
        if (query is not None) and (query != ""):
            for dictionary in DictionaryService.get_all_order_by_updated(db, dict_limit):
                dict_entry = {
                    "dictionary": dictionary,
                    "terms": []
                }

                terms = PhraseService.get_terms_without_phrases(db, dictionary.id)
                terms_with_sims = analyser.search_phrases_with_tfidf(query=query, phrases=terms)

                for term, sim in terms_with_sims:
                    term_entry = {
                        "term": term,
                        "connections": [],
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
                            continue
                            # connection_term_texts = [conn_term.from_term for conn_term in term.to_connections]
                        else:
                            connection_term_texts = [conn_term.to_term for conn_term in term.from_connections]

                        sentence_ids = analyser.search_batches_by_queries_with_tfidf(
                            queries=[term.text],
                            batch_vectors=batch_vectors,
                            top_k=sentences_limit
                        )

                        conn_texts_list = [conn.text for conn in connection_term_texts]
                        if conn_texts_list:
                            sentence_ids = sentence_ids + analyser.search_batches_by_queries_with_tfidf(
                                queries=[conn.text for conn in connection_term_texts],
                                batch_vectors=batch_vectors,
                                top_k=sentences_limit
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

                        term_entry["connections"] = term_entry["connections"] + connection_term_texts
                        term_entry["sentences"] = term_entry["sentences"] + sentences
                    dict_entry["terms"].append(term_entry)
                if len(dict_entry["terms"]) > 0:
                    result.append(dict_entry)

        return result

    @staticmethod
    def search_by_multiple_queries(
            db: Session,
            queries: List[str],
            dict_limit: int = 3,
            sentences_limit: int = 3
    ) -> List[Dict[str, List[Any] | Any]]:
        # Цвета для разных групп подсветки
        QUERY_BG_COLORS = [
            "#ffe082",  # Светло-жёлтый (Amber 200)
            "#81d4fa",  # Светло-голубой (Light Blue 200)
            "#a5d6a7",  # Светло-зелёный (Light Green 200)
            "#ffab91",  # Персиковый (Deep Orange 200)
            "#b39ddb",  # Светло-фиолетовый (Purple 200)
        ]

        analyser = Analyser()
        result = []

        if not queries or not any(queries):
            return result

        for dictionary in DictionaryService.get_all_order_by_updated(db, dict_limit):
            dict_entry = {
                "dictionary": dictionary,
                "terms": [],
                "intersection": {}
            }
            intersection_dict = {
                "terms": [],
                "sentences": []
            }
            sentences = []

            # Собираем термины по всем запросам
            terms_by_query = []
            for query in queries:
                terms = PhraseService.get_terms_without_phrases(db, dictionary.id)
                terms_with_sims = analyser.search_phrases_with_tfidf(query=query, phrases=terms)
                # Можно добавить сюда синонимы/значения, если они есть в модели
                terms_by_query.append([term for term, sim in terms_with_sims])

            # Собираем все предложения по всем терминам
            sentence_to_terms = defaultdict(set)  # предложение -> индексы запросов

            for idx, terms in enumerate(terms_by_query):
                for term in terms:
                    for dict_analysis_result in dictionary.dictionary_analysis_results:
                        analysis_result = dict_analysis_result.analysis_result
                        if analysis_result.document.content == "":
                            continue
                        batches = analysis_result.document_batches
                        batch_vectors = analyser.simple_vectorize(batches)
                        sentence_ids = analyser.search_batches_by_queries_with_tfidf(
                            queries=[term.text],
                            batch_vectors=batch_vectors,
                            top_k=sentences_limit * 2  # запас, чтобы не упустить пересечения
                        )
                        for sent_id in sentence_ids:
                            sentence_to_terms[(dict_analysis_result.id, sent_id)].add(idx)

            # Оставляем только те предложения, где встречаются хотя бы два разных запроса
            intersection_sentences = [
                (dict_analysis_result_id, sent_id, query_idxs)
                for (dict_analysis_result_id, sent_id), query_idxs in sentence_to_terms.items()
                if len(query_idxs) > 1
            ]

            id_to_result = {dar.id: dar for dar in dictionary.dictionary_analysis_results}
            # Для наглядности — подсветка
            for dict_analysis_result_id, sent_id, query_idxs in intersection_sentences:
                analysis_result = id_to_result[dict_analysis_result_id].analysis_result
                batches = analysis_result.document_batches
                sentence = batches[sent_id]

                # Собираем все фразы для каждого запроса
                phrase_colors = {}
                for idx, terms in enumerate(terms_by_query):
                    for term in terms:
                        color = TYPE_COLOR[term.phrase_type]
                        phrase_colors[term.text] = color
                        # Можно добавить сюда синонимы и значения, если нужно

                # Подсвечиваем с помощью background
                sentence_highlighted = html_highlight_phrases_in_sentence(
                    sentence,
                    phrase_colors
                )
                sentences.append(sentence_highlighted)

            if sentences:
                intersection_dict["sentences"] = sentences
                intersection_dict["terms"] = terms_by_query
                dict_entry["intersection"] = intersection_dict
                result.append(dict_entry)

        return result

