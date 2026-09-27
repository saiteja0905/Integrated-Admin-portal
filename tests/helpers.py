"""Shared test helpers (constants and API shortcuts)."""

DEMO_CUSTOMER = {"phone": "9876543210", "password": "password123"}
DEMO_WORKER = {"phone": "9876543211", "password": "password123"}
DEMO_ADMIN = {"phone": "9876543212", "password": "admin123"}


def login(client, credentials):
    """Log in and return (auth headers, user dict)."""
    response = client.post("/api/auth/login", json=credentials)
    assert response.status_code == 200, response.text
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]


def register(client, **overrides):
    payload = {
        "name": "Test User",
        "phone": "9000000001",
        "password": "secret123",
        "role": "customer",
    }
    payload.update(overrides)
    return client.post("/api/auth/register", json=payload)


def create_open_job(client, headers, **overrides):
    payload = {
        "type": "daily",
        "category": "skilled",
        "title": "Fix leaking tap",
        "description": "Kitchen tap is leaking",
        "location": {"lat": 28.6, "lng": 77.2, "address": "New Delhi"},
        "budget_amount": 1500,
    }
    payload.update(overrides)
    response = client.post("/api/jobs", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    job = response.json()
    response = client.put(f"/api/jobs/{job['id']}/publish", headers=headers)
    assert response.status_code == 200, response.text
    return job


def hire(client, customer_headers, worker_headers, worker_id, job):
    response = client.post(
        f"/api/jobs/{job['id']}/apply", json={"message": "Available"}, headers=worker_headers
    )
    assert response.status_code == 200, response.text
    response = client.post(
        f"/api/jobs/{job['id']}/assign",
        params={"worker_id": worker_id},
        headers=customer_headers,
    )
    assert response.status_code == 200, response.text
