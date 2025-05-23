from typing import List, Type

from sqlalchemy import delete
from sqlmodel import select, Session

from src.models.phrase_type import PhraseType
from src.services.exceptions import InvalidConnDictDTO
from src.analysis.phrase_extractor import PhraseExtractor
from database import get_session
from src.database.models import Dictionary, Document, Term, Connection
from src.models.dto import DictionaryShortDTO, DictionaryDTO, TermDTO, ConnectionDTO


class DictionaryService:
    def __init__(self):
        self.phrase_extractor = PhraseExtractor()
        self.gen_session = get_session()

    def get_short_dictionaries_from_db(
            self,
            with_timestamp: bool = False
    ) -> List[DictionaryShortDTO]:
        with next(self.gen_session) as db:
            dictionaries = db.exec(select(Dictionary)).all()

            dictionaries_data = [
                DictionaryShortDTO(
                    id=dictionary.id,
                    name=dictionary.name,
                    created_at=dictionary.created_at_local
                    if not with_timestamp
                    else dictionary.created_at_local.timestamp(),
                    terms_count=len(dictionary.terms),
                    connections_count=len(dictionary.connections)
                )
                for dictionary in dictionaries
            ]

            # Сортировка по дате создания (DESC)
            dictionaries_data.sort(key=lambda x: x.created_at, reverse=True)

            return dictionaries_data

    def get_dict_with_terms_and_connections(self, dictionary_id) -> DictionaryDTO | None:
        with next(self.gen_session) as db:
            dictionary = db.get(Dictionary, dictionary_id)
            if not dictionary:
                return None

            dict_terms = [
                TermDTO(
                    id=term.id,
                    text=term.text,
                    type=term.type,
                    phrase_type=term.phrase_type.value,
                    head_noun=self.phrase_extractor.get_head_noun_lemma(term.text),
                    tfidf=term.tfidf,
                )
                for term in dictionary.terms
            ]
            dict_terms.sort(key=lambda x: (x.head_noun, x.text))

            dict_terms = [
                TermDTO(
                    id=term.id,
                    text=term.text,
                    type=term.type,
                    phrase_type=term.phrase_type.value,
                    head_noun=self.phrase_extractor.get_head_noun_lemma(term.text),
                    tfidf=term.tfidf,
                )
                for term in dictionary.terms
            ]
            connections = [
                ConnectionDTO(
                    conn.from_term_id,
                    conn.to_term_id,
                )
                for conn in dictionary.connections
            ]

            return DictionaryDTO(
                id=dictionary.id,
                name=dictionary.name,
                tfidf_range=dictionary.tfidf_range,
                phrases=dict_terms,
                connections=connections
            )

    def save_dictionary_by_dto(self, dict_dto: DictionaryDTO) -> int:
        with next(self.gen_session) as db:
            with db.begin():
                # 1) Создаём словарь и документ
                dict_obj = Dictionary(
                    name=dict_dto.name,
                    tfidf_range=dict_dto.tfidf_range
                )
                db.add(dict_obj)
                db.flush()

                db.add(Document(
                    content=dict_dto.document_text,
                    dictionary_id=dict_obj.id
                ))

                # 3) Обрабатываем термины и связи
                try:
                    self._process_terms_for_new_dictionary(db, dict_dto, dict_obj.id)
                except Exception as e:
                    raise e

                return dict_obj.id

    def update_dictionary_by_dto(self, dict_dto: DictionaryDTO, dict_id) -> bool:
        with next(self.gen_session) as db:
            with db.begin():
                # 1) Находим словарь
                dict_obj = db.get(Dictionary, dict_id)
                if not dict_obj:
                    return False

                # Обновляем свойства словаря
                dict_obj.name = dict_dto.name
                dict_obj.tfidf_range = dict_dto.tfidf_range
                db.add(dict_obj)
                db.flush()

                # 2) Обрабатываем термины и связи более оптимально
                try:
                    self._process_terms_and_connections_optimized(db, dict_dto, dict_obj)
                except InvalidConnDictDTO as e:
                    raise e

        return True

    def delete_dictionary(self, dictionary_id: int) -> bool:
        with next(self.gen_session) as db:
            with db.begin():
                # 1) Находим словарь
                dict_obj = db.get(Dictionary, dictionary_id)
                if not dict_obj:
                    return False

                # 2) Удаляем связанные документы
                db.exec(delete(Document).where(Document.dictionary_id == dictionary_id))  # type: ignore

                # 2) Удаляем все связи словаря
                db.exec(delete(Connection).where(Connection.dictionary_id == dictionary_id))  # type: ignore

                # 3) Удаляем все термины словаря
                db.exec(delete(Term).where(Term.dictionary_id == dictionary_id))  # type: ignore

                # 4) Удаляем сам словарь
                db.delete(dict_obj)

        return True

    def merge_dictionaries(
            self,
            source_dict_data: DictionaryDTO,
            target_dict_id: int
    ) -> bool:
        with next(self.gen_session) as db:
            # по любому не всё тут учтено, но оно и не надо на самом деле сильно запариваться
            with db.begin():
                target_dict = db.get(Dictionary, target_dict_id)
                if not target_dict:
                    return False
                target_dict.tfidf_range = 0
                db.add(target_dict)
                db.flush()

                # Добавляем текстовый документ к словарю в который сливаем
                if source_dict_data.id:
                    existing_docs = db.exec(
                        select(Document).where(Document.dictionary_id == source_dict_data.id)
                    ).all()
                    for existing_doc in existing_docs:
                        existing_doc.dictionary_id = target_dict.id
                        db.add(existing_doc)
                else:
                    document_obj = Document(content=source_dict_data.document_text, dictionary_id=target_dict_id)
                    db.add(document_obj)
                db.flush()

                # Умное слияние терминов - учитываем существование в базе
                existing_terms = db.exec(
                    select(Term).where(Term.dictionary_id == target_dict_id)
                ).all()
                for existing_term in existing_terms:
                    existing_term.hidden = False
                    db.add(existing_term)
                db.flush()
                term_index = {
                    (t.text, t.type): t.id
                    for t in existing_terms
                }
                old_id_to_new_id = {}

                for term_dto in source_dict_data.phrases:
                    term_key = (term_dto.text, term_dto.type)
                    if term_key in term_index:
                        old_id_to_new_id[term_dto.id] = term_index[term_key]
                    else:
                        t = Term(
                            dictionary_id=target_dict_id,
                            phrase_type=term_dto.phrase_type,
                            text=term_dto.text,
                            type=term_dto.type,
                            tfidf=term_dto.tfidf,
                            hidden=False
                        )
                        db.add(t)
                        db.flush()
                        term_index[term_key] = t.id
                        if term_dto.id is not None:
                            old_id_to_new_id[term_dto.id] = t.id

                for conn in source_dict_data.connections:
                    from_id = old_id_to_new_id.get(conn.from_id)
                    to_id = old_id_to_new_id.get(conn.to_id)
                    if not from_id or not to_id:
                        raise InvalidConnDictDTO(f"Неверные ID связей: from={conn.from_id}, to={conn.to_id}")

                    c = Connection(
                        dictionary_id=target_dict_id,
                        from_term_id=from_id,
                        to_term_id=to_id,
                    )
                    db.add(c)

                # Удаление исходного словаря, если есть
                if source_dict_data.id:
                    source_dict_obj = db.get(Dictionary, source_dict_data.id)
                    if source_dict_obj:
                        db.exec(
                            delete(Connection).where(Connection.dictionary_id == source_dict_obj.id))  # type: ignore
                        db.exec(delete(Term).where(Term.dictionary_id == source_dict_obj.id))  # type: ignore
                        db.delete(source_dict_obj)

        return True

    @staticmethod
    def _process_terms_for_new_dictionary(
            db: Session,
            dict_dto: DictionaryDTO,
            dictionary_id: int
    ):
        """Обработка терминов для нового словаря."""
        terms = []
        term_id_mapping = {}  # {старый_id: новый_объект_термина}

        for term_dto in dict_dto.phrases:
            term = Term(
                dictionary_id=dictionary_id,
                phrase_type=term_dto.phrase_type,
                text=term_dto.text,
                type=term_dto.type,
                tfidf=term_dto.tfidf,
                hidden=term_dto.hidden
            )
            terms.append(term)
            db.add(term)

        db.flush()

        # Создаем маппинг старых ID к новым
        for term_dto, term in zip(dict_dto.phrases, terms):
            if term_dto.id is not None:
                term_id_mapping[term_dto.id] = term.id

        # Создаем связи
        for conn in dict_dto.connections:
            from_id = term_id_mapping.get(conn.from_id, conn.from_id)
            to_id = term_id_mapping.get(conn.to_id, conn.to_id)

            # Проверяем, что оба термина существуют
            if not db.get(Term, from_id) or not db.get(Term, to_id):
                raise InvalidConnDictDTO(f"Неверные ID связей: from={conn.from_id}, to={conn.to_id}")

            db.add(Connection(
                dictionary_id=dictionary_id,
                from_term_id=from_id,
                to_term_id=to_id
            ))

        return None

    @staticmethod
    def _process_terms_and_connections_optimized(
            db: Session,
            dict_dto: DictionaryDTO,
            dictionary: Type[Dictionary]
    ):
        """Оптимизированная функция для обработки терминов и связей словаря."""
        # Получаем текущие термины и связи из БД
        existing_terms = {term.id: term for term in dictionary.terms}
        existing_connections = {
            (conn.from_term_id, conn.to_term_id): conn
            for conn in dictionary.connections
        }

        # Словарь для маппинга старых ID (из DTO) в новые ID (из БД)
        old_id_to_new_id = {}

        # Обрабатываем термины
        for term_dto in dict_dto.phrases:
            if term_dto.id and term_dto.id in existing_terms:
                # Обновляем существующий термин
                term = existing_terms[term_dto.id]
                term.phrase_type = term_dto.phrase_type
                term.text = term_dto.text
                term.type = term_dto.type
                term.tfidf = term_dto.tfidf
                term.hidden = term_dto.hidden
                db.add(term)
                old_id_to_new_id[term_dto.id] = term.id
                # Удаляем из словаря, чтобы оставить только термины для удаления
                existing_terms.pop(term_dto.id)
            else:
                # Создаем новый термин
                term = Term(
                    dictionary_id=dictionary.id,
                    phrase_type=term_dto.phrase_type,
                    text=term_dto.text,
                    type=term_dto.type,
                    tfidf=term_dto.tfidf,
                    hidden=term_dto.hidden
                )
                db.add(term)
                db.flush()
                if term_dto.id is not None:
                    old_id_to_new_id[term_dto.id] = term.id

        # Удаляем оставшиеся термины (которые не пришли в DTO)
        for term_id in existing_terms:
            db.delete(existing_terms[term_id])

        # Обрабатываем связи
        new_connections = set()
        for conn in dict_dto.connections:
            from_id = old_id_to_new_id.get(conn.from_id, conn.from_id)
            to_id = old_id_to_new_id.get(conn.to_id, conn.to_id)

            if not from_id or not to_id:
                raise InvalidConnDictDTO(f"Неверные ID связей: from={conn.from_id}, to={conn.to_id}")

            connection_key = (from_id, to_id)
            new_connections.add(connection_key)

            if connection_key not in existing_connections:
                # Создаем новую связь
                c = Connection(
                    dictionary_id=dictionary.id,
                    from_term_id=from_id,
                    to_term_id=to_id,
                )
                db.add(c)
            else:
                # Связь уже существует - оставляем как есть
                existing_connections.pop(connection_key)

        # Удаляем оставшиеся связи (которые не пришли в DTO)
        for conn_key in existing_connections:
            db.delete(existing_connections[conn_key])

        return None
