from typing import Optional

from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.core.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    if not ObjectId.is_valid(user_id):
        raise credentials_exception

    user = await request.app.state.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise credentials_exception

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Inactive user")

    return user


async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme_optional),
):
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id or not ObjectId.is_valid(user_id):
            return None
    except InvalidTokenError:
        return None

    user = await request.app.state.db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("is_active", True):
        return None

    return user


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user