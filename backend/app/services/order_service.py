from datetime import datetime, timedelta, timezone
from bson import ObjectId
from fastapi import HTTPException

from app.core.config import settings
from app.services.bakong_service import BakongService
from app.services.coupon_service import CouponService


class OrderService:
    def __init__(self, db):
        self.db = db
        self.bakong = BakongService()
        self.coupons = CouponService(db)

    def _now(self):
        return datetime.now(timezone.utc)

    def _generate_order_number(self):
        now = self._now()
        return f"ORD-{now.strftime('%Y%m%d%H%M%S%f')}"

    def _build_customer_info(self, current_user: dict | None, customer: dict | None):
        if customer:
            return customer

        if current_user:
            return {
                "full_name": current_user.get("full_name") or current_user.get("username"),
                "email": current_user.get("email"),
                "phone": current_user.get("phone") or "",
            }

        raise HTTPException(
            status_code=400,
            detail="Customer information is required for guest checkout"
        )

    async def checkout(
        self,
        items: list,
        currency: str,
        shipping_address: dict,
        current_user: dict | None = None,
        customer: dict | None = None,
        coupon_code: str | None = None,
    ):
        if not items:
            raise HTTPException(status_code=400, detail="Checkout items are required")

        final_customer = self._build_customer_info(current_user, customer)

        if not final_customer.get("phone"):
            raise HTTPException(status_code=400, detail="Phone number is required")

        object_ids = []
        for item in items:
            if not ObjectId.is_valid(item["product_id"]):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid product_id: {item['product_id']}"
                )
            object_ids.append(ObjectId(item["product_id"]))

        products = await self.db.products.find({
            "_id": {"$in": object_ids},
            "is_active": True
        }).to_list(length=200)

        product_map = {str(product["_id"]): product for product in products}

        if len(product_map) != len(object_ids):
            raise HTTPException(status_code=404, detail="One or more products not found")

        order_items = []
        subtotal_minor = 0

        for item in items:
            product = product_map[item["product_id"]]
            qty = item["qty"]

            if product["currency"] != currency:
                raise HTTPException(
                    status_code=400,
                    detail=f"Currency mismatch for product: {product['name']}"
                )

            if product["stock_qty"] < qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for product: {product['name']}"
                )

            line_subtotal = product["price_minor"] * qty
            subtotal_minor += line_subtotal

            order_items.append({
                "product_id": product["_id"],
                "sku_snapshot": product["sku"],
                "name_snapshot": product["name"],
                "unit_price_minor": product["price_minor"],
                "qty": qty,
                "subtotal_minor": line_subtotal,
            })

        discount_minor = 0
        coupon_snapshot = None

        if coupon_code:
            coupon_result = await self.coupons.validate_coupon(
                code=coupon_code,
                currency=currency,
                subtotal_minor=subtotal_minor,
            )
            coupon = coupon_result["coupon"]
            discount_minor = coupon_result["discount_minor"]
            coupon_snapshot = {
                "coupon_id": coupon["_id"],
                "code": coupon["code"],
                "discount_type": coupon["discount_type"],
                "percent_off": coupon.get("percent_off"),
                "amount_off_minor": coupon.get("amount_off_minor"),
                "discount_minor": discount_minor,
            }

        grand_total_minor = subtotal_minor - discount_minor

        now = self._now()
        expires_at = now + timedelta(seconds=settings.payment_qr_expire_seconds)
        order_number = self._generate_order_number()
        user_id = current_user["_id"] if current_user else None

        order_doc = {
            "order_number": order_number,
            "user_id": user_id,
            "customer": final_customer,
            "shipping_address": shipping_address,
            "items": order_items,
            "coupon": coupon_snapshot,
            "currency": currency,
            "totals": {
                "subtotal_minor": subtotal_minor,
                "shipping_minor": 0,
                "discount_minor": discount_minor,
                "grand_total_minor": grand_total_minor,
            },
            "status": "AWAITING_PAYMENT",
            "current_payment_id": None,
            "created_at": now,
            "updated_at": now,
            "expires_at": expires_at,
        }

        order_result = await self.db.orders.insert_one(order_doc)
        order_id = order_result.inserted_id

        payment_assets = self.bakong.create_payment_assets(
            amount_minor=grand_total_minor,
            currency=currency,
            bill_number=order_number,
        )

        payment_doc = {
            "order_id": order_id,
            "bill_number": order_number,
            "qr_string": payment_assets["qr_string"],
            "qr_image_base64": payment_assets["qr_image_base64"],
            "deeplink": payment_assets["deeplink"],
            "md5": payment_assets["md5"],
            "bakong_account": settings.bakong_account,
            "amount_minor": grand_total_minor,
            "currency": currency,
            "status": "PENDING",
            "bakong_payment_info": None,
            "last_checked_at": None,
            "paid_at": None,
            "expires_at": expires_at,
            "raw_last_response": None,
            "created_at": now,
            "updated_at": now,
        }

        payment_result = await self.db.payments.insert_one(payment_doc)

        await self.db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "current_payment_id": payment_result.inserted_id,
                    "updated_at": self._now(),
                }
            }
        )

        order = await self.db.orders.find_one({"_id": order_id})
        payment = await self.db.payments.find_one({"_id": payment_result.inserted_id})

        return order, payment