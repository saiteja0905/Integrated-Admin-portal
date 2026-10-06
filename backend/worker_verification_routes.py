# FastAPI Router for Worker Identity Verification
import logging
import os
import uuid
import re
import base64
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

worker_verification_router = APIRouter(prefix="/api", tags=["worker_verification"])

# Helper function to get DB and dependencies lazily from server
def get_db():
    from server import db
    return db

def get_current_user_dep():
    from server import get_current_user
    return get_current_user

def require_role_dep(role: str):
    from server import require_role
    return require_role(role)

def get_secret_key():
    from server import SECRET_KEY
    return SECRET_KEY

# Private Storage directory for sensitive documents
def get_private_dir() -> Path:
    from server import UPLOAD_DIR
    p_dir = UPLOAD_DIR / "private_verifications"
    p_dir.mkdir(parents=True, exist_ok=True)
    return p_dir

# Encryption helpers for Aadhaar at rest
def encrypt_aadhaar(aadhaar: str) -> str:
    secret_key = get_secret_key()
    key = hashlib.sha256(secret_key.encode()).digest()
    raw_bytes = aadhaar.encode()
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw_bytes)])
    return base64.b64encode(encrypted).decode()

def decrypt_aadhaar(encrypted_b64: str) -> str:
    secret_key = get_secret_key()
    key = hashlib.sha256(secret_key.encode()).digest()
    encrypted = base64.b64decode(encrypted_b64.encode())
    raw = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
    return raw.decode()

def normalize_aadhaar(raw: str) -> str:
    """Strips spaces and dashes and ensures 12 digits."""
    digits = re.sub(r"\D", "", raw or "")
    return digits

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class VerificationStatusEnum(str):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class WorkerVerificationSubmit(BaseModel):
    aadhaar_number: str
    labour_certificate_filename: str
    labour_certificate_name: str
    live_photo_filename: str

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, value):
        digits = normalize_aadhaar(value)
        if len(digits) != 12:
            raise ValueError("Aadhaar number must contain exactly 12 digits.")
        return digits

class WorkerVerificationStatusResponse(BaseModel):
    id: Optional[str] = None
    worker_id: str
    status: str
    aadhaar_last_four: Optional[str] = None
    labour_certificate_name: Optional[str] = None
    labour_certificate_url: Optional[str] = None
    live_photo_url: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

class AdminRejectRequest(BaseModel):
    rejection_reason: str = Field(min_length=3, max_length=1000)

# =============================================================================
# WORKER UPLOAD & SUBMISSION ENDPOINTS
# =============================================================================

@worker_verification_router.post("/worker/verification/upload-doc")
async def upload_verification_doc(
    doc_type: str = Query(..., description="labour_certificate or live_photo"),
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_user_dep())
):
    """Securely upload sensitive verification file into private storage."""
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers can upload verification documents.")

    if doc_type not in ("labour_certificate", "live_photo"):
        raise HTTPException(status_code=400, detail="Invalid doc_type. Expected 'labour_certificate' or 'live_photo'.")

    file_ext = os.path.splitext(file.filename or "")[1].lower()

    # Read header bytes to validate file magic bytes
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    if doc_type == "labour_certificate":
        if file_ext != ".pdf" or not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Labour certificate must be a valid PDF file.")
    elif doc_type == "live_photo":
        allowed_exts = (".jpg", ".jpeg", ".png", ".webp")
        is_valid_image = (
            content.startswith(b"\xff\xd8\xff") or
            content.startswith(b"\x89PNG\r\n\x1a\n") or
            (content[:4] == b"RIFF" and content[8:12] == b"WEBP")
        )
        if file_ext not in allowed_exts or not is_valid_image:
            raise HTTPException(status_code=400, detail="Live photo must be a valid JPG, PNG, or WEBP image.")

    safe_filename = f"{uuid.uuid4()}{file_ext}"
    private_dir = get_private_dir()
    file_path = private_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": safe_filename,
        "original_name": file.filename or ("labour_certificate.pdf" if doc_type == "labour_certificate" else "live_photo.jpg")
    }


@worker_verification_router.post("/worker/verification/submit", response_model=WorkerVerificationStatusResponse)
async def submit_worker_verification(
    payload: WorkerVerificationSubmit,
    current_user: Any = Depends(get_current_user_dep())
):
    """Submit or resubmit worker identity verification details."""
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers can submit identity verification.")

    db = get_db()
    private_dir = get_private_dir()

    # Validate that uploaded files exist in private storage
    cert_path = private_dir / payload.labour_certificate_filename
    photo_path = private_dir / payload.live_photo_filename

    if not cert_path.is_file():
        raise HTTPException(status_code=400, detail="Uploaded Labour Certificate file not found. Please upload again.")
    if not photo_path.is_file():
        raise HTTPException(status_code=400, detail="Uploaded Live Photograph file not found. Please upload again.")

    normalized_aadhaar = normalize_aadhaar(payload.aadhaar_number)
    aadhaar_last_four = normalized_aadhaar[-4:]
    aadhaar_encrypted = encrypt_aadhaar(normalized_aadhaar)

    # Get worker profile info
    worker_profile = await db.worker_profiles.find_one({"user_id": current_user.id})
    skills = worker_profile.get("skills", []) if worker_profile else []
    trade_summary = ", ".join(skills) if skills else "General Service Worker"

    existing_verif = await db.worker_verifications.find_one({"worker_id": current_user.id})
    verif_id = existing_verif["id"] if existing_verif else str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    verif_doc = {
        "id": verif_id,
        "worker_id": current_user.id,
        "worker_name": current_user.name,
        "worker_phone": current_user.phone,
        "worker_trade": trade_summary,
        "aadhaar_last_four": aadhaar_last_four,
        "aadhaar_encrypted": aadhaar_encrypted,
        "labour_certificate_filename": payload.labour_certificate_filename,
        "labour_certificate_name": payload.labour_certificate_name,
        "live_photo_filename": payload.live_photo_filename,
        "status": VerificationStatusEnum.PENDING_VERIFICATION,
        "rejection_reason": None,
        "submitted_at": now,
        "reviewed_at": None,
        "reviewed_by": None,
        "created_at": existing_verif.get("created_at", now) if existing_verif else now,
        "updated_at": now
    }

    await db.worker_verifications.replace_one({"worker_id": current_user.id}, verif_doc, upsert=True)
    await db.users.update_one({"id": current_user.id}, {"$set": {"verification_status": VerificationStatusEnum.PENDING_VERIFICATION}})
    await db.worker_profiles.update_one({"user_id": current_user.id}, {"$set": {"verification_status": VerificationStatusEnum.PENDING_VERIFICATION}})

    # Create worker notification
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "type": "verification_status",
        "title": "Verification Submitted",
        "message": "Your worker identity verification documents have been submitted successfully and are pending admin review.",
        "read": False,
        "created_at": now
    }
    await db.notifications.insert_one(notification_doc)

    # Log audit
    audit_doc = {
        "id": str(uuid.uuid4()),
        "action": "WORKER_VERIFICATION_SUBMITTED",
        "user_id": current_user.id,
        "details": {"verification_id": verif_id, "status": VerificationStatusEnum.PENDING_VERIFICATION},
        "timestamp": now
    }
    await db.audit_logs.insert_one(audit_doc)

    return WorkerVerificationStatusResponse(
        id=verif_id,
        worker_id=current_user.id,
        status=VerificationStatusEnum.PENDING_VERIFICATION,
        aadhaar_last_four=aadhaar_last_four,
        labour_certificate_name=payload.labour_certificate_name,
        labour_certificate_url="/api/worker/verification/document/labour_certificate",
        live_photo_url="/api/worker/verification/document/live_photo",
        submitted_at=now
    )


@worker_verification_router.get("/worker/verification/status", response_model=WorkerVerificationStatusResponse)
async def get_worker_verification_status(
    current_user: Any = Depends(get_current_user_dep())
):
    """Fetch current worker verification status for the logged-in worker."""
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers have identity verification status.")

    db = get_db()
    verif = await db.worker_verifications.find_one({"worker_id": current_user.id})
    if not verif:
        return WorkerVerificationStatusResponse(
            worker_id=current_user.id,
            status=VerificationStatusEnum.NOT_SUBMITTED
        )

    return WorkerVerificationStatusResponse(
        id=verif["id"],
        worker_id=current_user.id,
        status=verif.get("status", VerificationStatusEnum.NOT_SUBMITTED),
        aadhaar_last_four=verif.get("aadhaar_last_four"),
        labour_certificate_name=verif.get("labour_certificate_name"),
        labour_certificate_url="/api/worker/verification/document/labour_certificate",
        live_photo_url="/api/worker/verification/document/live_photo",
        rejection_reason=verif.get("rejection_reason"),
        submitted_at=verif.get("submitted_at"),
        verified_at=verif.get("verified_at")
    )


@worker_verification_router.get("/worker/verification/document/{doc_type}")
async def get_worker_verification_document(
    doc_type: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Securely stream/download worker verification document for the logged-in worker."""
    if doc_type not in ("labour_certificate", "live_photo"):
        raise HTTPException(status_code=400, detail="Invalid document type.")

    db = get_db()
    verif = await db.worker_verifications.find_one({"worker_id": current_user.id})
    if not verif:
        raise HTTPException(status_code=404, detail="No verification record found.")

    filename = verif.get("labour_certificate_filename") if doc_type == "labour_certificate" else verif.get("live_photo_filename")
    if not filename:
        raise HTTPException(status_code=404, detail="Document not found.")

    private_dir = get_private_dir()
    file_path = private_dir / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file does not exist.")

    media_type = "application/pdf" if doc_type == "labour_certificate" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type, filename=verif.get("labour_certificate_name") if doc_type == "labour_certificate" else "live_photo.jpg")


# =============================================================================
# ADMIN WORKER VERIFICATION ENDPOINTS
# =============================================================================

@worker_verification_router.get("/admin/worker-verifications")
async def list_admin_worker_verifications(
    status_filter: Optional[str] = Query("all", alias="status"),
    search: Optional[str] = Query(None),
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin endpoint to list worker verification requests."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    query: Dict[str, Any] = {}

    if status_filter and status_filter.lower() != "all":
        query["status"] = status_filter.upper()

    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"worker_name": {"$regex": pattern, "$options": "i"}},
            {"worker_phone": {"$regex": pattern, "$options": "i"}},
            {"worker_trade": {"$regex": pattern, "$options": "i"}},
        ]

    verifications = await db.worker_verifications.find(query).sort("submitted_at", -1).to_list(length=1000)

    res = []
    for v in verifications:
        res.append({
            "id": v["id"],
            "worker_id": v["worker_id"],
            "worker_name": v.get("worker_name", "Worker"),
            "worker_phone": v.get("worker_phone", ""),
            "worker_trade": v.get("worker_trade", "General"),
            "aadhaar_last_four": v.get("aadhaar_last_four", "XXXX"),
            "labour_certificate_name": v.get("labour_certificate_name", "labour_certificate.pdf"),
            "status": v.get("status", VerificationStatusEnum.PENDING_VERIFICATION),
            "rejection_reason": v.get("rejection_reason"),
            "submitted_at": v.get("submitted_at"),
            "reviewed_at": v.get("reviewed_at")
        })

    return res


@worker_verification_router.get("/admin/worker-verifications/{verification_id}")
async def get_admin_worker_verification_detail(
    verification_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin endpoint to view verification details for review."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification request not found.")

    return {
        "id": v["id"],
        "worker_id": v["worker_id"],
        "worker_name": v.get("worker_name", "Worker"),
        "worker_phone": v.get("worker_phone", ""),
        "worker_trade": v.get("worker_trade", "General"),
        "aadhaar_masked": f"XXXX XXXX {v.get('aadhaar_last_four', 'XXXX')}",
        "labour_certificate_name": v.get("labour_certificate_name", "labour_certificate.pdf"),
        "labour_certificate_url": f"/api/admin/worker-verifications/{verification_id}/document/labour_certificate",
        "live_photo_url": f"/api/admin/worker-verifications/{verification_id}/document/live_photo",
        "status": v.get("status", VerificationStatusEnum.PENDING_VERIFICATION),
        "rejection_reason": v.get("rejection_reason"),
        "submitted_at": v.get("submitted_at"),
        "reviewed_at": v.get("reviewed_at")
    }


@worker_verification_router.get("/admin/worker-verifications/{verification_id}/document/{doc_type}")
async def get_admin_verification_document(
    verification_id: str,
    doc_type: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin endpoint to securely view/download verification document."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    if doc_type not in ("labour_certificate", "live_photo"):
        raise HTTPException(status_code=400, detail="Invalid document type.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    filename = v.get("labour_certificate_filename") if doc_type == "labour_certificate" else v.get("live_photo_filename")
    if not filename:
        raise HTTPException(status_code=404, detail="Document not found.")

    private_dir = get_private_dir()
    file_path = private_dir / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file does not exist.")

    media_type = "application/pdf" if doc_type == "labour_certificate" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type, filename=v.get("labour_certificate_name") if doc_type == "labour_certificate" else "live_photo.jpg")


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/verify")
async def approve_worker_verification(
    verification_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin approves worker identity verification."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    now = datetime.now(timezone.utc)
    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "status": VerificationStatusEnum.VERIFIED,
            "verified_at": now,
            "reviewed_at": now,
            "reviewed_by": current_user.id,
            "updated_at": now
        }}
    )

    worker_id = v["worker_id"]
    await db.users.update_one({"id": worker_id}, {"$set": {"verification_status": VerificationStatusEnum.VERIFIED, "is_verified": True}})
    await db.worker_profiles.update_one({"user_id": worker_id}, {"$set": {"verification_status": VerificationStatusEnum.VERIFIED, "is_verified": True}})

    # Notification
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": worker_id,
        "type": "verification_status",
        "title": "Verification Approved!",
        "message": "Your worker identity verification has been approved. You are now a verified worker on Sanyuth!",
        "read": False,
        "created_at": now
    }
    await db.notifications.insert_one(notification_doc)

    # Audit log
    audit_doc = {
        "id": str(uuid.uuid4()),
        "action": "WORKER_VERIFIED",
        "user_id": worker_id,
        "admin_id": current_user.id,
        "details": {"verification_id": verification_id},
        "timestamp": now
    }
    await db.audit_logs.insert_one(audit_doc)

    return {"message": "Worker verified successfully."}


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/reject")
async def reject_worker_verification(
    verification_id: str,
    payload: AdminRejectRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin rejects worker identity verification with a reason."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    reason = payload.rejection_reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    now = datetime.now(timezone.utc)
    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "status": VerificationStatusEnum.REJECTED,
            "rejection_reason": reason,
            "reviewed_at": now,
            "reviewed_by": current_user.id,
            "updated_at": now
        }}
    )

    worker_id = v["worker_id"]
    await db.users.update_one({"id": worker_id}, {"$set": {"verification_status": VerificationStatusEnum.REJECTED, "is_verified": False}})
    await db.worker_profiles.update_one({"user_id": worker_id}, {"$set": {"verification_status": VerificationStatusEnum.REJECTED, "is_verified": False}})

    # Notification
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": worker_id,
        "type": "verification_status",
        "title": "Verification Update Needed",
        "message": f"Your worker identity verification requires changes: {reason}",
        "read": False,
        "created_at": now
    }
    await db.notifications.insert_one(notification_doc)

    # Audit log
    audit_doc = {
        "id": str(uuid.uuid4()),
        "action": "WORKER_REJECTED",
        "user_id": worker_id,
        "admin_id": current_user.id,
        "details": {"verification_id": verification_id, "rejection_reason": reason},
        "timestamp": now
    }
    await db.audit_logs.insert_one(audit_doc)

    return {"message": "Worker verification rejected with reason."}
