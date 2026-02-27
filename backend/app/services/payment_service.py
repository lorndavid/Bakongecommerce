# app/services/payment_service.py
from datetime import datetime
from math import ceil

from bson import ObjectId
from fastapi import HTTPException
from pymongo import UpdateOne

from app.core.config import settings
from app.services.bakong_service import BakongService
from app.services.telegram_service import TelegramService


class PaymentService:
    def __init__(self, db):
        self.db = db
        self.bakong = BakongService()
        self.telegram = TelegramService()

    def _now(self):
        # Keep service timestamps naive UTC to match BSON datetimes returned by PyMongo.
        return datetime.utcnow()

    def _chunk(self, items: list, size: int):
        for i in range(0, len(items), size):
            yield items[i:i + size]

    async def _load_payment_and_order(self, payment_id: str):
        if not ObjectId.is_valid(payment_id):
            raise HTTPException(status_code=400, detail="Invalid payment id")

        payment = await self.db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        order = await self.db.orders.find_one({"_id": payment["order_id"]})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return payment, order

    async def _mark_expired_if_needed(self, payment: dict, order: dict):
        if self._now() <= payment["expires_at"]:
            return None

        await self.db.payments.update_one(
            {"_id": payment["_id"], "status": {"$nin": ["PAID", "EXPIRED"]}},
            {
                "$set": {
                    "status": "EXPIRED",
                    "updated_at": self._now(),
                }
            }
        )

        await self.db.orders.update_one(
            {"_id": order["_id"], "status": {"$nin": ["PAID", "EXPIRED"]}},
            {
                "$set": {
                    "status": "EXPIRED",
                    "updated_at": self._now(),
                }
            }
        )

        return {"status": "EXPIRED"}

    async def _handle_payment_mismatch(self, payment: dict, payment_info: dict, reason: str):
        await self.db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "status": "FAILED",
                    "bakong_payment_info": payment_info,
                    "raw_last_response": reason,
                    "updated_at": self._now(),
                }
            }
        )
        return {"status": "FAILED", "reason": reason}

    async def _send_paid_telegram_if_needed(self, order: dict, payment: dict, payment_info: dict):
        if payment.get("telegram_notified_at"):
            return

        try:
            text = self.telegram.build_payment_paid_message(order, payment, payment_info)
            result = await self.telegram.send_message(text)

            await self.db.payments.update_one(
                {"_id": payment["_id"]},
                {
                    "$set": {
                        "telegram_notified_at": self._now(),
                        "telegram_message_id": (
                            result.get("result", {}).get("message_id")
                            if isinstance(result, dict) else None
                        ),
                        "telegram_last_error": None,
                        "updated_at": self._now(),
                    }
                }
            )
        except Exception as exc:
            await self.db.payments.update_one(
                {"_id": payment["_id"]},
                {
                    "$set": {
                        "telegram_last_error": str(exc),
                        "updated_at": self._now(),
                    }
                }
            )

    async def _apply_paid_state(self, payment: dict, order: dict, payment_info: dict):
        paid_amount = payment_info.get("amount")
        paid_currency = payment_info.get("currency")
        to_account = payment_info.get("toAccountId")

        if paid_amount != payment["amount_minor"]:
            return await self._handle_payment_mismatch(payment, payment_info, "AMOUNT_MISMATCH")

        if paid_currency != payment["currency"]:
            return await self._handle_payment_mismatch(payment, payment_info, "CURRENCY_MISMATCH")

        if to_account != settings.bakong_account:
            return await self._handle_payment_mismatch(payment, payment_info, "ACCOUNT_MISMATCH")

        payment_update = await self.db.payments.update_one(
            {"_id": payment["_id"], "status": {"$ne": "PAID"}},
            {
                "$set": {
                    "status": "PAID",
                    "paid_at": self._now(),
                    "bakong_payment_info": payment_info,
                    "raw_last_response": "PAID",
                    "updated_at": self._now(),
                }
            }
        )

        if payment_update.modified_count == 1:
            await self.db.orders.update_one(
                {"_id": order["_id"], "status": {"$ne": "PAID"}},
                {
                    "$set": {
                        "status": "PAID",
                        "updated_at": self._now(),
                    }
                }
            )

            stock_ops = []
            for item in order["items"]:
                stock_ops.append(
                    UpdateOne(
                        {"_id": item["product_id"]},
                        {"$inc": {"stock_qty": -item["qty"]}}
                    )
                )

            if stock_ops:
                await self.db.products.bulk_write(stock_ops, ordered=True)

            if order.get("coupon") and order["coupon"].get("coupon_id"):
                await self.db.coupons.update_one(
                    {"_id": order["coupon"]["coupon_id"]},
                    {"$inc": {"used_count": 1}}
                )

        updated_payment = await self.db.payments.find_one({"_id": payment["_id"]})
        updated_order = await self.db.orders.find_one({"_id": order["_id"]})

        await self._send_paid_telegram_if_needed(
            updated_order,
            updated_payment,
            payment_info,
        )

        updated_payment = await self.db.payments.find_one({"_id": payment["_id"]})
        return {
            "status": "PAID",
            "payment": updated_payment,
            "order": updated_order,
        }

    async def verify_payment_by_id(self, payment_id: str):
        payment, order = await self._load_payment_and_order(payment_id)
        return await self.verify_loaded_payment(payment, order)

    async def verify_loaded_payment(self, payment: dict, order: dict | None = None):
        if order is None:
            order = await self.db.orders.find_one({"_id": payment["order_id"]})
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

        if payment["status"] == "PAID":
            return {
                "status": "PAID",
                "payment": payment,
                "order": order,
            }

        expired = await self._mark_expired_if_needed(payment, order)
        if expired:
            return expired

        bakong_status = self.bakong.check_payment(payment["md5"])

        await self.db.payments.update_one(
            {"_id": payment["_id"]},
            {
                "$set": {
                    "last_checked_at": self._now(),
                    "raw_last_response": bakong_status,
                    "updated_at": self._now(),
                }
            }
        )

        if bakong_status == "UNPAID":
            refreshed = await self.db.payments.find_one({"_id": payment["_id"]})
            return {
                "status": "PENDING",
                "payment": refreshed,
                "order": order,
            }

        if bakong_status == "PAID":
            payment_info = self.bakong.get_payment_info(payment["md5"])
            return await self._apply_paid_state(payment, order, payment_info)

        return {
            "status": "UNKNOWN",
            "raw": bakong_status,
        }

    async def retry_telegram_by_payment_id(self, payment_id: str):
        payment, order = await self._load_payment_and_order(payment_id)

        if payment["status"] != "PAID":
            raise HTTPException(status_code=400, detail="Payment is not PAID")

        payment_info = payment.get("bakong_payment_info") or {}
        await self._send_paid_telegram_if_needed(order, payment, payment_info)

        refreshed = await self.db.payments.find_one({"_id": payment["_id"]})
        return {
            "status": "OK",
            "payment": refreshed,
        }

    async def reconcile_pending_payments(self, limit: int = 100):
        pending = await self.db.payments.find(
            {"status": "PENDING"}
        ).sort("created_at", 1).limit(limit).to_list(length=limit)

        if not pending:
            return {
                "scanned": 0,
                "paid": 0,
                "expired": 0,
                "still_pending": 0,
                "failed": 0,
            }

        paid_count = 0
        expired_count = 0
        still_pending_count = 0
        failed_count = 0

        # handle expired first
        active_payments = []
        for payment in pending:
            order = await self.db.orders.find_one({"_id": payment["order_id"]})
            if not order:
                failed_count += 1
                continue

            expired = await self._mark_expired_if_needed(payment, order)
            if expired:
                expired_count += 1
            else:
                active_payments.append((payment, order))

        if not active_payments:
            return {
                "scanned": len(pending),
                "paid": paid_count,
                "expired": expired_count,
                "still_pending": still_pending_count,
                "failed": failed_count,
            }

        md5_to_data = {
            payment["md5"]: (payment, order)
            for payment, order in active_payments
        }

        all_md5 = list(md5_to_data.keys())
        paid_md5_set = set()

        for batch in self._chunk(all_md5, 50):
            try:
                paid_list = self.bakong.check_bulk_payments(batch)
                for md5 in paid_list:
                    paid_md5_set.add(md5)
            except Exception:
                # if bulk fails, fall back to single checks for that batch
                for md5 in batch:
                    try:
                        status = self.bakong.check_payment(md5)
                        if status == "PAID":
                            paid_md5_set.add(md5)
                    except Exception:
                        failed_count += 1

        for md5, (payment, order) in md5_to_data.items():
            if md5 in paid_md5_set:
                try:
                    result = await self._apply_paid_state(
                        payment,
                        order,
                        self.bakong.get_payment_info(md5),
                    )
                    if result["status"] == "PAID":
                        paid_count += 1
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1
            else:
                await self.db.payments.update_one(
                    {"_id": payment["_id"]},
                    {
                        "$set": {
                            "last_checked_at": self._now(),
                            "raw_last_response": "UNPAID",
                            "updated_at": self._now(),
                        }
                    }
                )
                still_pending_count += 1

        return {
            "scanned": len(pending),
            "paid": paid_count,
            "expired": expired_count,
            "still_pending": still_pending_count,
            "failed": failed_count,
        }
