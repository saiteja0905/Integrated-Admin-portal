"""Tests for the second round of fixes: BUG-16 (disputes), BUG-36 (phone masking),
BUG-44 (worker query when a job is published)."""
import server

from tests.helpers import DEMO_ADMIN, DEMO_CUSTOMER, DEMO_WORKER, create_open_job, hire, login, register


# --------------------------------------------------------------------------- BUG-36
def test_masking_catches_evasions():
    masked = server.mask_phone_numbers("call 9876543210now")
    assert "9876543210" not in masked and "98****10" in masked

    spelled = server.mask_phone_numbers("nine eight seven six five four three two one zero")
    assert "98****10" in spelled

    mixed = server.mask_phone_numbers("my num is 98765 four three two one zero")
    assert "98****10" in mixed and "98765" not in mixed

    # Ordinary numbers must survive untouched
    assert server.mask_phone_numbers("budget is 2500 for 2 rooms") == "budget is 2500 for 2 rooms"
    assert server.mask_phone_numbers("meet at 9 am on 12-09-2026") == "meet at 9 am on 12-09-2026"


def test_chat_masks_number_glued_to_a_word(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    hire(client, customer_headers, worker_headers, worker["id"], job)

    client.post(
        f"/api/jobs/{job['id']}/messages",
        json={"content": "call 9876543210now or nine eight seven six five four three two one zero"},
        headers=worker_headers,
    )
    content = client.get(f"/api/jobs/{job['id']}/messages", headers=customer_headers).json()[0]["content"]
    assert "9876543210" not in content
    assert sum(c.isdigit() for c in content.replace("98****10", "")) < 10


# --------------------------------------------------------------------------- BUG-44
class _RecordingDb:
    """Delegates to the real mock db but records worker_profiles.find() filters."""

    def __init__(self, db, calls):
        self._db = db
        self._calls = calls

    def __getattr__(self, name):
        collection = getattr(self._db, name)
        if name == "worker_profiles":
            calls = self._calls

            class _Spy:
                def __getattr__(self, attr):
                    return getattr(collection, attr)

                def find(self, *args, **kwargs):
                    calls.append(args[0] if args else kwargs.get("filter"))
                    return collection.find(*args, **kwargs)

            return _Spy()
        return collection

    def __getitem__(self, name):
        return self._db[name]


def _set_profile(client, headers, **profile):
    response = client.put("/api/workers/profile", json=profile, headers=headers)
    assert response.status_code == 200, response.text


def test_publishing_a_job_queries_only_candidate_workers(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    near_headers, near_worker = login(client, DEMO_WORKER)
    delhi = {"lat": 28.61, "lng": 77.21, "address": "New Delhi"}

    _set_profile(client, near_headers, skills=["Painting"], preferred_locations=[delhi], service_radius_km=10)

    far = register(client, phone="9000000201", role="worker").json()
    far_headers = {"Authorization": f"Bearer {far['access_token']}"}
    _set_profile(
        client,
        far_headers,
        skills=["Cooking"],
        preferred_locations=[{"lat": 19.07, "lng": 72.87, "address": "Mumbai"}],
        service_radius_km=10,
    )

    skilled = register(client, phone="9000000202", role="worker").json()
    skilled_headers = {"Authorization": f"Bearer {skilled['access_token']}"}
    _set_profile(client, skilled_headers, skills=["Plumbing"], preferred_locations=[])

    job = client.post(
        "/api/jobs",
        json={
            "type": "daily",
            "category": "skilled",
            "title": "Plumbing repair needed",
            "description": "Leaking pipe in the bathroom",
            "location": {"lat": 28.6139, "lng": 77.209, "address": "Connaught Place"},
            "budget_amount": 1500,
        },
        headers=customer_headers,
    ).json()

    calls = []
    real_db = server.db
    server.db = _RecordingDb(real_db, calls)
    try:
        assert client.put(f"/api/jobs/{job['id']}/publish", headers=customer_headers).status_code == 200
    finally:
        server.db = real_db

    # The query must be narrowed in the database, not by loading every profile
    assert calls and calls[0] not in ({}, None), f"worker_profiles.find called with {calls}"
    assert "$or" in calls[0]

    notified = {n["user_id"] for n in await_list(real_db, job["id"])}
    assert near_worker["id"] in notified  # matched on location
    assert skilled["user"]["id"] in notified  # matched on skill
    assert far["user"]["id"] not in notified  # 1100 km away, outside every radius


def await_list(db, job_id):
    """Small helper: read the notifications this job produced."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        db.notifications.find({"data.job_id": job_id}, {"_id": 0}).to_list(length=None)
    )


# --------------------------------------------------------------------------- BUG-16
DISPUTE = {
    "title": "Worker left the job unfinished",
    "description": "The pipe is still leaking and they stopped replying to messages.",
    "category": "quality",
}


def test_customer_can_raise_dispute_and_admin_sees_it(client):
    customer_headers, customer = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    admin_headers, _ = login(client, DEMO_ADMIN)
    job = create_open_job(client, customer_headers)

    # Not allowed before anyone is hired
    too_early = client.post(f"/api/jobs/{job['id']}/dispute", json=DISPUTE, headers=customer_headers)
    assert too_early.status_code == 400

    hire(client, customer_headers, worker_headers, worker["id"], job)

    response = client.post(f"/api/jobs/{job['id']}/dispute", json=DISPUTE, headers=customer_headers)
    assert response.status_code == 200, response.text
    dispute = response.json()
    assert dispute["complainant_id"] == customer["id"]
    assert dispute["respondent_id"] == worker["id"]
    assert dispute["status"] == "open"

    # Both parties can see it; the admin portal lists it too
    assert [d["id"] for d in client.get("/api/disputes", headers=customer_headers).json()] == [dispute["id"]]
    assert [d["id"] for d in client.get("/api/disputes", headers=worker_headers).json()] == [dispute["id"]]
    admin_list = client.get("/api/admin/disputes", headers=admin_headers).json()
    assert dispute["id"] in [d["id"] for d in admin_list]

    # No duplicate while the first one is open
    assert client.post(f"/api/jobs/{job['id']}/dispute", json=DISPUTE, headers=customer_headers).status_code == 400


def test_worker_dispute_targets_the_customer(client):
    customer_headers, customer = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    hire(client, customer_headers, worker_headers, worker["id"], job)

    response = client.post(
        f"/api/jobs/{job['id']}/dispute",
        json={**DISPUTE, "category": "payment", "title": "Customer has not paid"},
        headers=worker_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["respondent_id"] == customer["id"]


def test_outsiders_cannot_raise_disputes_and_input_is_validated(client):
    customer_headers, _ = login(client, DEMO_CUSTOMER)
    worker_headers, worker = login(client, DEMO_WORKER)
    job = create_open_job(client, customer_headers)
    hire(client, customer_headers, worker_headers, worker["id"], job)

    outsider = register(client, phone="9000000203").json()
    outsider_headers = {"Authorization": f"Bearer {outsider['access_token']}"}
    assert client.post(f"/api/jobs/{job['id']}/dispute", json=DISPUTE, headers=outsider_headers).status_code == 403
    assert client.get("/api/disputes", headers=outsider_headers).json() == []

    assert client.post(f"/api/jobs/{job['id']}/dispute", json=DISPUTE).status_code == 401
    bad = client.post(
        f"/api/jobs/{job['id']}/dispute",
        json={"title": "x", "description": "short", "category": "aliens"},
        headers=customer_headers,
    )
    assert bad.status_code == 422
