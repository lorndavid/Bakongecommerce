from datetime import datetime, timezone, timedelta
from app.services.payment_service import PaymentService

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pymongo.errors import DuplicateKeyError

from app.core.deps import require_admin
from app.schemas.coupon_schema import CouponCreate, CouponUpdate
from app.utils.serializer import serialize_doc

router = APIRouter(
    dependencies=[Depends(require_admin)]
)


def now_utc():
    return datetime.now(timezone.utc)


# ---------------------------
# Dashboard summary
# ---------------------------

@router.post("/reconciliation/run")
async def admin_run_reconciliation(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
):
    service = PaymentService(request.app.state.db)
    result = await service.reconcile_pending_payments(limit=limit)
    return result


@router.post("/payments/{payment_id}/retry-telegram")
async def admin_retry_telegram(payment_id: str, request: Request):
    service = PaymentService(request.app.state.db)
    result = await service.retry_telegram_by_payment_id(payment_id)

    if result.get("payment"):
        result["payment"] = serialize_doc(result["payment"])

    return result


@router.get("/payments/telegram-failed")
async def admin_list_telegram_failed(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    db = request.app.state.db

    query = {
        "status": "PAID",
        "telegram_last_error": {"$exists": True, "$ne": None}
    }

    cursor = db.payments.find(query).sort("updated_at", -1).skip(skip).limit(limit)
    payments = await cursor.to_list(length=limit)
    total = await db.payments.count_documents(query)

    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "items": [serialize_doc(payment) for payment in payments]
    }

@router.get("/dashboard/stats")
async def admin_dashboard_stats(request: Request):
    db = request.app.state.db

    now = now_utc()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    total_orders = await db.orders.count_documents({})
    paid_orders = await db.orders.count_documents({"status": "PAID"})
    pending_orders = await db.orders.count_documents({"status": "AWAITING_PAYMENT"})
    expired_orders = await db.orders.count_documents({"status": "EXPIRED"})

    total_payments = await db.payments.count_documents({})
    pending_payments = await db.payments.count_documents({"status": "PENDING"})
    paid_payments = await db.payments.count_documents({"status": "PAID"})
    failed_payments = await db.payments.count_documents({"status": "FAILED"})

    orders_24h = await db.orders.count_documents({"created_at": {"$gte": last_24h}})
    orders_7d = await db.orders.count_documents({"created_at": {"$gte": last_7d}})

    paid_orders_docs = await db.orders.find({"status": "PAID"}).to_list(length=1000)

    total_revenue_khr = 0
    total_revenue_usd = 0
    total_discount_khr = 0
    total_discount_usd = 0

    for order in paid_orders_docs:
        amount = order.get("totals", {}).get("grand_total_minor", 0)
        discount = order.get("totals", {}).get("discount_minor", 0)
        currency = order.get("currency")

        if currency == "KHR":
            total_revenue_khr += amount
            total_discount_khr += discount
        elif currency == "USD":
            total_revenue_usd += amount
            total_discount_usd += discount

    return {
        "orders": {
            "total": total_orders,
            "paid": paid_orders,
            "pending": pending_orders,
            "expired": expired_orders,
            "last_24h": orders_24h,
            "last_7d": orders_7d,
        },
        "payments": {
            "total": total_payments,
            "pending": pending_payments,
            "paid": paid_payments,
            "failed": failed_payments,
        },
        "revenue": {
            "KHR": total_revenue_khr,
            "USD": total_revenue_usd,
        },
        "discounts": {
            "KHR": total_discount_khr,
            "USD": total_discount_usd,
        }
    }


# ---------------------------
# Sales analytics
# ---------------------------

@router.get("/analytics/sales-by-day")
async def analytics_sales_by_day(
    request: Request,
    days: int = Query(default=7, ge=1, le=365),
    currency: str | None = Query(default=None),
):
    db = request.app.state.db

    since = now_utc() - timedelta(days=days)

    match_stage = {
        "status": "PAID",
        "created_at": {"$gte": since},
    }
    if currency:
        match_stage["currency"] = currency

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "day": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                        }
                    },
                    "currency": "$currency",
                },
                "orders_count": {"$sum": 1},
                "revenue_minor": {"$sum": "$totals.grand_total_minor"},
                "discount_minor": {"$sum": "$totals.discount_minor"},
            }
        },
        {"$sort": {"_id.day": 1}}
    ]

    cursor = db.orders.aggregate(pipeline)
    rows = await cursor.to_list(None)

    return {
        "days": days,
        "currency_filter": currency,
        "items": [
            {
                "day": row["_id"]["day"],
                "currency": row["_id"]["currency"],
                "orders_count": row["orders_count"],
                "revenue_minor": row["revenue_minor"],
                "discount_minor": row["discount_minor"],
            }
            for row in rows
        ]
    }


@router.get("/analytics/top-products")
async def analytics_top_products(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
):
    db = request.app.state.db

    since = now_utc() - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "status": "PAID",
                "created_at": {"$gte": since},
            }
        },
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": {
                    "product_id": "$items.product_id",
                    "sku": "$items.sku_snapshot",
                    "name": "$items.name_snapshot",
                },
                "qty_sold": {"$sum": "$items.qty"},
                "revenue_minor": {"$sum": "$items.subtotal_minor"},
            }
        },
        {"$sort": {"qty_sold": -1, "revenue_minor": -1}},
        {"$limit": limit},
    ]

    cursor = db.orders.aggregate(pipeline)
    rows = await cursor.to_list(None)

    return {
        "days": days,
        "items": [
            {
                "product_id": str(row["_id"]["product_id"]),
                "sku": row["_id"]["sku"],
                "name": row["_id"]["name"],
                "qty_sold": row["qty_sold"],
                "revenue_minor": row["revenue_minor"],
            }
            for row in rows
        ]
    }


@router.get("/analytics/coupon-performance")
async def analytics_coupon_performance(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
):
    db = request.app.state.db

    since = now_utc() - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "status": "PAID",
                "created_at": {"$gte": since},
                "coupon.code": {"$exists": True},
            }
        },
        {
            "$group": {
                "_id": {
                    "code": "$coupon.code",
                    "currency": "$currency",
                },
                "orders_count": {"$sum": 1},
                "discount_minor": {"$sum": "$totals.discount_minor"},
                "revenue_minor": {"$sum": "$totals.grand_total_minor"},
            }
        },
        {"$sort": {"discount_minor": -1, "orders_count": -1}},
    ]

    cursor = db.orders.aggregate(pipeline)
    rows = await cursor.to_list(None)

    return {
        "days": days,
        "items": [
            {
                "code": row["_id"]["code"],
                "currency": row["_id"]["currency"],
                "orders_count": row["orders_count"],
                "discount_minor": row["discount_minor"],
                "revenue_minor": row["revenue_minor"],
            }
            for row in rows
        ]
    }


# ---------------------------
# Coupon admin CRUD
# ---------------------------

@router.post("/coupons", status_code=status.HTTP_201_CREATED)
async def admin_create_coupon(payload: CouponCreate, request: Request):
    db = request.app.state.db

    code = payload.code.strip().upper()
    now = now_utc()

    if payload.discount_type == "PERCENT":
        if payload.percent_off is None:
            raise HTTPException(status_code=400, detail="percent_off is required")
    elif payload.discount_type == "FIXED":
        if payload.amount_off_minor is None or payload.currency is None:
            raise HTTPException(
                status_code=400,
                detail="amount_off_minor and currency are required"
            )

    doc = payload.model_dump()
    doc["code"] = code
    doc["used_count"] = 0
    doc["created_at"] = now
    doc["updated_at"] = now

    try:
        result = await db.coupons.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    created = await db.coupons.find_one({"_id": result.inserted_id})
    return serialize_doc(created)


@router.get("/coupons")
async def admin_list_coupons(
    request: Request,
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    db = request.app.state.db

    query = {}
    if is_active is not None:
        query["is_active"] = is_active

    cursor = db.coupons.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await db.coupons.count_documents(query)

    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "items": [serialize_doc(item) for item in items]
    }


@router.get("/coupons/{coupon_id}")
async def admin_get_coupon(coupon_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(coupon_id):
        raise HTTPException(status_code=400, detail="Invalid coupon id")

    coupon = await db.coupons.find_one({"_id": ObjectId(coupon_id)})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    return serialize_doc(coupon)


@router.patch("/coupons/{coupon_id}")
async def admin_update_coupon(
    coupon_id: str,
    payload: CouponUpdate,
    request: Request,
):
    db = request.app.state.db

    if not ObjectId.is_valid(coupon_id):
        raise HTTPException(status_code=400, detail="Invalid coupon id")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    update_data["updated_at"] = now_utc()

    result = await db.coupons.update_one(
        {"_id": ObjectId(coupon_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")

    updated = await db.coupons.find_one({"_id": ObjectId(coupon_id)})
    return serialize_doc(updated)


@router.post("/coupons/{coupon_id}/toggle")
async def admin_toggle_coupon(coupon_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(coupon_id):
        raise HTTPException(status_code=400, detail="Invalid coupon id")

    coupon = await db.coupons.find_one({"_id": ObjectId(coupon_id)})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    new_value = not coupon.get("is_active", True)

    await db.coupons.update_one(
        {"_id": coupon["_id"]},
        {"$set": {"is_active": new_value, "updated_at": now_utc()}}
    )

    updated = await db.coupons.find_one({"_id": coupon["_id"]})
    return serialize_doc(updated)


# ---------------------------
# Existing admin routes
# ---------------------------

@router.get("/dashboard/recent-orders")
async def admin_recent_orders(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
):
    db = request.app.state.db

    cursor = db.orders.find({}).sort("created_at", -1).limit(limit)
    orders = await cursor.to_list(length=limit)

    return {"items": [serialize_doc(order) for order in orders]}


@router.get("/dashboard/recent-payments")
async def admin_recent_payments(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
):
    db = request.app.state.db

    cursor = db.payments.find({}).sort("created_at", -1).limit(limit)
    payments = await cursor.to_list(length=limit)

    return {"items": [serialize_doc(payment) for payment in payments]}


@router.get("/orders")
async def admin_list_orders(
    request: Request,
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    db = request.app.state.db

    query = {}
    if status:
        query["status"] = status

    cursor = db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    total = await db.orders.count_documents(query)

    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "items": [serialize_doc(order) for order in orders]
    }


@router.get("/orders/{order_id}")
async def admin_get_order(order_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order id")

    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = None
    if order.get("current_payment_id"):
        payment = await db.payments.find_one({"_id": order["current_payment_id"]})

    return {
        "order": serialize_doc(order),
        "payment": serialize_doc(payment) if payment else None,
    }


@router.get("/payments")
async def admin_list_payments(
    request: Request,
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    db = request.app.state.db

    query = {}
    if status:
        query["status"] = status

    cursor = db.payments.find(query).sort("created_at", -1).skip(skip).limit(limit)
    payments = await cursor.to_list(length=limit)
    total = await db.payments.count_documents(query)

    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "items": [serialize_doc(payment) for payment in payments]
    }


@router.get("/payments/pending")
async def admin_list_pending_payments(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    db = request.app.state.db

    query = {"status": "PENDING"}

    cursor = db.payments.find(query).sort("created_at", -1).skip(skip).limit(limit)
    payments = await cursor.to_list(length=limit)
    total = await db.payments.count_documents(query)

    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "items": [serialize_doc(payment) for payment in payments]
    }