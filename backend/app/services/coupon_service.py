from datetime import datetime
from fastapi import HTTPException


class CouponService:
    def __init__(self, db):
        self.db = db

    def _now(self):
        # Keep service timestamps naive UTC to match BSON datetimes returned by PyMongo.
        return datetime.utcnow()

    def normalize_code(self, code: str) -> str:
        return code.strip().upper()

    async def get_coupon_by_code(self, code: str):
        normalized = self.normalize_code(code)
        return await self.db.coupons.find_one({"code": normalized})

    async def validate_coupon(self, code: str, currency: str, subtotal_minor: int):
        coupon = await self.get_coupon_by_code(code)

        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")

        now = self._now()

        if not coupon.get("is_active", True):
            raise HTTPException(status_code=400, detail="Coupon is inactive")

        starts_at = coupon.get("starts_at")
        ends_at = coupon.get("ends_at")

        if starts_at and now < starts_at:
            raise HTTPException(status_code=400, detail="Coupon is not active yet")

        if ends_at and now > ends_at:
            raise HTTPException(status_code=400, detail="Coupon has expired")

        usage_limit = coupon.get("usage_limit")
        used_count = coupon.get("used_count", 0)
        if usage_limit is not None and used_count >= usage_limit:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

        min_order_minor = coupon.get("min_order_minor", 0)
        if subtotal_minor < min_order_minor:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum order is {min_order_minor}"
            )

        discount_type = coupon["discount_type"]
        discount_minor = 0

        if discount_type == "PERCENT":
            percent_off = coupon.get("percent_off") or 0
            discount_minor = int(round(subtotal_minor * (percent_off / 100.0)))

            max_discount_minor = coupon.get("max_discount_minor")
            if max_discount_minor is not None:
                discount_minor = min(discount_minor, max_discount_minor)

        elif discount_type == "FIXED":
            coupon_currency = coupon.get("currency")
            if coupon_currency and coupon_currency != currency:
                raise HTTPException(status_code=400, detail="Coupon currency mismatch")

            discount_minor = coupon.get("amount_off_minor") or 0

        else:
            raise HTTPException(status_code=400, detail="Invalid coupon type")

        if discount_minor <= 0:
            raise HTTPException(status_code=400, detail="Coupon discount is invalid")

        if discount_minor > subtotal_minor:
            discount_minor = subtotal_minor

        return {
            "coupon": coupon,
            "discount_minor": discount_minor,
            "grand_total_minor": subtotal_minor - discount_minor,
        }
