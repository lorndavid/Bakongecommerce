from pymongo import ASCENDING, DESCENDING


async def create_indexes(db):
    # users
    await db.users.create_index([("username", ASCENDING)], unique=True)
    await db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
    await db.users.create_index([("role", ASCENDING)])
    await db.users.create_index([("is_active", ASCENDING)])

    # coupons
    await db.coupons.create_index([("code", ASCENDING)], unique=True)
    await db.coupons.create_index([("is_active", ASCENDING)])
    await db.coupons.create_index([("starts_at", ASCENDING)])
    await db.coupons.create_index([("ends_at", ASCENDING)])

    # products
    await db.products.create_index([("slug", ASCENDING)], unique=True)
    await db.products.create_index([("sku", ASCENDING)], unique=True)
    await db.products.create_index([("is_active", ASCENDING)])

    # orders
    await db.orders.create_index([("order_number", ASCENDING)], unique=True)
    await db.orders.create_index([("user_id", ASCENDING)])
    await db.orders.create_index([("status", ASCENDING)])
    await db.orders.create_index([("currency", ASCENDING)])
    await db.orders.create_index([("created_at", DESCENDING)])
    await db.orders.create_index([("customer.full_name", ASCENDING)])
    await db.orders.create_index([("customer.phone", ASCENDING)])
    await db.orders.create_index([("coupon.code", ASCENDING)], sparse=True)

    # payments
    await db.payments.create_index([("md5", ASCENDING)], unique=True)
    await db.payments.create_index([("bill_number", ASCENDING)], unique=True)
    await db.payments.create_index([("order_id", ASCENDING)])
    await db.payments.create_index([("status", ASCENDING)])
    await db.payments.create_index([("expires_at", ASCENDING)])
    await db.payments.create_index([("created_at", DESCENDING)])
    await db.payments.create_index([("telegram_notified_at", ASCENDING)])
    await db.payments.create_index([("telegram_last_error", ASCENDING)], sparse=True)
    await db.payments.create_index([("updated_at", DESCENDING)])