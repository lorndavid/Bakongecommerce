# Bakong Shop Backend

<p align="center">
  <strong>Modern ecommerce backend for Cambodia, powered by FastAPI, MongoDB, Bakong KHQR, JWT auth, coupons, analytics, Telegram alerts, and reconciliation tools.</strong>
</p>

<p align="center">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img alt="MongoDB" src="https://img.shields.io/badge/MongoDB-Database-47A248?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Bakong KHQR" src="https://img.shields.io/badge/Bakong-KHQR-orange?style=for-the-badge" />
  <img alt="JWT" src="https://img.shields.io/badge/Auth-JWT-black?style=for-the-badge" />
  <img alt="Telegram" src="https://img.shields.io/badge/Telegram-Notifications-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" />
</p>

---

## Overview

**Bakong Shop Backend** is a production-style backend for an ecommerce platform that supports:

- product catalog and inventory
- customer authentication and role-based access
- checkout with shipping information
- Bakong KHQR generation and MD5 payment verification
- coupon validation and discount tracking
- admin dashboard and analytics APIs
- Telegram payment notifications
- reconciliation for pending payments

This project is designed for two audiences:

- **Developers** who want a clean, scalable FastAPI backend
- **Business owners / clients** who want a backend ready for ecommerce operations, payment tracking, and admin reporting

---

## Why this project is useful

### For developers
- clean folder structure
- service-based backend architecture
- reusable auth and payment logic
- modern async MongoDB connection with PyMongo AsyncMongoClient
- Swagger docs out of the box

### For business / client teams
- secure user and admin separation
- product and order management
- payment confirmation and monitoring
- coupon campaigns and sales insights
- operational alerts through Telegram

---

## Key features

### Customer-facing
- register and login
- browse products
- validate coupon codes
- checkout with shipping address
- pay with Bakong KHQR
- refresh payment status
- view personal order history

### Admin-facing
- dashboard statistics
- product CRUD
- order management
- payment monitoring
- coupon CRUD
- analytics endpoints
- reconciliation tool for pending payments
- Telegram retry tools

---

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Language | Python 3.12+ |
| Database | MongoDB |
| Mongo driver | PyMongo 4.16+ AsyncMongoClient |
| Auth | JWT |
| Password hashing | pwdlib with Argon2 |
| Payment | Bakong KHQR + MD5 verification |
| HTTP client | HTTPX |
| Notifications | Telegram Bot API |
| Docs / testing | Swagger UI |

---

## Architecture at a glance

```text
Frontend (Next.js / mobile / web client)
        |
        v
FastAPI API Layer
  - auth routes
  - product routes
  - checkout routes
  - payment routes
  - admin routes
        |
        v
Service Layer
  - order service
  - payment service
  - coupon service
  - bakong service
  - telegram service
        |
        v
MongoDB
  - users
  - products
  - orders
  - payments
  - coupons
```

---

## Project structure

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

## Quick start

### 1) Create the project folder and virtual environment

```bash
mkdir backend
cd backend
python -m venv .venv
```

### 2) Activate the virtual environment

**Windows**
```bash
.venv\Scripts\activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -U pip
pip uninstall -y motor pymongo bson
pip install -U "fastapi[standard]" "pymongo>=4.16" pydantic-settings python-dotenv
pip install -U "bakong-khqr[image]" httpx "pwdlib[argon2]" PyJWT email-validator
```

If you installed plain `fastapi` earlier, also install:

```bash
pip install python-multipart
```

---

## Environment configuration

Create a `.env` file inside `backend/`.

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

### Environment variable notes

| Variable | Purpose |
|---|---|
| `MONGODB_URL` | MongoDB Atlas or local MongoDB connection string |
| `BAKONG_TOKEN` | Bakong or RBK token used to generate QR and verify payments |
| `BAKONG_ACCOUNT` | Merchant Bakong account receiving payments |
| `AUTH_SECRET_KEY` | JWT signing secret |
| `TELEGRAM_*` | Telegram bot alert configuration |

---

## Running the server

```bash
fastapi dev app/main.py
```

Or with Uvicorn:

```bash
uvicorn app.main:app --reload
```

### Default local URLs
- App root: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

---

## How the backend works

### 1) MongoDB connection
- `app/db/mongodb.py` creates one shared async MongoDB client at startup
- the app selects `settings.mongodb_db`
- a `ping` check confirms the database is reachable
- indexes are created when the app starts
- the client is closed cleanly on shutdown

### 2) Authentication
- users register with username, name, email, phone, and password
- passwords are hashed before saving
- login returns a JWT access token
- admin routes require a valid token and `role = admin`

### 3) Product management
- products are created and managed by admins
- customers can list and view products publicly
- stock is reduced only after successful payment

### 4) Checkout and payment flow
1. customer adds items to cart
2. frontend sends checkout payload
3. backend validates products and stock
4. backend validates coupon if provided
5. backend creates order document
6. backend generates Bakong KHQR and MD5 hash
7. backend creates payment document
8. frontend shows QR and polls payment status
9. backend verifies payment status with Bakong
10. if paid, backend updates payment and order to `PAID`
11. backend deducts stock
12. backend increments coupon usage
13. backend sends Telegram alert

### 5) Reconciliation flow
- used when a payment is still marked pending in the database
- scans pending payments
- marks expired payments
- checks remaining payments in batches
- finalizes paid payments

---

## First health checks

### Root endpoint
```http
GET /
```

Expected response:

```json
{
  "message": "Bakong Ecommerce Backend Running"
}
```

### Health endpoint
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

## Authentication guide

### Register a user
```http
POST /api/v1/auth/register
```

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

### Login
```http
POST /api/v1/auth/login
```

> Important: login uses **form-data**, not JSON.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=davidqt&password=strongpassword123"
```

Expected response:

```json
{
  "access_token": "YOUR_JWT_TOKEN",
  "token_type": "bearer"
}
```

Save the token:

**Linux / macOS**
```bash
export TOKEN="YOUR_JWT_TOKEN"
```

**PowerShell**
```powershell
$TOKEN="YOUR_JWT_TOKEN"
```

### Current user profile
```bash
curl "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Make the first admin user

New users start with role `customer`.
Promote one user manually in MongoDB:

```javascript
db.users.updateOne(
  { username: "davidqt" },
  { $set: { role: "admin" } }
)
```

Then log in again to get a valid admin session token.

---

## Product API

### Create product (admin)
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

### List products
```bash
curl "http://127.0.0.1:8000/api/v1/products"
```

### Get product by slug
```bash
curl "http://127.0.0.1:8000/api/v1/products/book-a"
```

### Update product
```bash
curl -X PATCH "http://127.0.0.1:8000/api/v1/products/PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_minor": 12000,
    "stock_qty": 15
  }'
```

### Delete product
```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/products/PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Coupon API

### Create a percent coupon (admin)
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

### Create a fixed coupon (admin)
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

### Validate coupon
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/coupons/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME10",
    "currency": "KHR",
    "subtotal_minor": 25000
  }'
```

### List coupons (admin)
```bash
curl "http://127.0.0.1:8000/api/v1/admin/coupons" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Checkout and order API

### Guest checkout
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

### Logged-in checkout with coupon
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

Save:
- `order.id`
- `payment.id`

### Get order by ID
```bash
curl "http://127.0.0.1:8000/api/v1/orders/ORDER_ID"
```

### User order list
```bash
curl "http://127.0.0.1:8000/api/v1/orders/my-orders/list" \
  -H "Authorization: Bearer $TOKEN"
```

### User order detail
```bash
curl "http://127.0.0.1:8000/api/v1/orders/my-orders/ORDER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Payment API

### Get payment by ID
```bash
curl "http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID"
```

### Check payment status
```bash
curl "http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID/status"
```

Typical statuses:
- `PENDING`
- `PAID`
- `EXPIRED`
- `FAILED`
- `UNKNOWN`

### Manual payment refresh
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/payments/PAYMENT_ID/refresh"
```

---

## Admin API

> All admin endpoints require an admin token.

### Dashboard stats
```bash
curl "http://127.0.0.1:8000/api/v1/admin/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### Recent orders
```bash
curl "http://127.0.0.1:8000/api/v1/admin/dashboard/recent-orders" \
  -H "Authorization: Bearer $TOKEN"
```

### Recent payments
```bash
curl "http://127.0.0.1:8000/api/v1/admin/dashboard/recent-payments" \
  -H "Authorization: Bearer $TOKEN"
```

### Orders list
```bash
curl "http://127.0.0.1:8000/api/v1/admin/orders" \
  -H "Authorization: Bearer $TOKEN"
```

### Orders filtered by status
```bash
curl "http://127.0.0.1:8000/api/v1/admin/orders?status=PAID" \
  -H "Authorization: Bearer $TOKEN"
```

### Order detail
```bash
curl "http://127.0.0.1:8000/api/v1/admin/orders/ORDER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Payments list
```bash
curl "http://127.0.0.1:8000/api/v1/admin/payments" \
  -H "Authorization: Bearer $TOKEN"
```

### Pending payments
```bash
curl "http://127.0.0.1:8000/api/v1/admin/payments/pending" \
  -H "Authorization: Bearer $TOKEN"
```

### Telegram failed notification list
```bash
curl "http://127.0.0.1:8000/api/v1/admin/payments/telegram-failed" \
  -H "Authorization: Bearer $TOKEN"
```

### Retry Telegram notification
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/payments/PAYMENT_ID/retry-telegram" \
  -H "Authorization: Bearer $TOKEN"
```

### Run reconciliation
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/reconciliation/run?limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

### Sales by day analytics
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/sales-by-day?days=7" \
  -H "Authorization: Bearer $TOKEN"
```

### Sales by day with currency filter
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/sales-by-day?days=30&currency=KHR" \
  -H "Authorization: Bearer $TOKEN"
```

### Top products analytics
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/top-products?days=30&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Coupon performance analytics
```bash
curl "http://127.0.0.1:8000/api/v1/admin/analytics/coupon-performance?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Recommended test order

Use this order for the smoothest testing experience:

1. `GET /`
2. `GET /api/v1/health`
3. `POST /api/v1/auth/register`
4. `POST /api/v1/auth/login`
5. `GET /api/v1/auth/me`
6. promote the user to admin in MongoDB
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

## Telegram setup notes

To enable payment notifications:

1. create a bot with `@BotFather`
2. copy the bot token
3. add the bot to your target chat, group, or channel
4. get the chat ID
5. set `TELEGRAM_ENABLED=true`

If Telegram is disabled, payment processing still works. Only the notification step is skipped.

---

## Common issues and fixes

### `ImportError: AsyncMongoClient`
Install modern PyMongo only:

```bash
pip uninstall -y motor pymongo bson
pip install -U "pymongo>=4.16"
```

### Login form parsing error
Install:

```bash
pip install python-multipart
```

### MongoDB Atlas connection fails
Check:
- username and password
- IP allow list
- SRV URI format
- database name in `.env`

### Bakong payment always stays pending
Check:
- correct Bakong token
- correct Bakong receiver account
- RBK token or deployment location requirements
- actual payment completion in the Bakong app

### Telegram notification fails
Check:
- bot token
- chat ID
- bot is inside the target chat
- bot has message permissions

---

## Security notes

Before production, consider adding:

- refresh tokens
- login rate limiting
- payment refresh rate limiting
- audit logs
- stronger inventory reservation / transaction strategy
- HTTPS everywhere
- stricter admin route protection
- image upload validation and storage rules

---

## Frontend integration summary

### Customer / storefront
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

### Admin dashboard
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

## Suggested next improvements

- add refresh-token flow
- create Postman collection
- add product image upload support
- schedule reconciliation as a background worker or cron job
- build admin charts in the frontend
- add delivery status workflow
- add customer profile update API

---

## License and usage

Use this README as a starter for your own Bakong ecommerce backend project. Adapt naming, routes, and business rules to match your final product requirements.
