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


@views_router.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """Обработчик GET-запроса для главной страницы"""
    return templates.TemplateResponse("index.html", {"request": request, "pattern_with_colors": PATTERN_COLOR})


@views_router.post("/")
async def analyze_text(
        request: Request,
        text: Optional[str] = Form(None),
        file: UploadFile = File(None)  # Изменено на File(None) вместо None
):
    """Обработчик POST-запроса для анализа текста"""
    if not text and not file:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
        })

    content = text or ""
    if file and file.filename:  # Проверяем, что файл был загружен
        try:
            file_content = (await file.read()).decode("utf-8")
            content = f"{content}\n{file_content}" if content else file_content
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return templates.TemplateResponse("index.html", {
                "request": request,
                "pattern_with_colors": PATTERN_COLOR,
                "error": f"Ошибка чтения файла: {str(e)}"
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
        logger.error(f"Analysis error: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": f"Ошибка при анализе текста: {str(e)}"
        })


@views_router.get("/dictionary/create")
async def create_dictionary(request: Request, analysis_file_id: str):
    """Страница для создания словаря из сохраненного анализа"""
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
        logger.error(f"Error loading analysis: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки анализа: {str(e)}"
        })


@views_router.get("/dictionaries")
async def list_dictionaries(request: Request):
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

        # Сортируем по дате создания (новые сначала)
        dictionaries.sort(key=lambda x: x['created_at'], reverse=True)

        return templates.TemplateResponse("dictionaries_list.html", {
            "request": request,
            "dictionaries": dictionaries
        })
    except Exception as e:
        logger.error(f"Error listing dictionaries: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка при загрузке списка словарей: {str(e)}"
        })


@views_router.get("/dictionary/{dictionary_id}/edit")
async def edit_dictionary(request: Request, dictionary_id: str):
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
            "is_edit_mode": True
        })
    except Exception as e:
        logger.error(f"Error loading dictionary: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки словаря: {e}"
        })


@views_router.get("/search")
async def search(request: Request):
    return templates.TemplateResponse("search.html", {
        "request": request
    })
