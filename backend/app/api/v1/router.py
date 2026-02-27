from fastapi import APIRouter
from app.api.v1.routes import health, products, orders, payments, admin, auth, coupons

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])