# Bakong Ecommerce Backend (FastAPI + MongoDB + Bakong KHQR)

A production-style backend for an ecommerce website using:

- FastAPI
- MongoDB Atlas or local MongoDB
- PyMongo AsyncMongoClient
- JWT authentication
- Role-based admin routes
- Bakong KHQR + MD5 payment verification
- Coupons
- Analytics
- Telegram payment notifications
- Payment reconciliation

---

## 1. Features

### Public / User
- Register and login
- Browse products
- Checkout with shipping address
- Coupon validation
- Bakong KHQR payment page
- Payment status refresh
- My orders

### Admin
- Dashboard stats
- Product CRUD
- Orders list
- Payments list
- Pending payments list
- Coupon CRUD
- Analytics endpoints
- Manual reconciliation
- Retry Telegram notification

---

## 2. Recommended stack

- Python 3.12
- FastAPI
- PyMongo 4.16+
- MongoDB Atlas with `mongodb+srv://`
- Bakong KHQR package
- HTTPX for Telegram notifications

---

## 3. Project structure

```text
backend/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ security.py
│  │  └─ deps.py
│  ├─ db/
│  │  ├─ mongodb.py
│  │  └─ indexes.py
│  ├─ api/
│  │  └─ v1/
│  │     ├─ router.py
│  │     └─ routes/
│  │        ├─ health.py
│  │        ├─ auth.py
│  │        ├─ products.py
│  │        ├─ coupons.py
│  │        ├─ orders.py
│  │        ├─ payments.py
│  │        └─ admin.py
│  ├─ schemas/
│  │  ├─ auth_schema.py
│  │  ├─ user_schema.py
│  │  ├─ product_schema.py
│  │  ├─ order_schema.py
│  │  ├─ payment_schema.py
│  │  └─ coupon_schema.py
│  ├─ services/
│  │  ├─ bakong_service.py
│  │  ├─ coupon_service.py
│  │  ├─ order_service.py
│  │  ├─ payment_service.py
│  │  └─ telegram_service.py
│  └─ utils/
│     └─ serializer.py
├─ .env
└─ requirements.txt
```

---

## 4. Create the backend project

### 4.1 Create virtual environment

```bash
mkdir backend
cd backend
python -m venv .venv
```

### 4.2 Activate virtual environment

**Windows**
```bash
.venv\Scripts\activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

### 4.3 Install dependencies

```bash
pip install -U pip
pip uninstall -y motor pymongo bson
pip install -U "fastapi[standard]" "pymongo>=4.16" pydantic-settings python-dotenv
pip install -U "bakong-khqr[image]" httpx "pwdlib[argon2]" PyJWT email-validator
```

If you ever install plain `fastapi` instead of `fastapi[standard]`, also install:

```bash
pip install python-multipart
```

---

## 5. Environment variables

Create a `.env` file in the `backend/` folder:

```env
APP_NAME=Ecommerce Bakong API
APP_ENV=development
APP_DEBUG=true

MONGODB_URL=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=ecommerce_bakong

BAKONG_TOKEN=your_bakong_or_rbk_token
BAKONG_ACCOUNT=your_name@bank
MERCHANT_NAME=Your Shop Name
MERCHANT_CITY=Phnom Penh
STORE_LABEL=MainStore
PHONE_NUMBER=85512345678
FRONTEND_URL=http://localhost:3000

PAYMENT_QR_EXPIRE_SECONDS=600

AUTH_SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_SECRET
AUTH_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

TELEGRAM_BOT_TOKEN=123456789:YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_ENABLED=true
```

---

## 6. How the backend works

### 6.1 MongoDB connection
- `app/db/mongodb.py` creates one shared `AsyncMongoClient` when the app starts
- it selects `settings.mongodb_db`
- it runs a `ping` command to verify the connection
- it closes the client on shutdown

### 6.2 Authentication
- users register with username, full name, email, phone, and password
- password is hashed before saving
- login returns a JWT access token
- admin routes require a valid token and `role = admin`

### 6.3 Product flow
- admin creates products
- public users can list and view products

### 6.4 Checkout flow
1. user logs in or checks out as guest
2. frontend sends cart items + shipping info
3. backend calculates subtotal
4. backend validates coupon if provided
5. backend creates order
6. backend creates Bakong KHQR + MD5
7. backend creates payment document
8. frontend shows QR code
9. frontend polls payment status endpoint
10. backend verifies payment by MD5
11. backend marks order as paid
12. backend deducts stock
13. backend increments coupon usage
14. backend sends Telegram notification

### 6.5 Reconciliation flow
- admin can run reconciliation manually
- backend loads pending payments
- expired payments are marked expired
- remaining pending payments are checked in bulk by MD5
- paid payments are finalized

---

## 7. Run the backend

```bash
fastapi dev app/main.py
```

Or with uvicorn:

```bash
uvicorn app.main:app --reload
```

Server URLs:
- App root: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

---

## 8. First checks

### 8.1 Root
```http
GET /
```

Expected response:

```json
{
  "message": "Bakong Ecommerce Backend Running"
}
```

### 8.2 Health
```http
GET /api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

---

## 9. Authentication endpoints

## 9.1 Register user
**Endpoint**
```http
POST /api/v1/auth/register
```

**Body**
```json
{
  "username": "davidqt",
  "full_name": "David QT",
  "email": "david@example.com",
  "phone": "85512345678",
  "password": "strongpassword123"
}
```

**curl**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "davidqt",
    "full_name": "David QT",
    "email": "david@example.com",
    "phone": "85512345678",
    "password": "strongpassword123"
  }'
```

---

## 9.2 Login user
**Endpoint**
```http
POST /api/v1/auth/login
```

**Important:** login uses **form-data**, not JSON.

**curl**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=davidqt&password=strongpassword123"
```

**Example response**
```json
{
  "access_token": "YOUR_JWT_TOKEN",
  "token_type": "bearer"
}
```

Save that token for protected routes:

```bash
export TOKEN="YOUR_JWT_TOKEN"
```

**Windows PowerShell**
```powershell
$TOKEN="YOUR_JWT_TOKEN"
```

---

## 9.3 Get current user
**Endpoint**
```http
GET /api/v1/auth/me
```

**curl**
```bash
curl "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 10. Make first admin user

After registration, users are created with `role = customer`.

Promote one user manually in MongoDB shell:

```javascript
db.users.updateOne(
  { username: "davidqt" },
  { $set: { role: "admin" } }
)
```

Then login again to get a token with admin access.

---

## 11. Product endpoints

## 11.1 Create product (Admin)
**Endpoint**
```http
POST /api/v1/products
```

**Body**
```json
{
  "name": "Book A",
  "slug": "book-a",
  "sku": "BOOK-A-001",
  "description": "Demo product",
  "price_minor": 9800,
  "currency": "KHR",
  "stock_qty": 10,
  "images": [],
  "category": "Books",
  "is_active": true
}
```

**curl**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Book A",
    "slug": "book-a",
    "sku": "BOOK-A-001",
    "description": "Demo product",
    "price_minor": 9800,
    "currency": "KHR",
    "stock_qty": 10,
    "images": [],
    "category": "Books",
    "is_active": true
  }'
```

Save the returned `id` as `PRODUCT_ID`.

---

## 11.2 List products
```http
GET /api/v1/products
```

```bash
curl "http://127.0.0.1:8000/api/v1/products"
```

---

## 11.3 Get product by slug
```http
GET /api/v1/products/book-a
```

```bash
curl "http://127.0.0.1:8000/api/v1/products/book-a"
```

---

## 11.4 Update product
```http
PATCH /api/v1/products/{product_id}
```

```bash
curl -X PATCH "http://127.0.0.1:8000/api/v1/products/PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_minor": 12000,
    "stock_qty": 15
  }'
```

---

## 11.5 Delete product
```http
DELETE /api/v1/products/{product_id}
```

```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/products/PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 12. Coupon endpoints

## 12.1 Create coupon (Admin)
**Endpoint**
```http
POST /api/v1/admin/coupons
```

**Percent coupon example**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/coupons" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME10",
    "description": "10 percent off first order",
    "discount_type": "PERCENT",
    "percent_off": 10,
    "min_order_minor": 10000,
    "max_discount_minor": 5000,
    "is_active": true
  }'
```

**Fixed coupon example**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/coupons" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "SAVE2000",
    "description": "2000 KHR off",
    "discount_type": "FIXED",
    "amount_off_minor": 2000,
    "currency": "KHR",
    "min_order_minor": 10000,
    "is_active": true
  }'
```

---

## 12.2 Validate coupon
**Endpoint**
```http
POST /api/v1/coupons/validate
```

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/coupons/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME10",
    "currency": "KHR",
    "subtotal_minor": 25000
  }'
```

---

## 12.3 List coupons (Admin)
```bash
curl "http://127.0.0.1:8000/api/v1/admin/coupons" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 13. Checkout and order endpoints

## 13.1 Guest checkout
```http
POST /api/v1/orders/checkout
```

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/orders/checkout" \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "KHR",
    "customer": {
      "full_name": "Guest User",
      "email": "guest@example.com",
      "phone": "85512345678"
    },
    "shipping_address": {
      "country": "Cambodia",
      "province_city": "Phnom Penh",
      "district": "Dangkor",
      "commune": "Choam Chao",
      "village": "Village 1",
      "street_address": "Street 271, House 12A",
      "postal_code": "12000",
      "note": "Call before delivery"
    },
    "items": [
      {
        "product_id": "PRODUCT_ID",
        "qty": 1
      }
    ]
  }'
```

---

## 13.2 Logged-in checkout
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/orders/checkout" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "KHR",
    "coupon_code": "WELCOME10",
    "shipping_address": {
      "country": "Cambodia",
      "province_city": "Phnom Penh",
      "district": "Dangkor",
      "commune": "Choam Chao",
      "village": "Village 1",
      "street_address": "Street 271, House 12A",
      "postal_code": "12000",
      "note": "Call before delivery"
    },
    "items": [
      {
        "product_id": "PRODUCT_ID",
        "qty": 1
      }
    ]
  }'
```

Save returned values:
- `order.id`
- `payment.id`

---

## 13.3 Get order by id
```bash
curl "http://127.0.0.1:8000/api/v1/orders/ORDER_ID"
```

---

## 13.4 My orders list
```bash
curl "http://127.0.0.1:8000/api/v1/orders/my-orders/list" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 13.5 My order detail
```bash
curl "http://127.0.0.1:8000/api/v1/orders/my-orders/ORDER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 14. Payment endpoints

## 14.1 Get payment by id
```bash
curl "http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID"
```

---

## 14.2 Check payment status
This is the endpoint the frontend should poll every few seconds.

```bash
curl "http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID/status"
```

Possible results:
- `PENDING`
- `PAID`
- `EXPIRED`
- `FAILED`
- `UNKNOWN`

---

## 14.3 Manual refresh payment
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID/refresh"
```

---

## 15. Admin endpoints

All admin endpoints need an **admin token**.

## 15.1 Dashboard stats
```bash
curl "http://127.0.0.1:8000/api/v1/admin/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.2 Recent orders
```bash
curl "http://127.0.0.1:8000/api/v1/admin/dashboard/recent-orders" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.3 Recent payments
```bash
curl "http://127.0.0.1:8000/api/v1/admin/dashboard/recent-payments" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.4 Orders list
```bash
curl "http://127.0.0.1:8000/api/v1/admin/orders" \
  -H "Authorization: Bearer $TOKEN"
```

Filter by status:
```bash
curl "http://127.0.0.1:8000/api/v1/admin/orders?status=PAID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.5 Order detail
```bash
curl "http://127.0.0.1:8000/api/v1/admin/orders/ORDER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.6 Payments list
```bash
curl "http://127.0.0.1:8000/api/v1/admin/payments" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.7 Pending payments list
```bash
curl "http://127.0.0.1:8000/api/v1/admin/payments/pending" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.8 Telegram failed notifications
```bash
curl "http://127.0.0.1:8000/api/v1/admin/payments/telegram-failed" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.9 Retry Telegram notification
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/payments/PAYMENT_ID/retry-telegram" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.10 Run reconciliation
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/reconciliation/run?limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.11 Analytics: sales by day
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/sales-by-day?days=7" \
  -H "Authorization: Bearer $TOKEN"
```

Optional currency filter:
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/sales-by-day?days=30&currency=KHR" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.12 Analytics: top products
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/top-products?days=30&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 15.13 Analytics: coupon performance
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/coupon-performance?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 16. Recommended endpoint test order

Use this order so debugging is easier:

1. `GET /`
2. `GET /api/v1/health`
3. `POST /api/v1/auth/register`
4. `POST /api/v1/auth/login`
5. `GET /api/v1/auth/me`
6. promote user to admin in MongoDB
7. login again
8. `POST /api/v1/products`
9. `GET /api/v1/products`
10. `POST /api/v1/admin/coupons`
11. `POST /api/v1/coupons/validate`
12. `POST /api/v1/orders/checkout`
13. `GET /api/v1/payments/{payment_id}/status`
14. `POST /api/v1/payments/{payment_id}/refresh`
15. `GET /api/v1/orders/my-orders/list`
16. `GET /api/v1/admin/dashboard/stats`
17. `GET /api/v1/admin/orders`
18. `GET /api/v1/admin/payments`
19. `POST /api/v1/admin/reconciliation/run`
20. analytics endpoints

---

## 17. Telegram setup notes

To use Telegram notifications:
1. create a bot with `@BotFather`
2. get your bot token
3. add the bot to your chat/group/channel
4. get the target chat id
5. set `TELEGRAM_ENABLED=true`

If Telegram is disabled, payment success still works. Only the notification is skipped.

---

## 18. Common problems and fixes

### Problem: `ImportError: AsyncMongoClient`
Use modern PyMongo:

```bash
pip uninstall -y motor pymongo bson
pip install -U "pymongo>=4.16"
```

### Problem: login endpoint returns form parsing error
Install:

```bash
pip install python-multipart
```

### Problem: MongoDB Atlas connection fails
Check:
- username/password
- IP allow list in Atlas
- `mongodb+srv://` connection string
- database name in `.env`

### Problem: Bakong payment always pending
Check:
- correct Bakong token
- correct Bakong account
- server location / RBK token rules
- payment really completed in Bakong app

### Problem: Telegram notification fails
Check:
- bot token
- chat id
- bot is added to the target chat
- bot has permission to send messages

---

## 19. Security notes

Before production, improve these areas:
- add refresh tokens
- add rate limiting for login and payment refresh
- add stronger audit logs
- add product image upload validation
- add transaction-safe stock reservation if high traffic
- protect all admin pages on frontend and backend
- use HTTPS in production

---

## 20. Frontend integration summary

Frontend should call these main endpoints:

### Public / user
- `GET /api/v1/products`
- `GET /api/v1/products/{slug}`
- `POST /api/v1/coupons/validate`
- `POST /api/v1/orders/checkout`
- `GET /api/v1/payments/{payment_id}/status`
- `POST /api/v1/payments/{payment_id}/refresh`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/orders/my-orders/list`
- `GET /api/v1/orders/my-orders/{order_id}`

### Admin
- `GET /api/v1/admin/dashboard/stats`
- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/payments`
- `GET /api/v1/admin/coupons`
- `POST /api/v1/admin/coupons`
- `GET /api/v1/admin/analytics/sales-by-day`
- `GET /api/v1/admin/analytics/top-products`
- `GET /api/v1/admin/analytics/coupon-performance`
- `POST /api/v1/admin/reconciliation/run`
- `POST /api/v1/admin/payments/{payment_id}/retry-telegram`

---

## 21. License / usage

This README is intended as a starter guide for your Bakong ecommerce backend project. Adjust route names, models, and validation rules as your project evolves.
