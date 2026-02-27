
from pydantic import BaseModel, Field
from datetime import datetime


class TimestampMixin(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None