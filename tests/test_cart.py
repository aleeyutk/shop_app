import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cart_workflow():
    # 1. Login as test user
    login_res = client.post(
        "/auth/mock-login",
        json={"name": "Cart Tester", "email": "cart.tester@example.com"},
    )
    assert login_res.status_code == 200
    user_data = login_res.json()
    assert user_data["token"] is not None
    token = user_data["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get empty cart
    res = client.get("/api/cart", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_count"] == 0

    # 3. Add item to cart
    add_res = client.post("/api/cart", json={"product_id": 1, "quantity": 2}, headers=headers)
    assert add_res.status_code == 200
    cart = add_res.json()
    assert cart["total_count"] == 2
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == 1
    assert cart["items"][0]["quantity"] == 2

    # 4. Update quantity
    upd_res = client.put("/api/cart/1", json={"quantity": 3}, headers=headers)
    assert upd_res.status_code == 200
    assert upd_res.json()["total_count"] == 3

    # 5. Remove item
    del_res = client.delete("/api/cart/1", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["total_count"] == 0
