"""Router экспорта данных."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/export", tags=["export"])
