"""Router технических проверок API."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Проверяет, что API-процесс запущен и отвечает на HTTP-запросы.

    Returns:
        короткий JSON-ответ без бизнес-данных и персональной информации.
    """
    return {"status": "ok"}
