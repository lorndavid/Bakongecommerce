# app/api/v1/routes/health.py
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    ping = await request.app.state.db.command("ping")

    return {
        "status": "ok",
        "database": "connected" if ping["ok"] == 1 else "disconnected"
    }