from tests.helpers import DEMO_CUSTOMER, DEMO_WORKER, create_open_job, hire, login, register


def test_my_jobs_only_returns_own_jobs(client):
    demo_headers, _ = login(client, DEMO_CUSTOMER)
    other = register(client, phone="9000000010").json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    other_job = create_open_job(client, other_headers, title="Other customer's job")

    demo_jobs = client.get("/api/jobs", params={"mine": True}, headers=demo_headers).json()
    assert other_job["id"] not in {job["id"] for job in demo_jobs}

    own_jobs = client.get("/api/jobs", params={"mine": True}, headers=other_headers).json()
    assert [job["id"] for job in own_jobs] == [other_job["id"]]


def test_marketplace_hides_drafts(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, _ = login(client, DEMO_WORKER)
    draft = client.post(
        "/api/jobs",
        json={
            "type": "daily",
            "category": "skilled",
            "title": "Draft job",
            "description": "Not published",
            "location": {"lat": 28.6, "lng": 77.2, "address": "Delhi"},
            "budget_amount": 500,
        },
        headers=customer_headers,
    ).json()

    listed = client.get("/api/jobs", headers=worker_headers).json()
    assert draft["id"] not in {job["id"] for job in listed}
    assert client.get(f"/api/jobs/{draft['id']}", headers=worker_headers).status_code == 404
    assert client.get("/api/jobs").status_code == 401


def test_job_create_rejects_invalid_values(client):
    headers, _ = login(client, DEMO_CUSTOMER)
    response = client.post(
        "/api/jobs",
        json={
            "type": "anything",
            "category": "skilled",
            "title": "Bad",
            "description": "Bad",
            "location": {"lat": 0, "lng": 0, "address": "x"},
            "budget_amount": -5,
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_publish_cannot_reopen_assigned_job(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    hire(client, customer_headers, worker_headers, worker["id"], job)

    response = client.put(f"/api/jobs/{job['id']}/publish", headers=customer_headers)
    assert response.status_code == 400


def test_applications_include_worker_info(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    client.post(f"/api/jobs/{job['id']}/apply", json={"message": "hi"}, headers=worker_headers)

    applications = client.get(
        f"/api/jobs/{job['id']}/applications", headers=customer_headers
    ).json()
    assert applications[0]["worker_info"]["name"] == worker["name"]


def test_payment_amount_must_match_and_cod_completes_once(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers, budget_amount=2500)
    hire(client, customer_headers, worker_headers, worker["id"], job)

    wrong = client.post(
        "/api/payments/create-order",
        json={"job_id": job["id"], "amount": 1, "method": "cod"},
        headers=customer_headers,
    )
    assert wrong.status_code == 400

    paid = client.post(
        "/api/payments/create-order",
        json={"job_id": job["id"], "amount": 2500, "method": "cod"},
        headers=customer_headers,
    )
    assert paid.status_code == 200, paid.text
    job_after = client.get(f"/api/jobs/{job['id']}", headers=customer_headers).json()
    assert job_after["status"] == "completed"

    again = client.post(
        "/api/payments/create-order",
        json={"job_id": job["id"], "method": "cod"},
        headers=customer_headers,
    )
    assert again.status_code == 400


def test_review_must_target_counterparty(client):
    customer_headers, customer = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    hire(client, customer_headers, worker_headers, worker["id"], job)
    client.post(
        "/api/payments/create-order",
        json={"job_id": job["id"], "method": "cod"},
        headers=customer_headers,
    )

    self_review = client.post(
        f"/api/jobs/{job['id']}/review",
        json={"stars": 5, "reviewee_user_id": customer["id"]},
        headers=customer_headers,
    )
    assert self_review.status_code == 400

    review = client.post(
        f"/api/jobs/{job['id']}/review", json={"stars": 4}, headers=customer_headers
    )
    assert review.status_code == 200, review.text
    assert review.json()["reviewee_user_id"] == worker["id"]

    duplicate = client.post(
        f"/api/jobs/{job['id']}/review", json={"stars": 1}, headers=customer_headers
    )
    assert duplicate.status_code == 400


def test_chat_masks_formatted_phone_numbers(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    hire(client, customer_headers, worker_headers, worker["id"], job)

    client.post(
        f"/api/jobs/{job['id']}/messages",
        json={"content": "Call me on 98765 43210 or +91-98765-43211"},
        headers=worker_headers,
    )
    messages = client.get(f"/api/jobs/{job['id']}/messages", headers=customer_headers).json()
    content = messages[0]["content"]
    assert "43210" not in content
    assert "43211" not in content
    assert "98****10" in content


def test_upload_rejects_non_images(client):
    headers, _ = login(client, DEMO_CUSTOMER)

    fake = client.post(
        "/api/upload",
        files={"file": ("photo.jpg", b"<html>not an image</html>", "image/jpeg")},
        headers=headers,
    )
    assert fake.status_code == 400

    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    real = client.post(
        "/api/upload", files={"file": ("photo.png", png, "image/png")}, headers=headers
    )
    assert real.status_code == 200, real.text
    assert real.json()["url"].startswith("/uploads/")
