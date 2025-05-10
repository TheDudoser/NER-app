import json
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, Form, File
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from config import logger, ANALYSIS_DIR, DICTIONARIES_DIR
from src.analysis.consts import PATTERN_COLOR
from src.analysis.phrase_extractor import PhraseExtractor

views_router = APIRouter(tags=["views"])
templates = Jinja2Templates(directory="templates")
phrase_extractor = PhraseExtractor()

# Фильтр для форматирования даты
templates.env.filters["datetimeformat"] = lambda value: datetime.fromtimestamp(value).strftime('%d.%m.%Y %H:%M')


@views_router.get("/")
async def read_root(request: Request) -> HTMLResponse:
    """Страница анализа текста"""
    return templates.TemplateResponse("index.html", {"request": request, "pattern_with_colors": PATTERN_COLOR})


@views_router.post("/")
async def analyze_text(
        request: Request,
        text: Optional[str] = Form(None),
        file: UploadFile = File(None)
) -> HTMLResponse:
    """Обработка и отображение заданного для анализа текста"""
    if not text and not file.filename:
        logger.warning(msg="Text or file is empty")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": "Был введён пустой текст или не выбран файл"
        })

    content = text or ""
    if file and file.filename:
        try:
            file_content = (await file.read()).decode("utf-8")
            content = f"{content}\n{file_content}" if content else file_content
        except Exception as e:
            logger.error(msg=f"Error reading file: {str(e)}", exc_info=True)
            return templates.TemplateResponse("index.html", {
                "request": request,
                "pattern_with_colors": PATTERN_COLOR,
                "error": "Произошла ошибка при чтении файла"
            })

    try:
        analysis = phrase_extractor.analyze_text_with_stats(content)

        for phrase in analysis['phrases']:
            phrase['color'] = PATTERN_COLOR.get(phrase['pattern_type'], 'black')

        return templates.TemplateResponse("index.html", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "result_analysis": analysis,
            "text_analysis": text
        })

    except Exception as e:
        logger.error(msg=f"Analysis error {str(e)}", exc_info=True)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": "Произошла неизвестная ошибка при анализе текста"
        })


@views_router.get("/dictionary/create")
async def create_dictionary(request: Request, analysis_file_id: str) -> HTMLResponse:
    """Страница для создания словаря из сохраненных ранее результатов анализа"""
    try:
        filename = f"{ANALYSIS_DIR}/analysis_{analysis_file_id}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # Преобразуем данные для шаблона
        phrases = [
            {
                "id": idx,
                "phrase": phrase["phrase"],
                "pattern_type": phrase["pattern_type"],
                "tfidf": phrase["tfidf_score"]
            }
            for idx, phrase in enumerate(analysis_data["phrases"])
        ]

        # 1) Добавляем лемму главного существительного
        for item in phrases:
            item['head_noun'] = phrase_extractor.get_head_noun_lemma(item['phrase'])

        # 2) Сортируем: сначала по head_noun, потом по тексту для стабильности
        phrases.sort(key=lambda x: (x['head_noun'], x['phrase']))

        return templates.TemplateResponse("dictionary.html", {
            "request": request,
            "phrases": phrases,
            "file_id": analysis_file_id
        })
    except Exception as e:
        logger.error(msg=f"Error loading analysis: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Произошла ошибка при загрузке файла с результатом анализа"
        })


@views_router.get("/dictionaries")
async def list_dictionaries(request: Request) -> HTMLResponse:
    """Страница со списком всех словарей"""
    try:
        dictionaries = []
        for filename in os.listdir(DICTIONARIES_DIR):
            if filename.startswith("dictionary_") and filename.endswith(".json"):
                filepath = os.path.join(DICTIONARIES_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dictionaries.append({
                        'id': filename.replace("dictionary_", "").replace(".json", ""),
                        'name': data.get('name', 'Без названия'),
                        'created_at': os.path.getctime(filepath),
                        'terms_count': len(data.get('terms', [])),
                        'connections_count': len(data.get('connections', []))
                    })

        # Сортируем словари по дате создания (сначала новые)
        dictionaries.sort(key=lambda x: x['created_at'], reverse=True)

        return templates.TemplateResponse("dictionaries_list.html", {
            "request": request,
            "dictionaries": dictionaries
        })
    except Exception as e:
        logger.error(msg=f"Error listing dictionaries: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Произошла ошибка при загрузке списка словарей"
        })


@views_router.get("/dictionary/{dictionary_id}/edit")
async def edit_dictionary(request: Request, dictionary_id: str) -> HTMLResponse:
    try:
        filename = f"{DICTIONARIES_DIR}/dictionary_{dictionary_id}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            dictionary_data = json.load(f)

        # 1. Извлекаем и обогащаем термины
        terms = dictionary_data.get('terms', [])
        for item in terms:
            item['phrase'] = item['text']
            item['pattern_type'] = item['type']
            item['head_noun'] = phrase_extractor.get_head_noun_lemma(item['phrase'])

        # 2. Сортируем термины по head_noun и тексту фразы
        terms.sort(key=lambda x: (x['head_noun'], x['phrase']))

        # 3. Записываем обратно в dictionary_data
        dictionary_data['terms'] = terms

        return templates.TemplateResponse("dictionary.html", {
            "request": request,
            "dictionary_name": dictionary_data.get('name', ''),
            "dictionary_data": dictionary_data,
            "file_id": dictionary_id,
            "is_edit_mode": True,
            "tfidfRange": dictionary_data['tfidfRange']
        })
    except Exception as e:
        logger.error(msg=f"Error loading dictionary: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Произошла ошибка при загрузке словаря"
        })


@views_router.get("/search")
async def search(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("search.html", {
        "request": request
    })
