from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth_schema import TokenResponse
from app.schemas.user_schema import UserRegister
from app.utils.serializer import serialize_doc

router = APIRouter()


def now_utc():
    return datetime.now(timezone.utc)


@router.post("/register")
async def register(payload: UserRegister, request: Request):
    db = request.app.state.db

    existing = await db.users.find_one({
        "$or": [
            {"username": payload.username},
            {"email": payload.email} if payload.email else {"username": "__no_match__"}
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user_doc = {
        "username": payload.username,
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "hashed_password": hash_password(payload.password),
        "role": "customer",
        "is_active": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }

    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    created = await db.users.find_one({"_id": result.inserted_id})
    return {
        "message": "User registered successfully",
        "user": serialize_doc(created),
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    db = request.app.state.db

    user = await db.users.find_one({"username": form_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Inactive user")

    access_token = create_access_token(
        subject=str(user["_id"]),
        role=user["role"],
    )

    return TokenResponse(access_token=access_token)


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return serialize_doc(current_user)