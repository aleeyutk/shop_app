from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ------------------------------------------------------------------------------
# Category Schemas
# ------------------------------------------------------------------------------
class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: str = "tag"
    product_count: Optional[int] = 0


# ------------------------------------------------------------------------------
# Product Schemas
# ------------------------------------------------------------------------------
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str
    price: float
    currency: str = "USD"
    image_url: str
    category_id: int
    stock: int
    is_featured: bool
    rating: float
    reviews_count: int
    created_at: datetime


# ------------------------------------------------------------------------------
# Cart & Checkout Schemas
# ------------------------------------------------------------------------------
class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0, le=1000)


class CheckoutIn(BaseModel):
    items: List[CartItemIn] = Field(min_length=1, description="List of items in the cart to checkout")
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    customer_phone: Optional[str] = Field(default=None, max_length=50)
    shipping_address: str = Field(min_length=5, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=2, max_length=30)
    country: str = Field(default="United States", max_length=100)
    payment_method: str = Field(default="CARD", max_length=50)


# ------------------------------------------------------------------------------
# Order Schemas
# ------------------------------------------------------------------------------
class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int] = None
    product_name: str
    product_image: Optional[str] = None
    unit_price: float
    quantity: int
    subtotal: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[int] = None
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: str
    city: str
    state: str
    postal_code: str
    country: str
    subtotal: float
    shipping_fee: float
    total_amount: float
    currency: str
    status: str
    payment_method: str
    mailgun_message_id: Optional[str] = None
    mailgun_sent: bool
    created_at: datetime
    items: List[OrderItemOut]


# ------------------------------------------------------------------------------
# User & Auth Schemas
# ------------------------------------------------------------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    created_at: datetime


class MockLoginIn(BaseModel):
    name: str = "Test Customer"
    email: EmailStr = "tester@example.com"
    avatar_url: Optional[str] = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80"


# ------------------------------------------------------------------------------
# Health Check Schema
# ------------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    database_connected: bool
    database_engine: str
    google_auth_configured: bool
    mailgun_configured: bool
    products_count: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
