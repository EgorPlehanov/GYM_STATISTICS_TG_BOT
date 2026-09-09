"""Пакет роутеров служебного internal API."""

from fastapi import APIRouter, Depends

from app.api.deps import get_internal_service

from . import exercises, groups, health, trainings, users

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(get_internal_service)],
)

router.include_router(health.router)
router.include_router(users.router)
router.include_router(exercises.router)
router.include_router(trainings.router)
router.include_router(groups.router)
