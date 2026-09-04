"""Router тренировок."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/trainings", tags=["trainings"])
