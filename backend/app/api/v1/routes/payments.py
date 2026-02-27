# app/api/v1/routes/payments.py
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.services.bakong_service import BakongService
from app.utils.serializer import serialize_doc

router = APIRouter()


def now_utc():
    # PyMongo returns BSON datetimes as naive UTC by default, so comparisons
    # against fetched timestamps must use naive UTC as well.
    return datetime.utcnow()


async def verify_payment_and_update(db, payment: dict):
    bakong = BakongService()

    order = await db.orders.find_one({"_id": payment["order_id"]})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payment["status"] == "PAID":
        return {
            "status": "PAID",
            "payment": serialize_doc(payment),
            "order": serialize_doc(order),
        }

    if now_utc() > payment["expires_at"]:
        await db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "status": "EXPIRED",
                    "updated_at": now_utc(),
                }
            }
        )
        await db.orders.update_one(
            {"_id": order["_id"]},
            {
                "$set": {
                    "status": "EXPIRED",
                    "updated_at": now_utc(),
                }
            }
        )
        return {"status": "EXPIRED"}

    bakong_status = bakong.check_payment(payment["md5"])

    await db.payments.update_one(
        {"_id": payment["_id"]},
        {
            "$set": {
                "last_checked_at": now_utc(),
                "raw_last_response": bakong_status,
                "updated_at": now_utc(),
            }
        }
    )

    if bakong_status == "UNPAID":
        return {
            "status": "PENDING",
            "payment_id": str(payment["_id"]),
            "order_id": str(order["_id"]),
            "amount_minor": payment["amount_minor"],
            "currency": payment["currency"],
            "deeplink": payment["deeplink"],
            "qr_image_base64": payment["qr_image_base64"],
            "expires_at": payment["expires_at"].isoformat(),
        }

    if bakong_status == "PAID":
        payment_info = bakong.get_payment_info(payment["md5"])

        paid_amount = payment_info.get("amount")
        paid_currency = payment_info.get("currency")
        to_account = payment_info.get("toAccountId")

        if paid_amount != payment["amount_minor"]:
            await db.payments.update_one(
                {"_id": payment["_id"]},
                {
                    "$set": {
                        "status": "FAILED",
                        "bakong_payment_info": payment_info,
                        "raw_last_response": "AMOUNT_MISMATCH",
                        "updated_at": now_utc(),
                    }
                }
            )
            return {"status": "FAILED", "reason": "Amount mismatch"}

        if paid_currency != payment["currency"]:
            await db.payments.update_one(
                {"_id": payment["_id"]},
                {
                    "$set": {
                        "status": "FAILED",
                        "bakong_payment_info": payment_info,
                        "raw_last_response": "CURRENCY_MISMATCH",
                        "updated_at": now_utc(),
                    }
                }
            )
            return {"status": "FAILED", "reason": "Currency mismatch"}

        if to_account != settings.bakong_account:
            await db.payments.update_one(
                {"_id": payment["_id"]},
                {
                    "$set": {
                        "status": "FAILED",
                        "bakong_payment_info": payment_info,
                        "raw_last_response": "ACCOUNT_MISMATCH",
                        "updated_at": now_utc(),
                    }
                }
            )
            return {"status": "FAILED", "reason": "Receiver account mismatch"}

        payment_update = await db.payments.update_one(
            {"_id": payment["_id"], "status": {"$ne": "PAID"}},
            {
                "$set": {
                    "status": "PAID",
                    "paid_at": now_utc(),
                    "bakong_payment_info": payment_info,
                    "updated_at": now_utc(),
                }
            }
        )

        if payment_update.modified_count == 1:
            await db.orders.update_one(
                {"_id": order["_id"], "status": {"$ne": "PAID"}},
                {"$set": {"status": "PAID", "updated_at": now_utc()}}
            )

            for item in order["items"]:
                await db.products.update_one(
                    {"_id": item["product_id"]},
                    {"$inc": {"stock_qty": -item["qty"]}}
                )

            if order.get("coupon") and order["coupon"].get("coupon_id"):
                await db.coupons.update_one(
                    {"_id": order["coupon"]["coupon_id"]},
                    {"$inc": {"used_count": 1}}
                )

        updated_payment = await db.payments.find_one({"_id": payment["_id"]})
        updated_order = await db.orders.find_one({"_id": order["_id"]})

        return {
            "status": "PAID",
            "payment": serialize_doc(updated_payment),
            "order": serialize_doc(updated_order),
        }

    return {"status": "UNKNOWN", "raw": bakong_status}


@router.get("/{payment_id}")
async def get_payment(payment_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(payment_id):
        raise HTTPException(status_code=400, detail="Invalid payment id")

    payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return serialize_doc(payment)


@router.get("/{payment_id}/status")
async def check_payment_status(payment_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(payment_id):
        raise HTTPException(status_code=400, detail="Invalid payment id")

    payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return await verify_payment_and_update(db, payment)


@router.post("/{payment_id}/refresh")
async def refresh_payment_status(payment_id: str, request: Request):
    db = request.app.state.db

    if not ObjectId.is_valid(payment_id):
        raise HTTPException(status_code=400, detail="Invalid payment id")

    payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return await verify_payment_and_update(db, payment)
