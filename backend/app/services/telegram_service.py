# app/services/telegram_service.py
from datetime import datetime, timezone
import html

import httpx

from app.core.config import settings


class TelegramService:
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = bool(
            settings.telegram_enabled and self.bot_token and self.chat_id
        )

    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def send_message(self, text: str):
        if not self.enabled:
            return {
                "ok": False,
                "reason": "telegram_disabled"
            }

        url = f"{self._base_url()}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")

        return data

    def build_payment_paid_message(self, order: dict, payment: dict, payment_info: dict | None = None) -> str:
        order_number = html.escape(order.get("order_number", "-"))
        customer_name = html.escape(order.get("customer", {}).get("full_name", "-"))
        phone = html.escape(order.get("customer", {}).get("phone", "-"))
        currency = html.escape(order.get("currency", "-"))
        total = order.get("totals", {}).get("grand_total_minor", 0)

        province_city = html.escape(order.get("shipping_address", {}).get("province_city", "-"))
        district = html.escape(order.get("shipping_address", {}).get("district", "-"))
        street = html.escape(order.get("shipping_address", {}).get("street_address", "-"))

        external_ref = "-"
        from_account = "-"
        if payment_info:
            external_ref = html.escape(str(payment_info.get("externalRef", "-")))
            from_account = html.escape(str(payment_info.get("fromAccountId", "-")))

        return (
            "✅ <b>Payment Received</b>\n"
            f"🧾 <b>Order:</b> {order_number}\n"
            f"👤 <b>Customer:</b> {customer_name}\n"
            f"📞 <b>Phone:</b> {phone}\n"
            f"💰 <b>Total:</b> {total} {currency}\n"
            f"🏦 <b>From:</b> {from_account}\n"
            f"🔗 <b>Ref:</b> {external_ref}\n"
            f"📍 <b>Address:</b> {street}, {district}, {province_city}\n"
            f"🕒 <b>Time:</b> {self._now_iso()}"
        )