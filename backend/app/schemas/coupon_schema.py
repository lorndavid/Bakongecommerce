from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    discount_type: str = Field(..., pattern="^(PERCENT|FIXED)$")

    # for PERCENT
    percent_off: Optional[float] = Field(default=None, gt=0, le=100)

    # for FIXED
    amount_off_minor: Optional[int] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, pattern="^(KHR|USD)$")

    min_order_minor: int = Field(default=0, ge=0)
    max_discount_minor: Optional[int] = Field(default=None, ge=0)

    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    usage_limit: Optional[int] = Field(default=None, ge=1)
    is_active: bool = True


class CouponUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=255)
    percent_off: Optional[float] = Field(default=None, gt=0, le=100)
    amount_off_minor: Optional[int] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, pattern="^(KHR|USD)$")
    min_order_minor: Optional[int] = Field(default=None, ge=0)
    max_discount_minor: Optional[int] = Field(default=None, ge=0)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    usage_limit: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None


class CouponValidateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    currency: str = Field(..., pattern="^(KHR|USD)$")
    subtotal_minor: int = Field(..., gt=0)