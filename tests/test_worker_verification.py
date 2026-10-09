# Pytest Test Suite for Worker Identity Verification
import io
import pytest
from tests.helpers import DEMO_WORKER, DEMO_ADMIN, DEMO_CUSTOMER, login

def test_worker_identity_verification_full_flow(client):
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

    # 3. Submit Worker Verification
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
    assert verif_res["aadhaar_last_four"] == "4521"
    verif_id = verif_res["id"]

    # 4. Check status as worker
    status_res = client.get("/api/worker/verification/status", headers=wrk_headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "PENDING_VERIFICATION"
    assert status_res.json()["aadhaar_last_four"] == "4521"

    # 5. Access document as worker
    doc_res = client.get("/api/worker/verification/document/labour_certificate", headers=wrk_headers)
    assert doc_res.status_code == 200

    # 6. Admin lists pending verifications
    admin_list = client.get("/api/admin/worker-verifications?status=pending_verification", headers=adm_headers)
    assert admin_list.status_code == 200
    list_items = admin_list.json()
    assert any(item["id"] == verif_id for item in list_items)

    # 7. Admin views detail
    admin_detail = client.get(f"/api/admin/worker-verifications/{verif_id}", headers=adm_headers)
    assert admin_detail.status_code == 200
    detail_data = admin_detail.json()
    assert detail_data["aadhaar_masked"] == "XXXX XXXX 4521"

    # 8. Admin rejects verification with reason
    reject_res = client.post(
        f"/api/admin/worker-verifications/{verif_id}/reject",
        json={"rejection_reason": "Labour certificate document signature is missing."},
        headers=adm_headers
    )
    assert reject_res.status_code == 200

    # Verify status is REJECTED
    status_rejected = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert status_rejected["status"] == "REJECTED"
    assert "rejection_reason" in status_rejected

    # 9. Worker resubmits
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

    # 10. Admin approves worker verification
    approve_res = client.post(f"/api/admin/worker-verifications/{verif_id}/verify", headers=adm_headers)
    assert approve_res.status_code == 200

    # Verify worker status is now VERIFIED
    status_verified = client.get("/api/worker/verification/status", headers=wrk_headers).json()
    assert status_verified["status"] == "VERIFIED"

    # 11. Security Check: Customers cannot access worker verification endpoints
    unauth_res = client.get("/api/admin/worker-verifications", headers=cust_headers)
    assert unauth_res.status_code == 403
