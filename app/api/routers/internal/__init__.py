"""Пакет роутеров служебного internal API."""

from fastapi import APIRouter, Depends

from app.api.deps import get_internal_service

from . import admin, exercises, export, groups, health, ratings, statistics, trainings, users

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(get_internal_service)],
)

router.include_router(health.router)
router.include_router(admin.router)
router.include_router(users.router)
router.include_router(exercises.router)
router.include_router(trainings.router)
router.include_router(groups.router)
router.include_router(ratings.router)
router.include_router(statistics.router)
router.include_router(export.router)
