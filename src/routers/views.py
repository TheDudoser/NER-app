from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, UploadFile, Form, File, Depends, Query
from sqlmodel import Session, select
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.services.search_service import SearchService
from src.services.phrase_service import PhraseService
from src.services.dictionary_service import DictionaryService
from src.services.text_service import TextService
from config import logger
from database import get_session
from src.database.models import PhraseType, Document, AnalysisResult
from src.analysis.consts import PATTERN_COLOR, TYPE_COLOR
from src.analysis.analyser import Analyser

views_router = APIRouter(tags=["views"], default_response_class=HTMLResponse)
templates = Jinja2Templates(directory="templates")

# Фильтр для форматирования даты
templates.env.filters["datetimeformat"] = lambda value: value.strftime("%H:%M %d.%m.%Y")
templates.env.globals["PhraseType"] = PhraseType
templates.env.globals["TYPE_COLOR"] = TYPE_COLOR


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
        analyser: Analyser = Depends(Analyser),
        db: Session = Depends(get_session),
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
        hash_key = TextService.get_text_content_hash(content)
        exist_document = db.exec(select(Document).where(Document.hash_key == hash_key)).one_or_none()
        if not exist_document:
            document = Document(
                hash_key=hash_key,
                content=content
            )
            db.add(document)
            db.flush()

            extracted_analysis = analyser.analyze_text_with_stats(content)
            for phrase in extracted_analysis["phrases"]:
                phrase["color"] = PATTERN_COLOR.get(phrase["type"], "black")

            # TODO: Возможно, имеет смысл сохранять сразу в базу ещё и vectorizer, sentence_vectors
            analysis_result = AnalysisResult(
                document_id=document.id,
                content=extracted_analysis,
                document_batches=Analyser.get_sentences_by_text(content)
            )
            db.add(analysis_result)

            db.commit()
        else:
            analysis_result = db.exec(
                select(AnalysisResult).where(AnalysisResult.document_id == exist_document.id)).one_or_none()

        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "analysis_result": analysis_result,
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
        analysis_result_id: int,
        phrase_service: PhraseService = Depends(PhraseService),
        db: Session = Depends(get_session),
) -> HTMLResponse:
    """Страница для создания словаря из сохраненных результатов анализа"""
    try:
        analysis_result = db.exec(select(AnalysisResult).where(AnalysisResult.id == analysis_result_id)).one_or_none()
        phrases = phrase_service.get_terms_by_analysis_data(analysis_result.content)

        return templates.TemplateResponse("dictionary.html.jinja", {
            "request": request,
            "phrases": [asdict(phrase) for phrase in phrases],
            "analysis_result_id": analysis_result_id
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
            "dictionaries": dict_service.get_all_short_dictionaries_from_db()
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
        db: Session = Depends(get_session),
        search_service: SearchService = Depends(SearchService),
) -> HTMLResponse:
    """Страница поиска по словарям"""
    return templates.TemplateResponse("search.html.jinja", {
        "request": request,
        "search_results": search_service.search_by_query(db, query)
    })
