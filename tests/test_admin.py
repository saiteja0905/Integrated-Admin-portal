from tests.helpers import DEMO_ADMIN, DEMO_CUSTOMER, DEMO_WORKER, login


def test_admin_dashboard_loads(client):
    headers, _ = login(client, DEMO_ADMIN)
    response = client.get("/api/admin/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    workers = response.json()["top_performing_workers"]
    assert workers and all("_id" not in worker for worker in workers)


def test_non_admin_is_forbidden(client):
    headers, _ = login(client, DEMO_CUSTOMER)
    assert client.get("/api/admin/users", headers=headers).status_code == 403


def test_admin_suspend_reactivate_and_status_filter(client):
    headers, _ = login(client, DEMO_ADMIN)
    _, worker = login(client, DEMO_WORKER)

    client.put(f"/api/admin/users/{worker['id']}/suspend", json={"suspend": True}, headers=headers)
    suspended = client.get("/api/admin/users", params={"status": "suspended"}, headers=headers).json()
    assert [user["id"] for user in suspended] == [worker["id"]]
    assert suspended[0]["status"] == "suspended"

    client.put(f"/api/admin/users/{worker['id']}/suspend", json={"suspend": False}, headers=headers)
    assert client.post("/api/auth/login", json=DEMO_WORKER).status_code == 200


def test_admin_verify_user(client):
    headers, _ = login(client, DEMO_ADMIN)
    _, worker = login(client, DEMO_WORKER)

    response = client.put(
        f"/api/admin/users/{worker['id']}/verify", json={"verified": True}, headers=headers
    )
    assert response.status_code == 200, response.text
    users = client.get("/api/admin/users", params={"role": "worker"}, headers=headers).json()
    assert users[0]["kyc_verified"] is True


def test_admin_search_handles_regex_characters(client):
    headers, _ = login(client, DEMO_ADMIN)
    response = client.get("/api/admin/users", params={"search": "(["}, headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_strike_requires_description(client):
    headers, _ = login(client, DEMO_ADMIN)
    _, worker = login(client, DEMO_WORKER)
    response = client.post(
        f"/api/admin/users/{worker['id']}/strike",
        json={"reason": "policy_violation", "description": ""},
        headers=headers,
    )
    assert response.status_code == 422
