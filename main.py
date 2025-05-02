from datetime import datetime
import time

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form
from src.analysis.phrase_extractor import PhraseExtractor
from src.analysis.consts import PATTERN_COLOR
import uvicorn
from typing import Optional
import logging

import json
import os

from src.input_text_worker.functions import get_json_hash

app = FastAPI(title="Анализатор словосочетаний", version="1.0.0")

logging.basicConfig(filename='dev.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# # Монтируем статические файлы (если будут)
app.mount("/public", StaticFiles(directory='public'))

# Инициализация анализатора
phrase_extractor = PhraseExtractor()

# Создаём папки для хранения промежуточных данных
ANALYSIS_DIR = "analysis"
os.makedirs(ANALYSIS_DIR, exist_ok=True)

DICTIONARIES_DIR = "dictionaries"
os.makedirs(DICTIONARIES_DIR, exist_ok=True)

# Добавим фильтр для форматирования даты
templates.env.filters["datetimeformat"] = lambda value: datetime.fromtimestamp(value).strftime('%d.%m.%Y %H:%M')


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Обработчик GET-запроса для главной страницы"""
    return templates.TemplateResponse("index.html", {"request": request, "pattern_with_colors": PATTERN_COLOR})


@app.post("/")
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


@app.post("/save-analysis")
async def save_analysis(request: Request):
    """Сохранение результатов анализа для последующего редактирования"""
    try:
        data = await request.json()
        # Ищем хэш текста чтобы каждый раз не сохранять новый файл
        file_hash = get_json_hash(data)

        filename = f"{ANALYSIS_DIR}/analysis_{file_hash}.json"

        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return {"success": True, "file_id": file_hash}
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")
        return {"success": False, "message": str(e)}


@app.get("/create-dictionary/{file_id}")
async def create_dictionary(request: Request, file_id: str):
    """Страница для создания словаря из сохраненного анализа"""
    try:
        filename = f"{ANALYSIS_DIR}/analysis_{file_id}.json"
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
            "file_id": file_id
        })
    except Exception as e:
        logger.error(f"Error loading analysis: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки анализа: {str(e)}"
        })


@app.post("/save-dictionary")
async def save_dictionary(request: Request):
    """Сохранение готового словаря"""
    try:
        data = await request.json()
        utc = time.gmtime(time.time())
        filename = f"{DICTIONARIES_DIR}/dictionary_{int(time.mktime(utc))}.json"

        now = datetime.now().isoformat()
        data['createdAt'] = now

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Словарь сохранен"}
    except Exception as e:
        logger.error(f"Error saving dictionary: {str(e)}")
        return {"success": False, "message": str(e)}


@app.patch("/update-dictionary/{file_id}")
async def update_dictionary(request: Request, file_id: str):
    try:
        data = await request.json()
        filename = f"{DICTIONARIES_DIR}/dictionary_{file_id}.json"
        # Читаем старый словарь, чтобы не потерять createdAt
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            data['createdAt'] = old_data.get('createdAt')
        data['updatedAt'] = datetime.now().isoformat()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True, "message": "Словарь обновлён"}
    except Exception as e:
        logger.error(f"Error updating dictionary: {str(e)}")
        return {"success": False, "message": str(e)}


@app.get("/dictionaries")
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


@app.delete("/delete-dictionary/{dictionary_id}")
async def delete_dictionary(dictionary_id: str):
    """Удаление словаря"""
    try:
        filename = f"{DICTIONARIES_DIR}/dictionary_{dictionary_id}.json"
        if os.path.exists(filename):
            os.remove(filename)
            return {"success": True, "message": "Словарь удален"}
        return {"success": False, "message": "Файл не найден"}
    except Exception as e:
        logger.error(f"Error deleting dictionary: {str(e)}")
        return {"success": False, "message": str(e)}


@app.get("/edit-dictionary/{dictionary_id}")
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


@app.get("/search")
async def search(request: Request):
    return templates.TemplateResponse("search.html", {
        "request": request
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
