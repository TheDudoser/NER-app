from datetime import datetime
import json
import os

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import delete
from sqlmodel import Session
from starlette.requests import Request
import starlette.status as status

from database import get_session
from src.routers.dto import DictionaryDTO
from src.database.models import Dictionary, Term, Connection, PhraseType
from src.input_text_worker.functions import get_json_hash
from config import ANALYSIS_DIR, logger, DICTIONARIES_DIR

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
        # Начинаем транзакцию
        with db.begin():
            # 1) Создаём запись словаря
            dict_obj = Dictionary(name=dict_dto.name, tfidf_range=dict_dto.tfidfRange)
            db.add(dict_obj)
            db.flush()

            # 2) Создаём термины и связи
            phrase_types = {
                "phrases": PhraseType.phrase,
                "terms": PhraseType.term,
                "synonyms": PhraseType.synonym,
                "definitions": PhraseType.definition
            }

            old_id_to_new_id = {}  # {"старый_id": "новый_id_из_БД"}

            # Шаг 1: Создаем все термины
            for key, phrase_type in phrase_types.items():
                term_list = getattr(dict_dto, key, [])  # Получаем список терминов по атрибуту

                for term_dto in term_list:
                    old_id = term_dto.id
                    t = Term(
                        dictionary_id=dict_obj.id,
                        phrase_type=phrase_type,
                        text=term_dto.text,
                        type=term_dto.type,
                        tfidf=term_dto.tfidf,
                        hidden=term_dto.hidden
                    )
                    db.add(t)
                    db.flush()

                    if old_id is not None:
                        old_id_to_new_id[old_id] = t.id

            # Шаг 2: Создаем связи
            for conn in dict_dto.connections:
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
                    dictionary_id=dict_obj.id,
                    from_term_id=from_id,
                    to_term_id=to_id,
                )
                db.add(c)

        return JSONResponse(
            content={"success": True, "dictionary_id": dict_obj.id, "message": "Словарь успешно сохранён"}
        )

    except Exception as e:
        logger.error(f"Ошибка сохранения словаря: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


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

            # Удаляем все связи словаря
            db.exec(delete(Connection).where(Connection.dictionary_id == dict_obj.id))

            # Удаляем все термины словаря
            db.exec(delete(Term).where(Term.dictionary_id == dict_obj.id))

            # 2) Создаём термины и связи
            phrase_types = {
                "phrases": PhraseType.phrase,
                "terms": PhraseType.term,
                "synonyms": PhraseType.synonym,
                "definitions": PhraseType.definition
            }

            old_id_to_new_id = {}  # {"старый_id": "новый_id_из_БД"}

            for key, phrase_type in phrase_types.items():
                term_list = getattr(dict_dto, key, [])  # Получаем список терминов по атрибуту

                for term_dto in term_list:
                    old_id = term_dto.id
                    t = Term(
                        dictionary_id=dict_obj.id,
                        phrase_type=phrase_type,
                        text=term_dto.text,
                        type=term_dto.type,
                        tfidf=term_dto.tfidf,
                        hidden=term_dto.hidden
                    )
                    db.add(t)
                    db.flush()

                    if old_id is not None:
                        old_id_to_new_id[old_id] = t.id

            # Шаг 2: Создаем связи
            for conn in dict_dto.connections:
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
                    dictionary_id=dict_obj.id,
                    from_term_id=from_id,
                    to_term_id=to_id,
                )
                db.add(c)

        return JSONResponse(content={"success": True, "message": "Словарь обновлён"})
    except Exception as e:
        logger.error(msg=f"Error updating dictionary: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


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

            # 2) Удаляем все связи словаря
            db.exec(delete(Connection).where(Connection.dictionary_id == dictionary_id))

            # 3) Удаляем все термины словаря
            db.exec(delete(Term).where(Term.dictionary_id == dictionary_id))

            # 4) Удаляем сам словарь
            db.delete(dict_obj)

        return JSONResponse(content={"success": True, "message": "Словарь удален"})
    except Exception as e:
        logger.error(msg=f"Error deleting dictionary: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Произошла ошибка во время удаления словаря"}
        )
