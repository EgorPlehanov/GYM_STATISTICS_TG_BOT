"""Health endpoints служебного internal API."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def internal_health_check() -> dict[str, str]:
    """Проверяет service-to-service авторизацию internal API.

    Returns:
        короткий JSON-ответ без бизнес-данных.
    """
    return {"status": "ok"}
