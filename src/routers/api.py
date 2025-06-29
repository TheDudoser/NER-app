from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import starlette.status as status

from src.services.exceptions import InvalidConnDictDTO
from src.services.dictionary_service import DictionaryService
from src.models.dto import DictionaryDTO
from config import logger

api_router = APIRouter(prefix="/api", tags=["api"], default_response_class=JSONResponse)


@api_router.post("/dictionary")
async def save_dictionary(
        dict_dto: DictionaryDTO,
        dict_service: DictionaryService = Depends(DictionaryService)
) -> JSONResponse:
    """Сохранение нового словаря"""
    try:
        dict_id = dict_service.save_dictionary_by_dto(dict_dto)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "dictionary_id": dict_id,
                "message": "Словарь успешно сохранён"
            }
        )

    except InvalidConnDictDTO as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error while save dict: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Произошла ошибка при сохранении словаря"
            }
        )


@api_router.patch("/dictionary/{dictionary_id}")
async def update_dictionary(
        dict_dto: DictionaryDTO,
        dictionary_id: int,
        dict_service: DictionaryService = Depends(DictionaryService)
) -> JSONResponse:
    try:
        updated = dict_service.update_dictionary_by_dto(dict_dto, dictionary_id)
        if not updated:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "Словарь не найден"}
            )

        return JSONResponse(content={"success": True, "message": "Словарь обновлён"})
    except InvalidConnDictDTO as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(msg=f"Error updating dictionary: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )


@api_router.delete("/dictionary/{dictionary_id}", name="delete_dictionary")
async def delete_dictionary(
        dictionary_id: int,
        dict_service: DictionaryService = Depends(DictionaryService)
) -> JSONResponse:
    """Удаление словаря"""
    try:
        if not dict_service.delete_dictionary(dictionary_id):
            logger.error(msg="Dictionary not found")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "Удаляемы словарь не был найден"}
            )

        return JSONResponse(content={"success": True, "message": "Словарь удален"})

    except Exception as e:
        logger.error(msg=f"Error deleting dictionary: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Произошла ошибка во время удаления словаря"}
        )


@api_router.get("/dictionaries", name="get_all_dictionaries")
async def get_all_dicts(dict_service: DictionaryService = Depends(DictionaryService)) -> JSONResponse:
    """Получение списка словарей с краткой сводкой для каждого"""
    try:
        dictionaries_dto = dict_service.get_all_short_dictionaries_from_db(True)

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
        dict_service: DictionaryService = Depends(DictionaryService)
) -> JSONResponse:
    """Слияние двух словарей"""
    try:
        merged = dict_service.merge_dictionaries(source_dict_data, target_dict_id)
        if not merged:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "Целевой словарь не найден"}
            )

        return JSONResponse(
            content={"success": True, "message": "Словари успешно объединены"}
        )
    except InvalidConnDictDTO as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(msg=f"Error merging dictionaries: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": str(e)}
        )
