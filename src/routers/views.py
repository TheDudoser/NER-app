from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, UploadFile, Form, File, Depends, Query
from sqlmodel import Session, select
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.services.phrase_service import PhraseService
from src.services.dictionary_service import DictionaryService
from src.services.text_service import TextService
from src.analysis.tfidf import search_phrases_with_tfidf, search_sentences_in_text_with_tfidf
from config import logger, ANALYSIS_DIR
from database import get_session
from src.database.models import Dictionary, PhraseType
from src.analysis.consts import PATTERN_COLOR
from src.analysis.phrase_extractor import PhraseExtractor

views_router = APIRouter(tags=["views"], default_response_class=HTMLResponse)
templates = Jinja2Templates(directory="templates")

# Фильтр для форматирования даты
templates.env.filters["datetimeformat"] = lambda value: value.strftime("%H:%M %d.%m.%Y")
templates.env.globals["PhraseType"] = PhraseType


@views_router.get("/", name="empty_analyze_text", status_code=status.HTTP_200_OK)
async def read_root(request: Request) -> HTMLResponse:
    """Страница анализа текста"""
    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, "pattern_with_colors": PATTERN_COLOR}
    )


@views_router.post("/", name="analyze_text")
async def analyze_text(
        request: Request,
        text: Optional[str] = Form(None),
        file: UploadFile = File(None),
        phrase_extractor: PhraseExtractor = Depends(PhraseExtractor)
) -> HTMLResponse:
    """Обработка и отображение заданного для анализа текста"""
    if not text and not file.filename:
        logger.warning(msg="Text or file is empty")
        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": "Был введён пустой текст или не выбран файл"
        })

    content = text or ""
    if file and file.filename:
        try:
            content = (await file.read()).decode("utf-8")
        except Exception as e:
            logger.error(msg=f"Error reading file: {str(e)}", exc_info=True)
            return templates.TemplateResponse("index.html.jinja", {
                "request": request,
                "pattern_with_colors": PATTERN_COLOR,
                "error": "Произошла ошибка при чтении файла"
            })

    try:
        analysis = phrase_extractor.analyze_text_with_stats(content)

        for phrase in analysis["phrases"]:
            phrase["color"] = PATTERN_COLOR.get(phrase["type"], "black")

        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "result_analysis": analysis,
            "text_analysis": text
        })

    except Exception as e:
        logger.error(msg=f"Analysis error {str(e)}", exc_info=True)
        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": "Произошла неизвестная ошибка при анализе текста"
        })


@views_router.get("/dictionary/create", name="create_dictionary")
async def create_dictionary(
        request: Request,
        analysis_file_id: str,
        phrase_service: PhraseService = Depends(PhraseService)
) -> HTMLResponse:
    """Страница для создания словаря из сохраненных результатов анализа"""
    try:
        filename = f"{ANALYSIS_DIR}/analysis_{analysis_file_id}.json"
        analysis_data = TextService.get_content_file(filename)

        phrases = phrase_service.get_terms_by_analysis_data(analysis_data)

        return templates.TemplateResponse("dictionary.html.jinja", {
            "request": request,
            "phrases": [asdict(phrase) for phrase in phrases],
            "file_id": analysis_file_id,
            "text": analysis_data["text"]
        })
    except Exception as e:
        logger.error(msg=f"Error loading analysis: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html.jinja", {
            "request": request,
            "error": "Произошла ошибка при загрузке файла с результатом анализа"
        })


@views_router.get("/dictionaries", name="list_dictionaries")
async def list_dictionaries(
        request: Request,
        dict_service: DictionaryService = Depends(DictionaryService)
) -> HTMLResponse:
    """Страница со списком всех словарей"""
    try:
        return templates.TemplateResponse("dictionaries_list.html.jinja", {
            "request": request,
            "dictionaries": dict_service.get_short_dictionaries_from_db()
        })
    except Exception as e:
        logger.error(msg=f"Error listing dictionaries: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html.jinja", {
            "request": request,
            "error": "Произошла ошибка при загрузке списка словарей"
        })


@views_router.get("/dictionary/{dictionary_id}/edit", name="edit_dictionary")
async def edit_dictionary(
        request: Request,
        dictionary_id: int,
        dict_service: DictionaryService = Depends(DictionaryService)
) -> HTMLResponse:
    """Страница редактирования словаря"""
    try:
        dictionary = dict_service.get_dict_with_terms_and_connections(dictionary_id)

        if dictionary is None:
            logger.warning(msg=f"Dictionary not found with id {dictionary_id}")
            return templates.TemplateResponse("error.html.jinja", {
                "request": request,
                "error": "Словарь не найден"
            })

        return templates.TemplateResponse("dictionary.html.jinja", {
            "request": request,
            "dictionary": dictionary,
            "phrases": [t for t in dictionary.phrases if t.phrase_type == PhraseType.phrase],
            "terms": [t for t in dictionary.phrases if t.phrase_type == PhraseType.term],
            "synonyms": [t for t in dictionary.phrases if t.phrase_type == PhraseType.synonym],
            "definitions": [t for t in dictionary.phrases if t.phrase_type == PhraseType.definition],
            "connections": [asdict(dto) for dto in dictionary.connections],
            "is_edit_mode": True
        })
    except Exception as e:
        logger.error(msg=f"Error edit dictionary: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html.jinja", {
            "request": request,
            "error": "Произошла ошибка при загрузке словаря"
        })


@views_router.get("/search", name="search")
async def search(
        request: Request,
        query: Optional[str] = Query(None),
        db: Session = Depends(get_session)
) -> HTMLResponse:
    """Страница поиска по словарям"""
    # TODO: Переосмыслить поиск в issue #20
    result = []
    if (query is not None) and (query != ""):
        dictionaries = db.exec(
            select(Dictionary)
            .order_by(Dictionary.updated_at)
            .limit(3)
        ).all()

        for dictionary in dictionaries:
            dict_entry = {
                "dictionary": dictionary,
                "terms": []
            }

            # 1. Ищем все подходящие термины.
            # Вытягивает только не скрытые термины.
            #   Можно было бы сделать это в запросе, но я так и не разобрался как нормально это сделать...
            dict_terms = [t for t in dictionary.terms if t.hidden is False]
            terms_with_sims = search_phrases_with_tfidf(query=query, phrases=dict_terms)

            for term, sim in terms_with_sims:
                term_entry = {
                    "term": term,
                    "similarity": sim,
                    "sentences": []
                }
                # 2. Поиск термина во всех текстах словаря
                for document in dictionary.documents:
                    if document.content == "":
                        continue
                    sentences = search_sentences_in_text_with_tfidf(
                        query=term.text,
                        text=document.content
                    )
                    term_entry["sentences"] = term_entry["sentences"] + sentences
                dict_entry["terms"].append(term_entry)
            result.append(dict_entry)

    return templates.TemplateResponse("search.html.jinja", {
        "request": request,
        "search_results": result
    })
