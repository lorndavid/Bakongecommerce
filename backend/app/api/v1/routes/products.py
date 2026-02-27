# app/api/v1/routes/products.py
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.utils.serializer import serialize_doc

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, request: Request):
    db = request.app.state.db

    doc = payload.model_dump()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()

    try:
        result = await db.products.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail="Product slug or SKU already exists"
        )

    created = await db.products.find_one({"_id": result.inserted_id})
    return serialize_doc(created)


@router.get("")
async def list_products(request: Request):
    db = request.app.state.db

    cursor = db.products.find({}).sort("created_at", -1)
    products = await cursor.to_list(length=100)

    return [serialize_doc(product) for product in products]


@router.get("/{slug}")
async def get_product(slug: str, request: Request):
    db = request.app.state.db

    product = await db.products.find_one({"slug": slug})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return serialize_doc(product)


@router.patch("/{product_id}")
async def update_product(product_id: str, payload: ProductUpdate, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product id")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    update_data["updated_at"] = datetime.utcnow()

    try:
        result = await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail="Product slug or SKU already exists"
        )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    updated = await db.products.find_one({"_id": ObjectId(product_id)})
    return serialize_doc(updated)


@router.delete("/{product_id}")
async def delete_product(product_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product id")

    result = await db.products.delete_one({"_id": ObjectId(product_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted successfully"}