from dataclasses import asdict
import json
import os
from typing import Optional, Type

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import delete
from sqlmodel import Session, select
from starlette.requests import Request
import starlette.status as status

from database import get_session
from src.routers.dto import DictionaryDTO, DictionaryShortDTO
from src.database.models import Dictionary, Term, Connection, PhraseType, Document
from src.input_text_worker.functions import get_json_hash
from config import ANALYSIS_DIR, logger

api_router = APIRouter(prefix="/api", tags=["api"], default_response_class=JSONResponse)


# TODO: Повыносить логику работы с данными в сервисы

@api_router.post("/analysis")
async def save_analysis(request: Request) -> JSONResponse:
    """Сохранение результатов анализа для последующего создания из них словаря"""
    try:
        data = await request.json()
        # Ищем хэш текста чтобы каждый раз не сохранять новый файл
        file_hash = get_json_hash(data)

        filename = f"{ANALYSIS_DIR}/analysis_{file_hash}.json"

        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return JSONResponse(content={"success": True, "file_id": file_hash})
    except Exception as e:
        logger.error(msg=f"Error saving analysis: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@api_router.post("/dictionary")
async def save_dictionary(dict_dto: DictionaryDTO, db: Session = Depends(get_session)) -> JSONResponse:
    try:
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
            if error_response := _process_terms_for_new_dictionary(dict_dto, dict_obj.id, db):
                return error_response

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "dictionary_id": dict_obj.id,
                "message": "Словарь успешно сохранён"
            }
        )

    except Exception as e:
        logger.error(f"Ошибка сохранения словаря: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Произошла ошибка при создании словаря"
            }
        )


def _process_terms_for_new_dictionary(
        dict_dto: DictionaryDTO,
        dictionary_id: int,
        db: Session
) -> Optional[JSONResponse]:
    """Оптимизированная обработка терминов для нового словаря."""
    # Создаем все термины сначала
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

    db.flush()  # Получаем ID всех терминов

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
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"Неверные ID связей: from={conn.from_id}, to={conn.to_id}"
                }
            )

        db.add(Connection(
            dictionary_id=dictionary_id,
            from_term_id=from_id,
            to_term_id=to_id
        ))

    return None


@api_router.patch("/dictionary/{dictionary_id}")
async def update_dictionary(dict_dto: DictionaryDTO, dictionary_id: int,
                            db: Session = Depends(get_session)) -> JSONResponse:
    try:
        with db.begin():
            # 1) Находим словарь
            dict_obj = db.get(Dictionary, dictionary_id)
            if not dict_obj:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "Словарь не найден"}
                )

            # Обновляем свойства словаря
            dict_obj.name = dict_dto.name
            dict_obj.tfidf_range = dict_dto.tfidf_range
            db.add(dict_obj)
            db.flush()

            # 2) Обрабатываем термины и связи более оптимально
            result = _process_terms_and_connections_optimized(dict_dto, dict_obj, db)
            if isinstance(result, JSONResponse):
                return result

        return JSONResponse(content={"success": True, "message": "Словарь обновлён"})
    except Exception as e:
        logger.error(msg=f"Error updating dictionary: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


def _process_terms_and_connections_optimized(
        dict_dto: DictionaryDTO,
        dictionary: Type[Dictionary],
        db: Session
) -> Optional[JSONResponse]:
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
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"Неверные ID связей: from={conn.from_id}, to={conn.to_id}"
                }
            )

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


@api_router.delete("/dictionary/{dictionary_id}", name="delete_dictionary")
async def delete_dictionary(dictionary_id: int, db: Session = Depends(get_session)) -> JSONResponse:
    try:
        with db.begin():
            # 1) Находим словарь
            dict_obj = db.get(Dictionary, dictionary_id)
            if not dict_obj:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "Словарь не найден"}
                )

            # 2) Удаляем связанные документы
            db.exec(delete(Document).where(Document.dictionary_id == dictionary_id))  # type: ignore

            # 2) Удаляем все связи словаря
            db.exec(delete(Connection).where(Connection.dictionary_id == dictionary_id))  # type: ignore

            # 3) Удаляем все термины словаря
            db.exec(delete(Term).where(Term.dictionary_id == dictionary_id))  # type: ignore

            # 4) Удаляем сам словарь
            db.delete(dict_obj)

        return JSONResponse(content={"success": True, "message": "Словарь удален"})
    except Exception as e:
        logger.error(msg=f"Error deleting dictionary: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Произошла ошибка во время удаления словаря"}
        )


@api_router.get("/dictionaries", name="get_all_dictionaries")
async def get_all_dicts(db: Session = Depends(get_session)) -> JSONResponse:
    try:
        dictionaries = db.exec(select(Dictionary)).all()

        # Конвертируем в DTO
        dictionaries_dto = [
            DictionaryShortDTO(
                id=dict_dto.id,
                name=dict_dto.name,
                created_at=dict_dto.created_at_local.timestamp(),
                terms_count=len(dict_dto.terms),
                connections_count=len(dict_dto.connections)
            )
            for dict_dto in dictionaries
        ]

        # Сортируем по дате создания (новые сверху)
        dictionaries_dto.sort(key=lambda x: x.created_at, reverse=True)

        return JSONResponse(
            content={
                "success": True,
                "data": [asdict(dto) for dto in dictionaries_dto]
            }
        )
    except Exception as e:
        logger.error(msg=f"Error getting dictionaries: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@api_router.post("/dictionary/{target_dict_id}/merge")
async def merge_dictionaries(
        target_dict_id: int,
        source_dict_data: DictionaryDTO,
        db: Session = Depends(get_session)
) -> JSONResponse:
    try:
        with db.begin():
            target_dict = db.get(Dictionary, target_dict_id)
            if not target_dict:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"success": False, "message": "Целевой словарь не найден"}
                )

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
            term_index = {
                (t.text, t.type, t.phrase_type): t.id
                for t in existing_terms
            }
            old_id_to_new_id = {}

            for term_dto in source_dict_data.phrases:
                term_key = (term_dto.text, term_dto.type, PhraseType.from_value(term_dto.phrase_type))
                if term_key in term_index:
                    old_id_to_new_id[term_dto.id] = term_index[term_key]
                else:
                    t = Term(
                        dictionary_id=target_dict_id,
                        phrase_type=term_dto.phrase_type,
                        text=term_dto.text,
                        type=term_dto.type,
                        tfidf=term_dto.tfidf,
                        hidden=term_dto.hidden
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
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "success": False,
                            "message": f"Неверные ID связей: from={conn.from_id}, to={conn.to_id}"
                        }
                    )
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
                    db.exec(delete(Connection).where(Connection.dictionary_id == source_dict_obj.id))  # type: ignore
                    db.exec(delete(Term).where(Term.dictionary_id == source_dict_obj.id))  # type: ignore
                    db.delete(source_dict_obj)

            return JSONResponse(
                content={"success": True, "message": "Словари успешно объединены"}
            )
    except Exception as e:
        logger.error(msg=f"Error merging dictionaries: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )
