from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form
from src.analysis.phrase_extractor import PhraseExtractor
import uvicorn
from typing import Optional
import logging

app = FastAPI(title="Анализатор словосочетаний", version="1.0.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# # Монтируем статические файлы (если будут)
app.mount("/public", StaticFiles(directory='public'))

# Инициализация анализатора
phrase_extractor = PhraseExtractor()

# Цветовая схема для веб-интерфейса
COLOR_MAPPING = {
    'однословное': 'blue',
    'адъективное': 'green',
    'генитивное': 'yellow',
    'адвербиальное': 'magenta',
    'субстантивное_с_предлогом': 'cyan',
    'адъективное_многословное': 'lightgreen',
    'генитивное_многословное': 'lightyellow',
    'адъективно-генитивное': 'lightblue',
    'генитивно-адъективное': 'lightpurple',
    'адъективное_с_предлогом': 'lightcyan',
    'генитивное_с_предлогом': 'lightred',
    'адвербиальное_сочетание': 'white'
}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница с формой ввода текста"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/analyze")
async def analyze_text(text: Optional[str] = Form(None), file: Optional[UploadFile] = File(None)):
    """
    Анализирует текст или загруженный файл, возвращает JSON с результатами

    Параметры:
    - text: текст для анализа (опционально)
    - file: текстовый файл для анализа (опционально)
    """
    if not text and not file:
        return JSONResponse(
            {"error": "Необходимо предоставить текст или файл для анализа"},
            status_code=400
        )

    content = text or ""
    try:
        file_content = (await file.read()).decode("utf-8")
        content = f"{content}\n{file_content}" if content else file_content
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return JSONResponse(
            {"error": f"Ошибка чтения файла: {str(e)}"},
            status_code=400,
        )

    try:
        analysis = phrase_extractor.analyze_text_with_stats(content)

        # Добавляем цвета для веб-интерфейса
        for phrase in analysis['phrases']:
            phrase['color'] = COLOR_MAPPING.get(phrase['pattern_type'], 'black')

        return analysis

    except Exception as e:
        return JSONResponse(
            {"error": f"Ошибка при анализе текста: {str(e)}"},
            status_code=500
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
