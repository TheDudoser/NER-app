from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import src.database.models as models
from src.routers.views import views_router
from src.routers.api import api_router
import uvicorn

from config import version


@asynccontextmanager
async def lifespan(appType: FastAPI):
    # Код, выполняемый при старте приложения
    models.create_all()
    yield
    # Код, выполняемый при завершении приложения (если нужно)
    # Например: models.close_all()


app = FastAPI(title="Сервис разметки текстовых документов", version=version, lifespan=lifespan)

# Монтируем статические файлы
app.mount("/public", StaticFiles(directory='public'))

app.include_router(api_router)
app.include_router(views_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
