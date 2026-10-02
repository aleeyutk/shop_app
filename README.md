# 🛍️ NovaShop — Modern E-Commerce Storefront (HNG 15 Stage 2)

A fast, responsive, and robust **Shop Website** built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL (Neon / Supabase)**, **Google Cloud Console OAuth 2.0**, and **Mailgun** email confirmations. Containerized for deployment on **Fly.io** with complete input validation and automated tests.

---

## 🌐 Live Deployment & Documentation
* **Live Web Storefront:** [https://hng15-shop-aleeyu.fly.dev/](https://hng15-shop-aleeyu.fly.dev/)
* **Interactive Swagger UI:** [https://hng15-shop-aleeyu.fly.dev/docs](https://hng15-shop-aleeyu.fly.dev/docs)
* **ReDoc Documentation:** [https://hng15-shop-aleeyu.fly.dev/redoc](https://hng15-shop-aleeyu.fly.dev/redoc)
* **Health Check & Diagnostics:** [https://hng15-shop-aleeyu.fly.dev/api/health](https://hng15-shop-aleeyu.fly.dev/api/health)

---

## ✨ Features & Stage 2 Requirements

### 1. 🛒 Shop Website & Checkout Page
* **Product Catalog:** Real-time search, category filtering (Electronics, Apparel, Home & Living, Accessories), price sorting, stock level badges, and star ratings.
* **Shopping Cart Drawer:** Add/remove items, adjust quantities, calculate subtotal and free shipping thresholds, with persistence in `localStorage`.
* **Checkout Page & Validation:**
  * Full shipping destination capture (Name, Email, Address, City, State, Zip Code, Country).
  * Simulated instant payment processing (Credit Card formatting & instant test credentials).
  * Transactional stock decrement upon checkout.
* **Order Confirmation & Receipts:**
  * Instant confirmation modal displaying unique Order ID (`ORD-YYMMDD-XXXX`), status, and summary.
  * Direct order history modal allowing buyers to view past orders and items purchased.

### 2. 🗄️ Database Persistence (Supabase / Neon)
* Relational database persistence powered by **SQLAlchemy 2.0**.
* Supports both **Neon PostgreSQL** and **Supabase PostgreSQL** via standard `DATABASE_URL` connection strings with connection pooling and SSL mode support.
* **Automatic Database Seeding:** Automatically seeds the database with curated products across multiple categories upon first run.
* **Graceful Local Fallback:** Automatically falls back to SQLite (`shop.db`) if cloud database credentials are not yet supplied.

### 3. ✉️ Order Confirmation Emails (Mailgun)
* Uses **Mailgun REST API** with HTTP Basic Authentication (`api`, `MAILGUN_API_KEY`).
* Dispatches high-converting, responsive HTML order confirmation emails containing:
  * Branded header and order reference code.
  * Line-item table of purchased products, quantities, and prices.
  * Itemized cost summary (Subtotal, Shipping, Grand Total).
  * Formatted shipping address card.
* Handled asynchronously via FastAPI `BackgroundTasks` to keep checkout response latency under 50ms.
* **Simulation Mode:** Automatically logs emails cleanly to console when Mailgun credentials are not yet configured.

### 4. 🔐 Google Authentication (Google Cloud Console)
* Implements OAuth 2.0 / OpenID Connect (`openid email profile`).
* Secure CSRF state token verification.
* Automatic user profile upserting (name, email, avatar).
* Signed HTTP-only session cookies (`itsdangerous`).
* **Demo / Mock Login:** Includes a 1-click test user authentication button for review and CI environments.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, HTTPX, Authlib, ItsDangerous.
* **Database:** PostgreSQL (Neon / Supabase), with SQLite fallback.
* **Email Service:** Mailgun REST API.
* **Authentication:** Google OAuth 2.0 via Google Cloud Console.
* **Frontend:** Responsive Single-Page Application (HTML5, Tailwind CSS, Lucide Icons, Vanilla JavaScript).
* **Testing:** Pytest, HTTPX `TestClient`, Pytest-Cov (23 automated tests, >85% code coverage).
* **Containerization & Hosting:** Docker (`python:3.12-slim`), Fly.io.

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the single-page shop storefront |
| `GET` | `/api/health` | Health diagnostics (DB status, products count, Mailgun & Google config) |
| `GET` | `/api/categories` | List categories with product counts |
| `GET` | `/api/products` | List & filter products (by category, search term, sort) |
| `GET` | `/api/products/{id}` | Get product details by ID |
| `POST` | `/api/checkout` | Process checkout, decrement stock, persist order, dispatch Mailgun email |
| `GET` | `/api/orders/{id}` | Retrieve order summary and receipt by order ID |
| `GET` | `/api/orders` | List orders for current user or filter by email |
| `GET` | `/auth/google/login` | Redirect to Google OAuth 2.0 consent screen |
| `GET` | `/auth/google/callback` | OAuth 2.0 redirect handler and session issuer |
| `GET` | `/auth/me` | Get currently authenticated user profile |
| `POST` | `/auth/mock-login` | 1-click demo login for testing |
| `POST` | `/auth/logout` | Clear session cookie |

---

## 💻 Local Setup & Development

### 1. Clone & Setup Virtual Environment
```bash
cd hng15/shop-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your credentials:
```env
# Database (Neon / Supabase or local SQLite)
DATABASE_URL=postgresql://user:password@ep-xxxx.neon.tech/neondb?sslmode=require

# Google Cloud OAuth 2.0
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Mailgun Email
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=sandboxxxxxxxxxxx.mailgun.org
MAILGUN_FROM_EMAIL=NovaShop Orders <orders@sandboxxxxxxxxxxx.mailgun.org>

# Application Base URL
BASE_URL=http://localhost:8000
```

### 3. Start Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🧪 Running Automated Tests
```bash
pytest -v --cov=app tests/
```
Output:
```
======================== 23 passed in 4.44s (86% coverage) ========================
```

---

## 🚢 Docker & Deployment to Fly.io

### Build & Run Locally with Docker:
```bash
docker build -t novashop .
docker run -p 8000:8000 --env-file .env novashop
```

### Deploy to Fly.io:
```bash
flyctl launch --no-deploy
flyctl secrets set DATABASE_URL="postgresql://..." \
                   MAILGUN_API_KEY="..." \
                   MAILGUN_DOMAIN="..." \
                   GOOGLE_CLIENT_ID="..." \
                   GOOGLE_CLIENT_SECRET="..."
flyctl deploy
```

---

## 📄 License
This project is open-source under the MIT License. Developed for the HNG 15 Internship.
