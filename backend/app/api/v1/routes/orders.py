from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.deps import get_current_user, get_current_user_optional
from app.schemas.order_schema import CheckoutRequest
from app.services.order_service import OrderService
from app.utils.serializer import serialize_doc

router = APIRouter()


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    request: Request,
    current_user=Depends(get_current_user_optional),
):
    service = OrderService(request.app.state.db)

    order, payment = await service.checkout(
        items=[item.model_dump() for item in payload.items],
        currency=payload.currency,
        customer=payload.customer.model_dump() if payload.customer else None,
        shipping_address=payload.shipping_address.model_dump(),
        coupon_code=payload.coupon_code,
        current_user=current_user,
    )

    return {
        "message": "Checkout created successfully",
        "order": serialize_doc(order),
        "payment": serialize_doc(payment),
    }


@router.get("/my-orders/list")
async def my_orders(
    request: Request,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db

    cursor = db.orders.find({
        "user_id": current_user["_id"]
    }).sort("created_at", -1)

    orders = await cursor.to_list(length=100)

    return {
        "items": [serialize_doc(order) for order in orders]
    }


@router.get("/my-orders/{order_id}")
async def my_order_detail(
    order_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db

    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order id")

    order = await db.orders.find_one({
        "_id": ObjectId(order_id),
        "user_id": current_user["_id"],
    })
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = None
    if order.get("current_payment_id"):
        payment = await db.payments.find_one({"_id": order["current_payment_id"]})

    return {
        "order": serialize_doc(order),
        "payment": serialize_doc(payment) if payment else None,
    }


@router.get("/{order_id}")
async def get_order(order_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order id")

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return serialize_doc(order)