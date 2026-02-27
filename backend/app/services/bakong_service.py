# app/services/bakong_service.py
from bakong_khqr import KHQR
from app.core.config import settings


class BakongService:
    def __init__(self):
        self.khqr = KHQR(settings.bakong_token)

    def create_payment_assets(self, amount_minor: int, currency: str, bill_number: str):
        qr = self.khqr.create_qr(
            bank_account=settings.bakong_account,
            merchant_name=settings.merchant_name,
            merchant_city=settings.merchant_city,
            amount=amount_minor,
            currency=currency,
            store_label=settings.store_label,
            phone_number=settings.phone_number,
            bill_number=bill_number,
            terminal_label="WEB-CHECKOUT",
            static=False,
        )

        deeplink = self.khqr.generate_deeplink(
            qr,
            callback=f"{settings.frontend_url}/payment/{bill_number}",
            appIconUrl=f"{settings.frontend_url}/logo.png",
            appName="MyShop"
        )

        md5 = self.khqr.generate_md5(qr)
        qr_image_base64 = self.khqr.qr_image(qr, format="base64_uri")

        return {
            "qr_string": qr,
            "deeplink": deeplink,
            "md5": md5,
            "qr_image_base64": qr_image_base64,
        }

    def check_payment(self, md5: str):
        result = self.khqr.check_payment(md5)
        if isinstance(result, str):
            return result.upper().strip()
        return str(result).upper().strip()

    def get_payment_info(self, md5: str):
        return self.khqr.get_payment(md5)

    def check_bulk_payments(self, md5_list: list[str]) -> list[str]:
        return self.khqr.check_bulk_payments(md5_list)