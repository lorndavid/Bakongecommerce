from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError

from app.schemas.coupon_schema import CouponValidateRequest
from app.services.coupon_service import CouponService
from app.utils.serializer import serialize_doc

router = APIRouter()


@router.post("/validate")
async def validate_coupon(payload: CouponValidateRequest, request: Request):
    service = CouponService(request.app.state.db)

    result = await service.validate_coupon(
        code=payload.code,
        currency=payload.currency,
        subtotal_minor=payload.subtotal_minor,
    )

    coupon = result["coupon"]

    return {
        "valid": True,
        "coupon": {
            "id": str(coupon["_id"]),
            "code": coupon["code"],
            "discount_type": coupon["discount_type"],
            "percent_off": coupon.get("percent_off"),
            "amount_off_minor": coupon.get("amount_off_minor"),
            "currency": coupon.get("currency"),
        },
        "discount_minor": result["discount_minor"],
        "grand_total_minor": result["grand_total_minor"],
    }