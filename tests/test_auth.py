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


def test_google_auth_new_user(client):
    payload = {
        "email": "newgoogleuser@example.com",
        "name": "Google New User",
        "role": "customer",
        "uid": "google_uid_12345"
    }
    response = client.post("/api/auth/google", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newgoogleuser@example.com"
    assert data["user"]["name"] == "Google New User"
    assert len(data["user"]["phone"]) == 10
    assert data["user"]["phone"].startswith("99")


def test_google_auth_existing_user(client):
    # First register normal user with email
    reg = register(client, email="existinggoogle@example.com", phone="9000000088")
    assert reg.status_code == 200

    # Google auth with same email should log in
    payload = {
        "email": "existinggoogle@example.com",
        "name": "Existing User",
        "role": "customer"
    }
    response = client.post("/api/auth/google", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "existinggoogle@example.com"


def test_authorized_admin_emails_get_admin_role_on_google_login(client):
    admin_emails = [
        "shaikbashe222@gmail.com",
        "Saiteja.g@alignx.ai",  # test mixed case handling
        "saiteja7778@gmail.com",
        "shanmukhaveera6969@gmail.com",
        "kamisettyyogesh@gmail.com",
    ]
    for email in admin_emails:
        payload = {
            "email": email,
            "name": "Admin Tester",
            "role": "customer",  # client requests customer, but server must promote to admin
        }
        response = client.post("/api/auth/google", json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["user"]["role"] == "admin", f"Expected admin role for {email}, got {data['user']['role']}"

        # Verify admin can access admin dashboard stats
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        stats_res = client.get("/api/admin/dashboard", headers=headers)
        assert stats_res.status_code == 200, stats_res.text


def test_unauthorized_email_cannot_be_admin(client):
    payload = {
        "email": "intruder@gmail.com",
        "name": "Regular User",
        "role": "admin",  # tries to request admin
    }
    response = client.post("/api/auth/google", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user"]["role"] != "admin"
    assert data["user"]["role"] == "customer"

    # Verify denied on admin routes
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    stats_res = client.get("/api/admin/users", headers=headers)
    assert stats_res.status_code == 403


def test_stateless_jwt_rehydration_across_serverless_cold_starts(client):
    # Register a user and get token
    reg = client.post("/api/auth/google", json={
        "email": "coldstartuser@example.com",
        "name": "Cold Start User",
        "role": "customer"
    })
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]

    import server
    import asyncio
    # Simulate a new serverless container by deleting the user from db.users
    asyncio.run(server.db.users.delete_one({"id": user_id}))

    # Verify user is gone from DB
    deleted_check = asyncio.run(server.db.users.find_one({"id": user_id}))
    assert deleted_check is None

    # Call /api/auth/me with the existing token:
    # It must re-hydrate the user without returning 401
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200, me_res.text
    assert me_res.json()["id"] == user_id
    assert me_res.json()["email"] == "coldstartuser@example.com"


def test_login_with_email_and_password_customer(client):
    # Customer demo user login by email
    response = client.post("/api/auth/login", json={
        "email_or_phone": "customer@demo.com",
        "password": "password123"
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user"]["email"] == "customer@demo.com"
    assert data["user"]["role"] == "customer"


def test_login_with_email_and_password_admin(client):
    # Admin login by authorized email
    response = client.post("/api/auth/login", json={
        "email_or_phone": "shaikbashe222@gmail.com",
        "password": "admin123"
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user"]["email"] == "shaikbashe222@gmail.com"
    assert data["user"]["role"] == "admin"

    # Verify access to admin portal with this token
    token = data["access_token"]
    dash_res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert dash_res.status_code == 200


def test_login_with_email_and_wrong_password(client):
    response = client.post("/api/auth/login", json={
        "email_or_phone": "customer@demo.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401



