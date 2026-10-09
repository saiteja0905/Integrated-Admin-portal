# Pytest Test Suite for 5 New Sanyuth Features
import pytest
from datetime import datetime, timezone
from tests.helpers import DEMO_CUSTOMER, DEMO_WORKER, DEMO_ADMIN, login, create_open_job

def test_scope_agreement_flow(client):
    cust_headers, cust_user = login(client, DEMO_CUSTOMER)
    wrk_headers, wrk_user = login(client, DEMO_WORKER)

    # 1. Create open job & assign
    job = create_open_job(client, cust_headers, title="Kitchen Leak Repair", budget_amount=1800)
    job_id = job["id"]

    # Worker applies
    client.post(f"/api/jobs/{job_id}/apply", json={"message": "I can fix it today"}, headers=wrk_headers)

    # Customer assigns worker
    assign_res = client.post(f"/api/jobs/{job_id}/assign?worker_id={wrk_user['id']}", headers=cust_headers)
    assert assign_res.status_code == 200, assign_res.text

    # 2. Get Scope Agreement
    ag_res = client.get(f"/api/agreements/job/{job_id}", headers=cust_headers)
    assert ag_res.status_code == 200
    ag_data = ag_res.json()
    agreement_id = ag_data["id"]
    assert ag_data["status"] == "draft"

    # 3. Customer agrees
    cust_agree = client.post(f"/api/agreements/{agreement_id}/agree", headers=cust_headers)
    assert cust_agree.status_code == 200

    # 4. Worker agrees -> becomes ACTIVE
    wrk_agree = client.post(f"/api/agreements/{agreement_id}/agree", headers=wrk_headers)
    assert wrk_agree.status_code == 200
    assert wrk_agree.json()["status"] == "active"

    # 5. Worker creates Change Request
    cr_res = client.post(
        f"/api/agreements/{agreement_id}/change-requests",
        json={
            "description": "Replace main PVC valve",
            "price_change": 400.0,
            "new_agreed_price": 2200.0,
            "additional_notes": "Valve heavily corroded"
        },
        headers=wrk_headers
    )
    assert cr_res.status_code == 200
    cr_id = cr_res.json()["id"]

    # 6. Customer approves Change Request
    resp_res = client.post(
        f"/api/agreements/change-requests/{cr_id}/respond",
        json={"status": "approved", "response_notes": "Approved additional valve replacement"},
        headers=cust_headers
    )
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "approved"

    # Verify updated price in agreement
    final_ag = client.get(f"/api/agreements/job/{job_id}", headers=cust_headers).json()
    assert final_ag["agreed_price"] == 2200.0


def test_job_chaining_day_planner(client):
    wrk_headers, wrk_user = login(client, DEMO_WORKER)

    # Fetch Day Planner
    plan_res = client.get("/api/planner/day-plan", headers=wrk_headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert "timeline" in plan
    assert "suggested_jobs" in plan

    # Test 1-Tap Quick Bid on suggested job if present
    if plan["suggested_jobs"]:
        sugg = plan["suggested_jobs"][0]
        bid_res = client.post(
            "/api/planner/quick-bid",
            json={
                "job_id": sugg["job_id"],
                "bid_amount": sugg["estimated_earnings"],
                "visiting_charge": 0.0,
                "message": "Quick Bid test"
            },
            headers=wrk_headers
        )
        assert bid_res.status_code == 200
        assert "bid_id" in bid_res.json()


def test_family_mode_flow(client):
    cust_headers, cust_user = login(client, DEMO_CUSTOMER)
    wrk_headers, wrk_user = login(client, DEMO_WORKER)

    # 1. Create parent address
    addr_res = client.post(
        "/api/family/addresses",
        json={
            "parent_name": "Sita Sharma (Mother)",
            "parent_phone": "9876543333",
            "address": "Plot 15, Madhapur",
            "city": "Hyderabad",
            "preferred_language": "Telugu"
        },
        headers=cust_headers
    )
    assert addr_res.status_code == 200
    addr_id = addr_res.json()["id"]

    # List parent addresses
    list_res = client.get("/api/family/addresses", headers=cust_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 2. Create family booking
    family_payload = {
        "title": "Mother's AC Servicing",
        "description": "Clean filters and top-up gas for parents",
        "category": "skilled",
        "budget_amount": 1200.0,
        "parent_name": "Sita Sharma",
        "parent_phone": "9876543333",
        "address": "Plot 15, Madhapur",
        "city": "Hyderabad",
        "preferred_language": "Telugu"
    }
    j_res = client.post("/api/family/bookings", json=family_payload, headers=cust_headers)
    assert j_res.status_code == 200
    job_id = j_res.json()["job_id"]
    otp = j_res.json()["parent_otp"]

    # Parent booking details
    track_res = client.get(f"/api/family/bookings/{job_id}", headers=cust_headers)
    assert track_res.status_code == 200
    assert track_res.json()["parent_name"] == "Sita Sharma"

    # Worker verifies arrival OTP
    otp_res = client.post(
        f"/api/family/bookings/{job_id}/verify-otp",
        json={"otp": otp},
        headers=wrk_headers
    )
    assert otp_res.status_code == 200
    assert otp_res.json()["verified"] is True

    # Support request
    supp_res = client.post(
        f"/api/family/bookings/{job_id}/support",
        json={"message": "Parent requested call back"},
        headers=cust_headers
    )
    assert supp_res.status_code == 200


def test_fair_start_new_worker_eligibility(client):
    wrk_headers, wrk_user = login(client, DEMO_WORKER)
    admin_headers, _ = login(client, DEMO_ADMIN)

    # Check eligibility
    elig_res = client.get("/api/fair-start/eligibility", headers=wrk_headers)
    assert elig_res.status_code == 200
    elig = elig_res.json()
    assert "is_eligible" in elig
    assert elig["badge_label"] == "New on Sanyuth"

    # Admin fair start view
    admin_res = client.get("/api/admin/fair-start", headers=admin_headers)
    assert admin_res.status_code == 200
    assert "eligible_new_workers" in admin_res.json()


def test_ask_a_pro_qa_flow(client):
    cust_headers, cust_user = login(client, DEMO_CUSTOMER)
    wrk_headers, wrk_user = login(client, DEMO_WORKER)

    # 1. Customer asks a question
    q_res = client.post(
        "/api/ask-pro/questions",
        json={
            "title": "Why does my fuse trip when turning on microwave?",
            "description": "Every time microwave starts, main circuit breaker trips.",
            "category": "electrical",
            "language": "English"
        },
        headers=cust_headers
    )
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    # 2. List questions
    list_res = client.get("/api/ask-pro/questions?category=electrical")
    assert list_res.status_code == 200
    assert any(q["id"] == q_id for q in list_res.json())

    # 3. Verified worker answers
    ans_res = client.post(
        f"/api/ask-pro/questions/{q_id}/answers",
        json={"answer_text": "Your microwave has an internal short circuit or the breaker amperage rating is too low."},
        headers=wrk_headers
    )
    assert ans_res.status_code == 200
    ans_id = ans_res.json()["id"]

    # 4. Customer marks answer as Most Helpful
    mark_res = client.post(f"/api/ask-pro/answers/{ans_id}/mark-helpful", headers=cust_headers)
    assert mark_res.status_code == 200

    # 5. Verify worker score incremented
    score_res = client.get(f"/api/ask-pro/workers/{wrk_user['id']}/pro-score")
    assert score_res.status_code == 200
    assert score_res.json()["helpful_pro_points"] >= 1
