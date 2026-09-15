from tests.helpers import DEMO_ADMIN, DEMO_CUSTOMER, DEMO_WORKER, login, register


def test_register_cannot_create_admin(client):
    response = register(client, role="admin")
    assert response.status_code == 422


def test_register_with_blank_optional_email(client):
    response = register(client, email="")
    assert response.status_code == 200, response.text
    assert response.json()["user"]["email"] is None


def test_register_normalizes_phone_and_blocks_duplicates(client):
    response = register(client, phone="+91 90000 00002")
    assert response.status_code == 200, response.text
    assert response.json()["user"]["phone"] == "9000000002"

    duplicate = register(client, phone="9000000002")
    assert duplicate.status_code == 400


def test_register_rejects_short_password(client):
    response = register(client, password="123")
    assert response.status_code == 422


def test_register_rejects_duplicate_email(client):
    assert register(client, phone="9000000003", email="dup@example.com").status_code == 200
    response = register(client, phone="9000000004", email="dup@example.com")
    assert response.status_code == 400


def test_login_accepts_formatted_phone(client):
    response = client.post(
        "/api/auth/login", json={"phone": "+91 98765 43210", "password": "password123"}
    )
    assert response.status_code == 200, response.text


def test_missing_token_returns_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_suspended_user_cannot_log_in(client):
    admin_headers, _ = login(client, DEMO_ADMIN)
    _, worker = login(client, DEMO_WORKER)

    response = client.put(
        f"/api/admin/users/{worker['id']}/suspend", json={"suspend": True}, headers=admin_headers
    )
    assert response.status_code == 200, response.text

    response = client.post("/api/auth/login", json=DEMO_WORKER)
    assert response.status_code == 403


def test_user_profile_hides_contact_details(client):
    headers, _ = login(client, DEMO_CUSTOMER)
    _, worker = login(client, DEMO_WORKER)

    assert client.get(f"/api/users/{worker['id']}").status_code == 401

    response = client.get(f"/api/users/{worker['id']}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "phone" not in body
    assert "email" not in body
