"""Router авторизации."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])
