"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, exercises, export, health, internal, statistics, trainings, users
from app.core.config import config


def create_app() -> FastAPI:
    """Создает FastAPI-приложение и подключает базовые API-роутеры.

    Выход:
        настроенный объект `FastAPI`, который используется `uvicorn` при запуске API-сервиса.
    """
    application = FastAPI(
        title=config.APP_NAME,
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(exercises.router)
    application.include_router(trainings.router)
    application.include_router(statistics.router)
    application.include_router(export.router)
    application.include_router(internal.router)

    return application


app = create_app()
