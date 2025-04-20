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
from uuid import uuid4

app = FastAPI(title="Анализатор словосочетаний", version="1.0.0")

logging.basicConfig(filename='dev.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# # Монтируем статические файлы (если будут)
app.mount("/public", StaticFiles(directory='public'))

# Инициализация анализатора
phrase_extractor = PhraseExtractor()

# Добавим в начало файла
DICTIONARIES_DIR = "dictionaries"
os.makedirs(DICTIONARIES_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Обработчик GET-запроса для главной страницы"""
    return templates.TemplateResponse("index.html", {"request": request, "result_analysis": []})


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
        file_id = str(uuid4())
        filename = f"{DICTIONARIES_DIR}/analysis_{file_id}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"success": True, "file_id": file_id}
    except Exception as e:
        logger.error(f"Error saving analysis: {str(e)}")
        return {"success": False, "message": str(e)}


@app.get("/create-dictionary/{file_id}")
async def create_dictionary(request: Request, file_id: str):
    """Страница для создания словаря из сохраненного анализа"""
    try:
        filename = f"{DICTIONARIES_DIR}/analysis_{file_id}.json"
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


@app.post("/save-dictionary/{file_id}")
async def save_dictionary(request: Request, file_id: str):
    """Сохранение готового словаря"""
    try:
        data = await request.json()
        filename = f"{DICTIONARIES_DIR}/dictionary_{file_id}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "Словарь сохранен"}
    except Exception as e:
        logger.error(f"Error saving dictionary: {str(e)}")
        return {"success": False, "message": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
