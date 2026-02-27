from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


class CheckoutItem(BaseModel):
    product_id: str
    qty: int = Field(..., gt=0)


class CustomerInfo(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=8, max_length=20)


class ShippingAddress(BaseModel):
    country: str = Field(..., min_length=2, max_length=100)
    province_city: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    commune: Optional[str] = Field(default=None, max_length=100)
    village: Optional[str] = Field(default=None, max_length=150)
    street_address: str = Field(..., min_length=3, max_length=255)
    postal_code: Optional[str] = Field(default=None, max_length=30)
    note: Optional[str] = Field(default=None, max_length=500)


class CheckoutRequest(BaseModel):
    items: List[CheckoutItem]
    currency: str = Field(..., pattern="^(KHR|USD)$")
    customer: Optional[CustomerInfo] = None
    shipping_address: ShippingAddress
    coupon_code: Optional[str] = Field(default=None, min_length=3, max_length=50)