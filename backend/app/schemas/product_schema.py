from pydantic import BaseModel, Field
from typing import List


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=200)
    sku: str = Field(min_length=2, max_length=100)
    description: str = ""
    price_minor: int = Field(gt=0)
    currency: str = Field(pattern="^(KHR|USD)$")
    stock_qty: int = Field(ge=0)
    images: List[str] = []
    category: str = ""
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=200)
    sku: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    price_minor: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, pattern="^(KHR|USD)$")
    stock_qty: int | None = Field(default=None, ge=0)
    images: List[str] | None = None
    category: str | None = None
    is_active: bool | None = None
