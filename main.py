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

app = FastAPI(title="Анализатор словосочетаний", version="1.0.0")

logging.basicConfig(filename='dev.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# # Монтируем статические файлы (если будут)
app.mount("/public", StaticFiles(directory='public'))

# Инициализация анализатора
phrase_extractor = PhraseExtractor()


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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
