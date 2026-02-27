# app/db/mongodb.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.db.indexes import create_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(settings.mongodb_url)

    try:
        db = client[settings.mongodb_db]

        # verify connection
        ping = await db.command("ping")
        if int(ping["ok"]) != 1:
            raise RuntimeError("MongoDB ping failed")

        # save shared objects on app state
        app.state.mongodb_client = client
        app.state.db = db

        # create indexes once at startup
        await create_indexes(db)

        yield

    except PyMongoError as exc:
        raise RuntimeError(f"MongoDB connection error: {exc}") from exc

    finally:
        await client.close()