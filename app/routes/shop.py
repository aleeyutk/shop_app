import logging
import secrets
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db, SessionLocal
from app.models import Category, Product, Order, OrderItem, User
from app.schemas import (
    CategoryOut,
    ProductOut,
    CheckoutIn,
    OrderOut,
)
from app.routes.auth import get_current_user_optional
from app.services.email_service import send_order_confirmation_email

logger = logging.getLogger("shop.api")
router = APIRouter(prefix="/api", tags=["Shop & Checkout"])


async def trigger_email_background(order_id: str):
    """Background task to send confirmation email and update Mailgun tracking in DB."""
    with SessionLocal() as db:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return

        order_dict = {
            "id": order.id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "shipping_address": order.shipping_address,
            "city": order.city,
            "state": order.state,
            "postal_code": order.postal_code,
            "country": order.country,
            "subtotal": order.subtotal,
            "shipping_fee": order.shipping_fee,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status,
            "payment_method": order.payment_method,
        }

        items_list = [
            {
                "product_name": it.product_name,
                "product_image": it.product_image,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "subtotal": it.subtotal,
            }
            for it in order.items
        ]

        result = await send_order_confirmation_email(order_dict, items_list)
        if result.get("sent"):
            order.mailgun_sent = True
            order.mailgun_message_id = result.get("message_id")
            db.commit()


@router.get("/categories", response_model=List[CategoryOut], summary="List Categories")
def list_categories(db: Session = Depends(get_db)):
    """Return all categories along with their respective product counts."""
    categories = db.query(Category).all()
    results = []
    for cat in categories:
        count = db.query(func.count(Product.id)).filter(Product.category_id == cat.id).scalar() or 0
        cat_out = CategoryOut.model_validate(cat)
        cat_out.product_count = count
        results.append(cat_out)
    return results


@router.get("/products", response_model=List[ProductOut], summary="List & Filter Products")
def list_products(
    category: Optional[str] = Query(None, description="Category slug or ID to filter by"),
    search: Optional[str] = Query(None, description="Search term in product name or description"),
    featured: Optional[bool] = Query(None, description="Filter for featured items"),
    sort: Optional[str] = Query("featured", description="Sorting: 'price_asc', 'price_desc', 'rating', 'newest'"),
    db: Session = Depends(get_db),
):
    """Retrieve catalog products with full-text search, category filtering, and sorting."""
    query = db.query(Product)

    if category and category.lower() != "all":
        if category.isdigit():
            query = query.filter(Product.category_id == int(category))
        else:
            cat_obj = db.query(Category).filter(Category.slug == category).first()
            if cat_obj:
                query = query.filter(Product.category_id == cat_obj.id)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )

    if featured is not None:
        query = query.filter(Product.is_featured == featured)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "rating":
        query = query.order_by(Product.rating.desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else:
        # Default sort: featured first, then newest
        query = query.order_by(Product.is_featured.desc(), Product.id.asc())

    return query.all()


@router.get("/products/{product_id}", response_model=ProductOut, summary="Get Product Details")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Retrieve product details by product ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} was not found.",
        )
    return product


@router.post("/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED, summary="Process Checkout & Create Order")
def checkout(
    payload: CheckoutIn,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Process checkout:
    1. Validates items in cart and checks available stock.
    2. Computes line items, subtotal, shipping fee, and grand total.
    3. Decrements stock levels in the database.
    4. Persists the Order and OrderItems to Supabase/Neon PostgreSQL (or SQLite).
    5. Dispatches a Mailgun order confirmation email in the background.
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot process checkout with an empty cart.",
        )

    order_items_to_create = []
    subtotal = 0.0

    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item.product_id} no longer exists.",
            )

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}, requested: {item.quantity}.",
            )

        # Decrement stock
        product.stock -= item.quantity

        line_subtotal = round(product.price * item.quantity, 2)
        subtotal += line_subtotal

        order_items_to_create.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "product_image": product.image_url,
                "unit_price": product.price,
                "quantity": item.quantity,
                "subtotal": line_subtotal,
            }
        )

    subtotal = round(subtotal, 2)
    # Free shipping on orders >= $50, else $5.00
    shipping_fee = 0.0 if subtotal >= 50.0 else 5.0
    total_amount = round(subtotal + shipping_fee, 2)

    # Unique human-friendly order ID
    order_id = f"ORD-{datetime.now(timezone.utc).strftime('%y%m%d')}-{secrets.token_hex(3).upper()}"

    new_order = Order(
        id=order_id,
        user_id=current_user.id if current_user else None,
        customer_name=payload.customer_name.strip(),
        customer_email=payload.customer_email.lower().strip(),
        customer_phone=payload.customer_phone.strip() if payload.customer_phone else None,
        shipping_address=payload.shipping_address.strip(),
        city=payload.city.strip(),
        state=payload.state.strip(),
        postal_code=payload.postal_code.strip(),
        country=payload.country.strip(),
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total_amount=total_amount,
        currency="USD",
        status="CONFIRMED",
        payment_method=payload.payment_method.strip(),
        mailgun_sent=False,
    )
    db.add(new_order)
    db.flush()

    for item_data in order_items_to_create:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            product_image=item_data["product_image"],
            unit_price=item_data["unit_price"],
            quantity=item_data["quantity"],
            subtotal=item_data["subtotal"],
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)

    # Dispatch Mailgun email in background
    background_tasks.add_task(trigger_email_background, new_order.id)

    return new_order


@router.get("/orders/{order_id}", response_model=OrderOut, summary="Get Order by ID")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Retrieve full order summary and receipt by order ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' was not found.",
        )
    return order


@router.get("/orders", response_model=List[OrderOut], summary="List Orders for Current User or Customer Email")
def list_orders(
    email: Optional[str] = Query(None, description="Optional email to query orders"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    List orders. If user is logged in, defaults to their user account orders.
    Can also search by customer email for guest lookups.
    """
    query = db.query(Order)

    if current_user:
        query = query.filter(
            or_(
                Order.user_id == current_user.id,
                Order.customer_email == current_user.email,
            )
        )
    elif email:
        query = query.filter(Order.customer_email == email.lower().strip())
    else:
        # Return recent orders (limit to 10 for dashboard preview)
        query = query.order_by(Order.created_at.desc()).limit(10)

    return query.order_by(Order.created_at.desc()).all()
