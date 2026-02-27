from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    full_name: str = Field(..., min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=8, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)


class UserPublic(BaseModel):
    id: str
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None