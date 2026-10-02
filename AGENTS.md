# 🤖 Contributor & AI Agent Guide (`AGENTS.md`)

## 📌 Project Overview
**NovaShop** is a production-grade e-commerce shop web application built for the **HNG 15 Internship (Stage 2 - Individual Shop Website Task)**.

### Core Deliverables Met:
1. **Interactive Shop Front & Checkout Page:** Full product catalog, category filtering, search, interactive cart drawer, and a multi-step checkout workflow with shipping address capture and simulated payment processing.
2. **Cloud Database Persistence with Supabase / Neon:** PostgreSQL database persistence with SQLAlchemy 2.0 models for Users, Categories, Products, Orders, and OrderItems. Includes automatic schema creation and initial catalog seeding on startup.
3. **Mailgun Email Confirmation:** HTML-styled transactional order receipt emails sent automatically in background tasks upon order placement via the Mailgun REST API.
4. **Google Authentication via Google Cloud Console:** Full OAuth 2.0 flow with CSRF state protection, token exchange, and encrypted session management.
5. **Production Readiness:** Dockerized container with health checks, Fly.io deployment config, and automated test suite with >85% code coverage.

---

## 🏗 Architecture & Code Structure

```
shop-app/
├── app/
│   ├── config.py             # Pydantic Settings & environment variables
│   ├── database.py           # SQLAlchemy Engine, SessionLocal, init_db, seed_data
│   ├── models.py             # ORM models (User, Category, Product, Order, OrderItem)
│   ├── schemas.py            # Pydantic v2 validation models
│   ├── services/
│   │   ├── auth_service.py   # Google OAuth 2.0 URL generator, token exchange, user upsert
│   │   └── email_service.py  # Mailgun client & responsive HTML email invoice template
│   ├── routes/
│   │   ├── auth.py           # /auth/google/login, /auth/google/callback, /auth/me, /auth/mock-login
│   │   └── shop.py           # /api/products, /api/categories, /api/checkout, /api/orders
│   ├── static/
│   │   ├── index.html        # Responsive Single Page Application UI
│   │   ├── app.js            # Frontend reactive state & API logic
│   │   └── style.css         # Styling, card elevation & animations
│   └── main.py               # FastAPI entrypoint, CORS, static files, health check
├── tests/
│   ├── conftest.py           # In-memory SQLite fixture and FastAPI TestClient
│   └── test_shop.py          # 23 automated tests (catalog, checkout, auth, mailgun)
├── Dockerfile                # Multi-stage lean Python 3.12 image
├── fly.toml                  # Fly.io deployment specification
├── requirements.txt          # Development dependencies
├── requirements-prod.txt     # Lean runtime dependencies
└── README.md                 # Public documentation
```

---

## 🔑 Environment Setup & External Integrations

### 1. Database (Neon or Supabase)
Set `DATABASE_URL` in `.env`:
* **Neon PostgreSQL:**
  ```env
  DATABASE_URL=postgresql://username:password@ep-xxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
  ```
* **Supabase PostgreSQL:**
  ```env
  DATABASE_URL=postgresql://postgres:password@db.xxxxxx.supabase.co:5432/postgres
  ```
* **Local Development Fallback:** If `DATABASE_URL` is omitted, the application automatically uses SQLite (`sqlite:///./shop.db`).

### 2. Google Cloud Console (OAuth 2.0)
1. Go to [Google Cloud Console](https://console.cloud.google.com/) -> **APIs & Services** -> **Credentials**.
2. Create an **OAuth 2.0 Client ID** (Application type: *Web application*).
3. Add Authorized Redirect URIs:
   * Local: `http://localhost:8000/auth/google/callback`
   * Production (Fly.io): `https://<your-app>.fly.dev/auth/google/callback`
4. Set credentials in `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

### 3. Mailgun Configuration
1. Sign in to [Mailgun](https://www.mailgun.com/) and copy your API Key and Sending Domain (or Sandbox domain).
2. Set credentials in `.env`:
   ```env
   MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxx
   MAILGUN_DOMAIN=sandboxxxxxxxxxxx.mailgun.org
   MAILGUN_FROM_EMAIL=NovaShop Orders <orders@sandboxxxxxxxxxxx.mailgun.org>
   MAILGUN_BASE_URL=https://api.mailgun.net/v3
   ```
> [!NOTE]
> If `MAILGUN_API_KEY` is omitted or empty, the application enters **Simulation Mode**: it logs the full order invoice to the console without crashing, allowing frictionless local testing and evaluations.

---

## 🧪 Testing Guidelines
Always run the automated test suite before committing code:
```bash
source venv/bin/activate
pytest -v --cov=app tests/
```
All pull requests must maintain ≥80% test coverage and ensure zero test failures.

---

## 🚀 Fly.io Deployment Checklist
1. Authenticate with Fly CLI: `flyctl auth login`
2. Create app / launch: `flyctl launch --no-deploy`
3. Set production secrets on Fly:
   ```bash
   flyctl secrets set \
     DATABASE_URL="postgresql://..." \
     GOOGLE_CLIENT_ID="..." \
     GOOGLE_CLIENT_SECRET="..." \
     MAILGUN_API_KEY="..." \
     MAILGUN_DOMAIN="..." \
     BASE_URL="https://hng15-shop-aleeyu.fly.dev"
   ```
4. Deploy: `flyctl deploy`
