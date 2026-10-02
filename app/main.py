import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import get_settings
from app.database import init_db, get_db
from app.models import Product
from app.schemas import HealthResponse
from app.routes import shop, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and seed products
    init_db()
    yield


app = FastAPI(
    title="NovaShop API",
    description="E-Commerce Shop API with Google Cloud OAuth, Neon/Supabase PostgreSQL persistence, and Mailgun Order Confirmations.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(shop.router)
app.include_router(auth.router)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def serve_home():
    """Serve the single-page storefront."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "NovaShop API is running. Visit /docs for OpenAPI documentation."}


@app.get("/api/health", response_model=HealthResponse, tags=["System Health"], summary="Health Check")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint displaying DB engine, connectivity, and integration configurations."""
    db_connected = False
    count = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        count = db.query(Product).count()
    except Exception:
        db_connected = False

    return HealthResponse(
        status="ok" if db_connected else "degraded",
        database_connected=db_connected,
        database_engine="PostgreSQL" if settings.is_postgres else "SQLite",
        google_auth_configured=settings.is_google_auth_configured,
        mailgun_configured=settings.is_mailgun_configured,
        products_count=count,
    )
