"""Router служебного internal API."""

from fastapi import APIRouter, Depends

from app.api.deps import get_internal_service

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(get_internal_service)],
)


@router.get("/health")
async def internal_health_check() -> dict[str, str]:
    """Проверяет service-to-service авторизацию internal API.

    Выход:
        короткий JSON-ответ без бизнес-данных.
    """
    return {"status": "ok"}
