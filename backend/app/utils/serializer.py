# app/utils/serializer.py
from bson import ObjectId
from datetime import datetime


def serialize_value(value):
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [serialize_value(item) for item in value]

    if isinstance(value, dict):
        return {key: serialize_value(val) for key, val in value.items()}

    return value


def serialize_doc(doc: dict | None):
    if not doc:
        return None

    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
        else:
            result[key] = serialize_value(value)

    return result