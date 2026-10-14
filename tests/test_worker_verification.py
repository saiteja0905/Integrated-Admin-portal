# Pytest Test Suite for Worker Identity Verification (Two-Stage & Offline Scheduling)
import io
from datetime import datetime, timezone, timedelta
import pytest
from tests.helpers import DEMO_WORKER, DEMO_ADMIN, DEMO_CUSTOMER, login

def test_worker_identity_verification_two_stage_flow(client):
    wrk_headers, wrk_user = login(client, DEMO_WORKER)
    adm_headers, adm_user = login(client, DEMO_ADMIN)
    cust_headers, cust_user = login(client, DEMO_CUSTOMER)

    # 1. Upload Labour Certificate PDF
    pdf_content = b"%PDF-1.4 Fake PDF Content for Labour Certificate"
    pdf_file = {"file": ("my_certificate.pdf", io.BytesIO(pdf_content), "application/pdf")}
    cert_upload_res = client.post("/api/worker/verification/upload-doc?doc_type=labour_certificate", files=pdf_file, headers=wrk_headers)
    assert cert_upload_res.status_code == 200, cert_upload_res.text
    cert_data = cert_upload_res.json()
    assert "filename" in cert_data

    # 2. Upload Live Photo
    photo_content = b"\xff\xd8\xff\xe0\x00\x10JFIF Fake JPG photo stream"
    photo_file = {"file": ("live_photo.jpg", io.BytesIO(photo_content), "image/jpeg")}
    photo_upload_res = client.post("/api/worker/verification/upload-doc?doc_type=live_photo", files=photo_file, headers=wrk_headers)
    assert photo_upload_res.status_code == 200, photo_upload_res.text
    photo_data = photo_upload_res.json()
    assert "filename" in photo_data

    # 3. Submit Worker Verification (Stage 1 begins)
    submit_res = client.post(
        "/api/worker/verification/submit",
        json={
            "aadhaar_number": "1234 5678 4521",
            "labour_certificate_filename": cert_data["filename"],
            "labour_certificate_name": cert_data["original_name"],
            "live_photo_filename": photo_data["filename"]
        },
        headers=wrk_headers
    )
    assert submit_res.status_code == 200, submit_res.text
    verif_res = submit_res.json()
    assert verif_res["status"] == "PENDING_VERIFICATION"
    assert verif_res["stage1_status"] == "PENDING_REVIEW"
    assert verif_res["stage2_status"] == "NOT_SCHEDULED"
    assert verif_res["is_verified"] is False
    assert verif_res["aadhaar_last_four"] == "4521"
    verif_id = verif_res["id"]

    # 4. Check status as worker
    status_res = client.get("/api/worker/verification/status", headers=wrk_headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "PENDING_VERIFICATION"
    assert status_res.json()["stage1_status"] == "PENDING_REVIEW"
    assert status_res.json()["is_verified"] is False

    # 5. Admin lists pending verifications
    admin_list = client.get("/api/admin/worker-verifications?status=pending_verification", headers=adm_headers)
    assert admin_list.status_code == 200
    list_items = admin_list.json()
    assert any(item["id"] == verif_id for item in list_items)

    # 6. Admin rejects verification with reason (Stage 1 rejection)
    reject_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/reject",
        json={"rejection_reason": "Labour certificate document signature is missing."},
        headers=adm_headers
    )
    assert reject_res.status_code == 200

    # Verify status is REJECTED
    status_rejected = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert status_rejected["status"] == "REJECTED"
    assert status_rejected["stage1_status"] == "REJECTED"
    assert "rejection_reason" in status_rejected

    # Business Rule: Cannot schedule when documents are rejected/pending
    tomorrow_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    unapproved_sched = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Sanyuth South Center",
            "venue_address": "Plot 42, Hitec City, Hyderabad",
            "appointment_date": tomorrow_date,
            "start_time": "10:00",
            "end_time": "11:30",
            "officer_name": "Ramesh Kumar",
            "officer_phone": "9876543210",
            "instructions": "Bring original Aadhaar card and certificate."
        },
        headers=adm_headers
    )
    assert unapproved_sched.status_code == 400
    assert "approved" in unapproved_sched.text.lower()

    # 7. Worker resubmits documents
    resubmit_res = client.post(
        "/api/worker/verification/submit",
        json={
            "aadhaar_number": "1234 5678 4521",
            "labour_certificate_filename": cert_data["filename"],
            "labour_certificate_name": "labour_certificate_updated.pdf",
            "live_photo_filename": photo_data["filename"]
        },
        headers=wrk_headers
    )
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["status"] == "PENDING_VERIFICATION"
    assert resubmit_res.json()["stage1_status"] == "PENDING_REVIEW"

    # 8. Admin approves documents (Stage 1 Approved)
    approve_doc_res = client.post(f"/api/admin/worker-verifications/{verif_id}/approve-documents", headers=adm_headers)
    assert approve_doc_res.status_code == 200
    assert approve_doc_res.json()["status"] == "DOCUMENTS_APPROVED"

    # Check worker status after doc approval: Documents approved, but NOT fully verified yet!
    status_doc_appr = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert status_doc_appr["status"] == "DOCUMENTS_APPROVED"
    assert status_doc_appr["stage1_status"] == "APPROVED"
    assert status_doc_appr["is_verified"] is False

    # 9. Test scheduling validations:
    # A. Past date rejected
    past_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    past_sched = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Sanyuth South Center",
            "venue_address": "Plot 42, Hitec City, Hyderabad",
            "appointment_date": past_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "officer_name": "Ramesh Kumar",
            "officer_phone": "9876543210",
            "instructions": "Bring original Aadhaar."
        },
        headers=adm_headers
    )
    assert past_sched.status_code == 400
    assert "past" in past_sched.text.lower()

    # B. End time <= start time rejected
    invalid_time_sched = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Sanyuth South Center",
            "venue_address": "Plot 42, Hitec City, Hyderabad",
            "appointment_date": tomorrow_date,
            "start_time": "14:00",
            "end_time": "13:00",
            "officer_name": "Ramesh Kumar",
            "officer_phone": "9876543210",
            "instructions": "Bring original Aadhaar."
        },
        headers=adm_headers
    )
    assert invalid_time_sched.status_code == 400
    assert "later than start time" in invalid_time_sched.text.lower()

    # 10. Admin schedules appointment with all required fields & internal admin notes
    sched_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Sanyuth Central Verification Hub",
            "venue_address": "Building 5, Innovation Valley, Madhapur, Hyderabad - 500081",
            "appointment_date": tomorrow_date,
            "start_time": "10:00",
            "end_time": "11:30",
            "officer_name": "Suresh Verma - Lead Officer",
            "officer_phone": "+91 91234 56789",
            "instructions": "Please bring physical Aadhaar card and original Labour Certificate.",
            "admin_notes": "Internal check: Verify trade certificate stamp with Telangana labour board."
        },
        headers=adm_headers
    )
    assert sched_res.status_code == 200, sched_res.text
    sched_data = sched_res.json()
    assert sched_data["status"] == "SCHEDULED"
    assert sched_data["location_name"] == "Sanyuth Central Verification Hub"
    assert len(sched_data["history"]) == 1

    # Duplicate scheduling attempt must be rejected
    dup_sched = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Another Center",
            "venue_address": "Address 123",
            "appointment_date": tomorrow_date,
            "start_time": "10:00",
            "end_time": "11:30",
            "officer_name": "Suresh Verma",
            "officer_phone": "+91 91234 56789",
            "instructions": "Bring ID."
        },
        headers=adm_headers
    )
    assert dup_sched.status_code == 400
    assert "already scheduled" in dup_sched.text.lower()

    # 11. Worker sees appointment details card, but internal admin notes are STRIPPED
    wrk_view = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert wrk_view["status"] == "IN_PERSON_SCHEDULED"
    assert wrk_view["stage2_status"] == "SCHEDULED"
    assert wrk_view["is_verified"] is False  # Scheduling alone does NOT make verified!
    assert "appointment" in wrk_view and wrk_view["appointment"] is not None
    appt = wrk_view["appointment"]
    assert appt["location_name"] == "Sanyuth Central Verification Hub"
    assert appt["appointment_date"] == tomorrow_date
    assert appt["start_time"] == "10:00"
    assert appt["end_time"] == "11:30"
    assert appt["officer_name"] == "Suresh Verma - Lead Officer"
    # Privacy check: internal admin_notes must not be present
    assert "admin_notes" not in appt

    # 12. Admin reschedules appointment
    resched_date = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d")
    resched_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/reschedule-appointment",
        json={
            "appointment_date": resched_date,
            "start_time": "14:00",
            "end_time": "15:30",
            "location_name": "Sanyuth West Verification Desk",
            "reschedule_reason": "Officer travelling; rescheduled to afternoon slot.",
            "admin_notes": "Worker confirmed via phone."
        },
        headers=adm_headers
    )
    assert resched_res.status_code == 200, resched_res.text
    resched_data = resched_res.json()
    assert resched_data["status"] == "RESCHEDULED"
    assert resched_data["appointment_date"] == resched_date
    assert resched_data["reschedule_reason"] == "Officer travelling; rescheduled to afternoon slot."
    assert len(resched_data["history"]) == 2  # History preserved!

    # Worker checks rescheduled appointment
    wrk_resched_view = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert wrk_resched_view["status"] == "IN_PERSON_RESCHEDULED"
    assert wrk_resched_view["stage2_status"] == "RESCHEDULED"
    assert wrk_resched_view["appointment"]["appointment_date"] == resched_date
    assert wrk_resched_view["appointment"]["reschedule_reason"] == "Officer travelling; rescheduled to afternoon slot."

    # 13. Admin cancels appointment
    cancel_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/cancel-appointment",
        json={"cancellation_reason": "Heavy rain forecast; center temporarily closed."},
        headers=adm_headers
    )
    assert cancel_res.status_code == 200
    status_cancelled = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert status_cancelled["stage2_status"] == "CANCELLED"
    assert status_cancelled["is_verified"] is False

    # 14. Admin schedules a new appointment after cancellation
    sched_new_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
    sched_new_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Sanyuth Central Verification Hub",
            "venue_address": "Building 5, Innovation Valley, Madhapur, Hyderabad - 500081",
            "appointment_date": sched_new_date,
            "start_time": "11:00",
            "end_time": "12:00",
            "officer_name": "Priya Sharma",
            "officer_phone": "+91 99887 76655",
            "instructions": "Bring original Aadhaar card and certificate."
        },
        headers=adm_headers
    )
    assert sched_new_res.status_code == 200

    # 15. Outcome recording:
    # A. Failure requires a reason
    fail_no_reason = client.post(
        f"/api/admin/worker-verifications/{verif_id}/record-outcome",
        json={"outcome": "FAILED", "outcome_reason": ""},
        headers=adm_headers
    )
    assert fail_no_reason.status_code == 400

    # B. Record No-Show with reason
    noshow_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/record-outcome",
        json={"outcome": "NO_SHOW", "outcome_reason": "Worker did not appear for scheduled time."},
        headers=adm_headers
    )
    assert noshow_res.status_code == 200
    status_noshow = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert status_noshow["stage2_status"] == "NO_SHOW"
    assert status_noshow["is_verified"] is False

    # C. Reschedule and record PASSED
    pass_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    client.post(
        f"/api/admin/worker-verifications/{verif_id}/reschedule-appointment",
        json={
            "appointment_date": pass_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "reschedule_reason": "Worker rescheduled after missing initial slot."
        },
        headers=adm_headers
    )

    pass_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/record-outcome",
        json={"outcome": "PASSED", "outcome_reason": "Aadhaar and labour certificate verified in-person. Biometrics match."},
        headers=adm_headers
    )
    assert pass_res.status_code == 200
    assert pass_res.json()["status"] == "FULLY_VERIFIED"
    assert pass_res.json()["stage2_status"] == "PASSED"

    # Worker is now FULLY VERIFIED!
    final_wrk = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert final_wrk["status"] == "FULLY_VERIFIED"
    assert final_wrk["stage1_status"] == "APPROVED"
    assert final_wrk["stage2_status"] == "PASSED"
    assert final_wrk["is_verified"] is True

    # 16. Security & Authorization Checks:
    # Customer cannot schedule, reschedule, cancel, or record outcome
    unauth_sched = client.post(
        f"/api/admin/worker-verifications/{verif_id}/schedule-appointment",
        json={
            "location_name": "Hub Center",
            "venue_address": "Plot 42, Hitec City, Hyderabad",
            "appointment_date": tomorrow_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "officer_name": "Officer Name",
            "officer_phone": "9876543210",
            "instructions": "Bring original ID cards."
        },
        headers=cust_headers
    )
    assert unauth_sched.status_code == 403

    unauth_outcome = client.post(
        f"/api/admin/worker-verifications/{verif_id}/record-outcome",
        json={"outcome": "PASSED"},
        headers=cust_headers
    )
    assert unauth_outcome.status_code == 403

    unauth_admin_list = client.get("/api/admin/worker-verifications", headers=wrk_headers)
    assert unauth_admin_list.status_code == 403
