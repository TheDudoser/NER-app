from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel

from database import engine
import src.database.models as models
from src.routers.views import views_router
from src.routers.api import api_router
import uvicorn

from config import version

app = FastAPI(title="Сервис разметки текстовых документов", version=version)


@app.on_event("startup")
def on_startup():
    models.create_all()


# Монтируем статические файлы
app.mount("/public", StaticFiles(directory='public'))

app.include_router(api_router)
app.include_router(views_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
