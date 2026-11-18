from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from repositories.moderation import ModerationRepository
from services.moderation import ModerationService

router = APIRouter()

repository = ModerationRepository()
service = ModerationService(repository)


class PredictRequest(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str = Field(min_length=1)
    description: str
    category: int
    images_qty: int = Field(ge=0)


@router.post("/predict", response_model=bool)
async def predict(request: PredictRequest) -> bool:
    try:
        return service.predict(
            is_verified_seller=request.is_verified_seller,
            images_qty=request.images_qty,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from exc
