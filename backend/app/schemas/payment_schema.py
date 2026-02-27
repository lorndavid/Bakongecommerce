# app/schemas/product_schema.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List , Optional , Any


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200)
    sku: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    price_minor: int = Field(..., gt=0)
    currency: str = Field(..., pattern="^(KHR|USD)$")
    stock_qty: int = Field(..., ge=0)
    images: List[str] = []
    category: str = ""
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    slug: str | None = Field(None, min_length=2, max_length=200)
    sku: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None
    price_minor: int | None = Field(None, gt=0)
    currency: str | None = Field(None, pattern="^(KHR|USD)$")
    stock_qty: int | None = Field(None, ge=0)
    images: List[str] | None = None
    category: str | None = None
    is_active: bool | None = None


class PaymentStatusResponse(BaseModel):
    status: str
    payment_id: str
    order_id: str
    amount_minor: int
    currency: str
    deeplink: Optional[str] = None
    qr_image_base64: Optional[str] = None
    expires_at: Optional[str] = None
    payment_info: Optional[Any] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    slug: str
    sku: str
    description: str
    price_minor: int
    currency: str
    stock_qty: int
    images: List[str]
    category: str
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)