import pytest
from unittest.mock import patch, MagicMock
from app.services.email_service import send_order_confirmation_email, generate_order_html
from app.models import Product


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True
    assert data["products_count"] > 0


def test_list_categories(client):
    response = client.get("/api/categories")
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) >= 4
    slugs = [c["slug"] for c in categories]
    assert "electronics" in slugs
    assert "apparel" in slugs


def test_list_products_all(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    assert any("Aura Pro" in p["name"] for p in products)


def test_filter_products_by_category(client):
    response = client.get("/api/products?category=electronics")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    assert all("Headphones" in p["name"] or "Watch" in p["name"] or "Keyboard" in p["name"] or "Monitor" in p["name"] for p in products)


def test_search_products(client):
    response = client.get("/api/products?search=headphones")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 1
    assert "Headphones" in products[0]["name"]


def test_sort_products(client):
    res_asc = client.get("/api/products?sort=price_asc")
    assert res_asc.status_code == 200
    prices_asc = [p["price"] for p in res_asc.json()]
    assert prices_asc == sorted(prices_asc)

    res_desc = client.get("/api/products?sort=price_desc")
    assert res_desc.status_code == 200
    prices_desc = [p["price"] for p in res_desc.json()]
    assert prices_desc == sorted(prices_desc, reverse=True)


def test_get_single_product(client):
    res_list = client.get("/api/products")
    first_id = res_list.json()[0]["id"]

    response = client.get(f"/api/products/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_id
    assert "name" in data
    assert "price" in data


def test_get_nonexistent_product(client):
    response = client.get("/api/products/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_checkout_successful(client, db_session):
    # Find product with stock
    product = db_session.query(Product).first()
    initial_stock = product.stock

    payload = {
        "items": [{"product_id": product.id, "quantity": 2}],
        "customer_name": "Sarah Connor",
        "customer_email": "sarah.connor@example.com",
        "customer_phone": "+1 555-0199",
        "shipping_address": "742 Evergreen Terrace",
        "city": "Springfield",
        "state": "OR",
        "postal_code": "97477",
        "country": "United States",
        "payment_method": "VISA •••• 4242",
    }

    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 201
    order = response.json()

    assert order["id"].startswith("ORD-")
    assert order["customer_name"] == "Sarah Connor"
    assert order["customer_email"] == "sarah.connor@example.com"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2
    assert order["total_amount"] > 0
    assert order["status"] == "CONFIRMED"

    # Verify stock decremented
    db_session.refresh(product)
    assert product.stock == initial_stock - 2


def test_checkout_empty_cart(client):
    payload = {
        "items": [],
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "shipping_address": "123 Main St",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 422


def test_checkout_insufficient_stock(client, db_session):
    product = db_session.query(Product).first()

    payload = {
        "items": [{"product_id": product.id, "quantity": product.stock + 5}],
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "shipping_address": "123 Main St",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()


def test_checkout_invalid_email(client, db_session):
    product = db_session.query(Product).first()
    payload = {
        "items": [{"product_id": product.id, "quantity": 1}],
        "customer_name": "Test User",
        "customer_email": "not-an-email",
        "shipping_address": "123 Main St",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
    }
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 422


def test_get_order_by_id(client, db_session):
    product = db_session.query(Product).first()
    payload = {
        "items": [{"product_id": product.id, "quantity": 1}],
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "shipping_address": "100 Pine St",
        "city": "Seattle",
        "state": "WA",
        "postal_code": "98101",
    }
    create_res = client.post("/api/checkout", json=payload)
    order_id = create_res.json()["id"]

    get_res = client.get(f"/api/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id
    assert get_res.json()["customer_email"] == "john@example.com"


def test_get_nonexistent_order(client):
    response = client.get("/api/orders/ORD-NONEXISTENT")
    assert response.status_code == 404


def test_mock_login_and_authenticated_checkout(client, db_session):
    # Perform mock login
    login_res = client.post(
        "/auth/mock-login",
        json={
            "name": "Jane Developer",
            "email": "jane.dev@example.com",
            "avatar_url": "https://example.com/avatar.jpg",
        },
    )
    assert login_res.status_code == 200
    user_data = login_res.json()
    assert user_data["email"] == "jane.dev@example.com"

    # Verify session persisted via cookie in client
    me_res = client.get("/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "jane.dev@example.com"

    # Place order as authenticated user
    product = db_session.query(Product).first()
    order_res = client.post(
        "/api/checkout",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "customer_name": "Jane Developer",
            "customer_email": "jane.dev@example.com",
            "shipping_address": "456 Silicon Way",
            "city": "San Jose",
            "state": "CA",
            "postal_code": "95112",
        },
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["user_id"] == user_data["id"]

    # Retrieve user's orders
    orders_res = client.get("/api/orders")
    assert orders_res.status_code == 200
    orders = orders_res.json()
    assert any(o["id"] == order_data["id"] for o in orders)

    # Logout
    logout_res = client.post("/auth/logout")
    assert logout_res.status_code == 200

    # /auth/me should now return 401
    me_after_logout = client.get("/auth/me")
    assert me_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_mailgun_email_service_fallback():
    order_data = {
        "id": "ORD-TEST-001",
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "shipping_address": "123 Test St",
        "city": "Testville",
        "state": "TS",
        "postal_code": "12345",
        "country": "United States",
        "subtotal": 50.0,
        "shipping_fee": 0.0,
        "total_amount": 50.0,
        "currency": "USD",
        "status": "CONFIRMED",
        "payment_method": "CARD",
    }
    items = [
        {
            "product_name": "Aura Pro Headphones",
            "product_image": None,
            "quantity": 1,
            "unit_price": 50.0,
            "subtotal": 50.0,
        }
    ]

    # Without Mailgun API key set, it safely returns simulated status
    result = await send_order_confirmation_email(order_data, items)
    assert result["sent"] is True
    assert "simulated" in result
    assert result["simulated"] is True


@pytest.mark.asyncio
async def test_mailgun_email_service_success_mocked():
    order_data = {
        "id": "ORD-TEST-002",
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "shipping_address": "123 Test St",
        "city": "Testville",
        "state": "TS",
        "postal_code": "12345",
        "country": "United States",
        "subtotal": 60.0,
        "shipping_fee": 0.0,
        "total_amount": 60.0,
        "currency": "USD",
        "status": "CONFIRMED",
        "payment_method": "CARD",
    }
    items = [
        {
            "product_name": "Test Product",
            "product_image": None,
            "quantity": 1,
            "unit_price": 60.0,
            "subtotal": 60.0,
        }
    ]

    with patch("app.services.email_service.settings.MAILGUN_API_KEY", "key-test-12345"), \
         patch("app.services.email_service.settings.MAILGUN_DOMAIN", "test.mailgun.org"), \
         patch("httpx.AsyncClient.post") as mock_post:
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "<20261002.test@test.mailgun.org>",
            "message": "Queued. Thank you.",
        }
        mock_post.return_value = mock_response

        result = await send_order_confirmation_email(order_data, items)
        assert result["sent"] is True
        assert result["simulated"] is False
        assert result["message_id"] == "<20261002.test@test.mailgun.org>"


def test_google_login_not_configured(client):
    with patch("app.routes.auth.settings.GOOGLE_CLIENT_ID", ""), \
         patch("app.routes.auth.settings.GOOGLE_CLIENT_SECRET", ""):
        res = client.get("/auth/google/login")
        assert res.status_code == 503
        assert "not configured" in res.json()["detail"].lower()


def test_google_login_redirect_when_configured(client):
    with patch("app.routes.auth.settings.GOOGLE_CLIENT_ID", "mock-client-id"), \
         patch("app.routes.auth.settings.GOOGLE_CLIENT_SECRET", "mock-client-secret"):
        res = client.get("/auth/google/login", follow_redirects=False)
        assert res.status_code == 302
        assert "accounts.google.com" in res.headers["location"]


def test_google_callback_missing_code(client):
    res = client.get("/auth/google/callback")
    assert res.status_code == 400
    assert "missing" in res.json()["detail"].lower()


def test_google_callback_with_error(client):
    res = client.get("/auth/google/callback?error=access_denied")
    assert res.status_code == 400
    assert "access_denied" in res.json()["detail"]


def test_home_page_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "NovaShop" in res.text


def test_list_orders_by_guest_email(client, db_session):
    product = db_session.query(Product).first()
    client.post(
        "/api/checkout",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "customer_name": "Unique Buyer",
            "customer_email": "unique.buyer@example.com",
            "shipping_address": "880 Broadway",
            "city": "New York",
            "state": "NY",
            "postal_code": "10003",
        },
    )

    res = client.get("/api/orders?email=unique.buyer@example.com")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["customer_email"] == "unique.buyer@example.com"

