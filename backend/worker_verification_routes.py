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
# STATUS CONSTANTS & ENUMS
# =============================================================================

class VerificationStatusEnum(str):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    DOCUMENTS_APPROVED = "DOCUMENTS_APPROVED"
    IN_PERSON_SCHEDULED = "IN_PERSON_SCHEDULED"
    IN_PERSON_RESCHEDULED = "IN_PERSON_RESCHEDULED"
    IN_PERSON_FAILED = "IN_PERSON_FAILED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"
    VERIFIED = "VERIFIED"
    FULLY_VERIFIED = "FULLY_VERIFIED"
    REJECTED = "REJECTED"

class Stage1Status(str):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Stage2Status(str):
    NOT_SCHEDULED = "NOT_SCHEDULED"
    SCHEDULED = "SCHEDULED"
    RESCHEDULED = "RESCHEDULED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"

class OverallVerificationStatus(str):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    DOCUMENTS_APPROVED = "DOCUMENTS_APPROVED"
    IN_PERSON_SCHEDULED = "IN_PERSON_SCHEDULED"
    IN_PERSON_RESCHEDULED = "IN_PERSON_RESCHEDULED"
    IN_PERSON_FAILED = "IN_PERSON_FAILED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"
    FULLY_VERIFIED = "FULLY_VERIFIED"
    REJECTED = "REJECTED"

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

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
    stage1_status: Optional[str] = None
    stage2_status: Optional[str] = None
    is_verified: bool = False
    aadhaar_last_four: Optional[str] = None
    labour_certificate_name: Optional[str] = None
    labour_certificate_url: Optional[str] = None
    live_photo_url: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    appointment: Optional[Dict[str, Any]] = None

class AdminRejectRequest(BaseModel):
    rejection_reason: str = Field(min_length=3, max_length=1000)

class ScheduleAppointmentRequest(BaseModel):
    location_name: str = Field(..., min_length=2, max_length=200)
    venue_address: str = Field(..., min_length=5, max_length=500)
    appointment_date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM (24-hour)")
    end_time: str = Field(..., description="HH:MM (24-hour)")
    officer_name: str = Field(..., min_length=2, max_length=100)
    officer_phone: str = Field(..., min_length=5, max_length=20)
    officer_photo_url: Optional[str] = Field(None, max_length=500)
    instructions: str = Field(
        default="Please bring your original physical Aadhaar card, physical Labour Certificate, and government photo ID.",
        min_length=5,
        max_length=1000
    )
    admin_notes: Optional[str] = Field(None, max_length=1000)

class RescheduleAppointmentRequest(BaseModel):
    appointment_date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM (24-hour)")
    end_time: str = Field(..., description="HH:MM (24-hour)")
    location_name: Optional[str] = Field(None, min_length=2, max_length=200)
    venue_address: Optional[str] = Field(None, min_length=5, max_length=500)
    officer_name: Optional[str] = Field(None, min_length=2, max_length=100)
    officer_phone: Optional[str] = Field(None, min_length=5, max_length=20)
    officer_photo_url: Optional[str] = None
    instructions: Optional[str] = Field(None, min_length=5, max_length=1000)
    reschedule_reason: str = Field(..., min_length=3, max_length=500)
    admin_notes: Optional[str] = Field(None, max_length=1000)

class CancelAppointmentRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=3, max_length=500)

class RecordOutcomeRequest(BaseModel):
    outcome: Literal["PASSED", "FAILED", "NO_SHOW"]
    outcome_reason: Optional[str] = Field(None, max_length=1000)
    admin_notes: Optional[str] = Field(None, max_length=1000)

# =============================================================================
# VALIDATION & HELPER FUNCTIONS
# =============================================================================

def validate_appointment_schedule(appointment_date_str: str, start_time_str: str, end_time_str: str):
    try:
        appt_date = datetime.strptime(appointment_date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment_date format. Please use YYYY-MM-DD."
        )

    today_date = datetime.now(timezone.utc).date()
    if appt_date < today_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment date cannot be in the past."
        )

    time_regex = r"^([01]?\d|2[0-3]):([0-5]\d)$"
    if not re.match(time_regex, start_time_str.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid start_time format. Please use HH:MM (24-hour)."
        )
    if not re.match(time_regex, end_time_str.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid end_time format. Please use HH:MM (24-hour)."
        )

    start_dt = datetime.strptime(start_time_str.strip(), "%H:%M")
    end_dt = datetime.strptime(end_time_str.strip(), "%H:%M")
    if end_dt <= start_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment end time must be later than start time."
        )

def sanitize_appointment_for_worker(appt: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Strips internal admin notes and private metadata from appointment for worker privacy."""
    if not appt:
        return None
    appt_copy = dict(appt)
    appt_copy.pop("admin_notes", None)
    appt_copy.pop("_id", None)
    if "history" in appt_copy and isinstance(appt_copy["history"], list):
        sanitized_history = []
        for h in appt_copy["history"]:
            h_copy = dict(h)
            h_copy.pop("notes", None)
            h_copy.pop("admin_notes", None)
            sanitized_history.append(h_copy)
        appt_copy["history"] = sanitized_history
    return appt_copy

async def send_worker_notification(db, worker_id: str, title: str, message: str, notif_type: str = "verification_status"):
    now = datetime.now(timezone.utc)
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": worker_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "read": False,
        "is_read": False,
        "data": {"type": notif_type},
        "created_at": now
    }
    await db.notifications.insert_one(notification_doc)

async def log_audit(db, action: str, user_id: str, admin_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    now = datetime.now(timezone.utc)
    audit_doc = {
        "id": str(uuid.uuid4()),
        "action": action,
        "user_id": user_id,
        "admin_id": admin_id,
        "details": details or {},
        "timestamp": now
    }
    await db.audit_logs.insert_one(audit_doc)

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

    cert_path = private_dir / payload.labour_certificate_filename
    photo_path = private_dir / payload.live_photo_filename

    if not cert_path.is_file():
        raise HTTPException(status_code=400, detail="Uploaded Labour Certificate file not found. Please upload again.")
    if not photo_path.is_file():
        raise HTTPException(status_code=400, detail="Uploaded Live Photograph file not found. Please upload again.")

    normalized_aadhaar = normalize_aadhaar(payload.aadhaar_number)
    aadhaar_last_four = normalized_aadhaar[-4:]
    aadhaar_encrypted = encrypt_aadhaar(normalized_aadhaar)

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
        "status": OverallVerificationStatus.PENDING_VERIFICATION,
        "stage1_status": Stage1Status.PENDING_REVIEW,
        "stage2_status": Stage2Status.NOT_SCHEDULED,
        "current_appointment_id": None,
        "rejection_reason": None,
        "submitted_at": now,
        "reviewed_at": None,
        "reviewed_by": None,
        "verified_at": None,
        "created_at": existing_verif.get("created_at", now) if existing_verif else now,
        "updated_at": now
    }

    await db.worker_verifications.replace_one({"worker_id": current_user.id}, verif_doc, upsert=True)
    await db.users.update_one({"id": current_user.id}, {"$set": {"verification_status": OverallVerificationStatus.PENDING_VERIFICATION, "is_verified": False}})
    await db.worker_profiles.update_one({"user_id": current_user.id}, {"$set": {"verification_status": OverallVerificationStatus.PENDING_VERIFICATION, "is_verified": False}})

    await send_worker_notification(
        db,
        current_user.id,
        title="Verification Submitted",
        message="Your worker identity verification documents have been submitted successfully and are pending admin review."
    )

    await log_audit(
        db,
        action="WORKER_VERIFICATION_SUBMITTED",
        user_id=current_user.id,
        details={"verification_id": verif_id, "status": OverallVerificationStatus.PENDING_VERIFICATION}
    )

    return WorkerVerificationStatusResponse(
        id=verif_id,
        worker_id=current_user.id,
        status=OverallVerificationStatus.PENDING_VERIFICATION,
        stage1_status=Stage1Status.PENDING_REVIEW,
        stage2_status=Stage2Status.NOT_SCHEDULED,
        is_verified=False,
        aadhaar_last_four=aadhaar_last_four,
        labour_certificate_name=payload.labour_certificate_name,
        labour_certificate_url="/api/worker/verification/document/labour_certificate",
        live_photo_url="/api/worker/verification/document/live_photo",
        submitted_at=now,
        appointment=None
    )


@worker_verification_router.get("/worker/verification/status", response_model=WorkerVerificationStatusResponse)
async def get_worker_verification_status(
    current_user: Any = Depends(get_current_user_dep())
):
    """Fetch current worker verification status for the logged-in worker, including sanitized appointment details."""
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers have identity verification status.")

    db = get_db()
    verif = await db.worker_verifications.find_one({"worker_id": current_user.id})
    if not verif:
        return WorkerVerificationStatusResponse(
            worker_id=current_user.id,
            status=OverallVerificationStatus.NOT_SUBMITTED,
            stage1_status=Stage1Status.PENDING_REVIEW,
            stage2_status=Stage2Status.NOT_SCHEDULED,
            is_verified=False
        )

    appointment_doc = None
    if verif.get("current_appointment_id"):
        appointment_doc = await db.verification_appointments.find_one({"id": verif["current_appointment_id"]})
    if not appointment_doc:
        appointment_doc = await db.verification_appointments.find_one(
            {"worker_id": current_user.id},
            sort=[("created_at", -1)]
        )

    sanitized_appointment = sanitize_appointment_for_worker(appointment_doc)

    is_fully_verified = (
        (verif.get("status") in (OverallVerificationStatus.FULLY_VERIFIED, VerificationStatusEnum.VERIFIED)) and
        (verif.get("stage2_status") == Stage2Status.PASSED or verif.get("status") == VerificationStatusEnum.VERIFIED)
    )

    return WorkerVerificationStatusResponse(
        id=verif["id"],
        worker_id=current_user.id,
        status=verif.get("status", OverallVerificationStatus.NOT_SUBMITTED),
        stage1_status=verif.get("stage1_status", Stage1Status.PENDING_REVIEW),
        stage2_status=verif.get("stage2_status", Stage2Status.NOT_SCHEDULED),
        is_verified=is_fully_verified,
        aadhaar_last_four=verif.get("aadhaar_last_four"),
        labour_certificate_name=verif.get("labour_certificate_name"),
        labour_certificate_url="/api/worker/verification/document/labour_certificate",
        live_photo_url="/api/worker/verification/document/live_photo",
        rejection_reason=verif.get("rejection_reason"),
        submitted_at=verif.get("submitted_at"),
        verified_at=verif.get("verified_at"),
        appointment=sanitized_appointment
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
    """Admin endpoint to list worker verification requests with appointment summary."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    query: Dict[str, Any] = {}

    if status_filter and status_filter.lower() != "all":
        s = status_filter.strip().upper()
        if s == "PENDING_VERIFICATION":
            query["status"] = {"$in": ["PENDING_VERIFICATION", "PENDING_REVIEW"]}
        elif s in ("DOCUMENTS_APPROVED", "AWAITING_IN_PERSON"):
            query["status"] = "DOCUMENTS_APPROVED"
        elif s in ("SCHEDULED", "IN_PERSON_SCHEDULED"):
            query["status"] = {"$in": ["IN_PERSON_SCHEDULED", "IN_PERSON_RESCHEDULED", "SCHEDULED", "RESCHEDULED"]}
        elif s in ("VERIFIED", "FULLY_VERIFIED"):
            query["status"] = {"$in": ["FULLY_VERIFIED", "VERIFIED"]}
        elif s == "REJECTED":
            query["status"] = "REJECTED"
        elif s == "INCOMPLETE":
            query["status"] = {"$in": ["IN_PERSON_FAILED", "NO_SHOW", "CANCELLED"]}
        else:
            query["status"] = s

    if search:
        pattern = re.escape(search.strip())
        query["$or"] = [
            {"worker_name": {"$regex": pattern, "$options": "i"}},
            {"worker_phone": {"$regex": pattern, "$options": "i"}},
            {"worker_trade": {"$regex": pattern, "$options": "i"}},
        ]

    verifications = await db.worker_verifications.find(query).sort("submitted_at", -1).to_list(length=1000)

    verif_ids = [v["id"] for v in verifications]
    appointments = await db.verification_appointments.find({"verification_id": {"$in": verif_ids}}).to_list(length=2000)
    appt_map = {}
    for a in appointments:
        v_id = a.get("verification_id")
        if v_id not in appt_map or (a.get("created_at") and appt_map[v_id].get("created_at") and a["created_at"] > appt_map[v_id]["created_at"]):
            appt_map[v_id] = a

    res = []
    for v in verifications:
        appt = appt_map.get(v["id"])
        res.append({
            "id": v["id"],
            "worker_id": v["worker_id"],
            "worker_name": v.get("worker_name", "Worker"),
            "worker_phone": v.get("worker_phone", ""),
            "worker_trade": v.get("worker_trade", "General"),
            "aadhaar_last_four": v.get("aadhaar_last_four", "XXXX"),
            "labour_certificate_name": v.get("labour_certificate_name", "labour_certificate.pdf"),
            "status": v.get("status", OverallVerificationStatus.PENDING_VERIFICATION),
            "stage1_status": v.get("stage1_status", Stage1Status.PENDING_REVIEW),
            "stage2_status": v.get("stage2_status", Stage2Status.NOT_SCHEDULED),
            "rejection_reason": v.get("rejection_reason"),
            "submitted_at": v.get("submitted_at"),
            "reviewed_at": v.get("reviewed_at"),
            "verified_at": v.get("verified_at"),
            "appointment_date": appt.get("appointment_date") if appt else None,
            "appointment_time": f"{appt.get('start_time')} - {appt.get('end_time')}" if appt and appt.get("start_time") else None,
            "appointment_status": appt.get("status") if appt else None,
            "location_name": appt.get("location_name") if appt else None
        })

    return res


@worker_verification_router.get("/admin/worker-verifications/{verification_id}")
async def get_admin_worker_verification_detail(
    verification_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin endpoint to view verification details and appointment history."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification request not found.")

    appointment_doc = None
    if v.get("current_appointment_id"):
        appointment_doc = await db.verification_appointments.find_one({"id": v["current_appointment_id"]})
    if not appointment_doc:
        appointment_doc = await db.verification_appointments.find_one(
            {"verification_id": verification_id},
            sort=[("created_at", -1)]
        )

    appointment_data = None
    if appointment_doc:
        appointment_data = {
            "id": appointment_doc["id"],
            "verification_id": appointment_doc.get("verification_id", verification_id),
            "worker_id": appointment_doc.get("worker_id", v["worker_id"]),
            "worker_name": appointment_doc.get("worker_name", v.get("worker_name", "")),
            "worker_phone": appointment_doc.get("worker_phone", v.get("worker_phone", "")),
            "location_name": appointment_doc.get("location_name", ""),
            "venue_address": appointment_doc.get("venue_address", ""),
            "appointment_date": appointment_doc.get("appointment_date", ""),
            "start_time": appointment_doc.get("start_time", ""),
            "end_time": appointment_doc.get("end_time", ""),
            "officer_name": appointment_doc.get("officer_name", ""),
            "officer_phone": appointment_doc.get("officer_phone", ""),
            "officer_photo_url": appointment_doc.get("officer_photo_url", ""),
            "instructions": appointment_doc.get("instructions", ""),
            "admin_notes": appointment_doc.get("admin_notes"),
            "status": appointment_doc.get("status", Stage2Status.SCHEDULED),
            "outcome": appointment_doc.get("outcome"),
            "outcome_reason": appointment_doc.get("outcome_reason"),
            "outcome_recorded_at": appointment_doc.get("outcome_recorded_at"),
            "reschedule_reason": appointment_doc.get("reschedule_reason"),
            "cancellation_reason": appointment_doc.get("cancellation_reason"),
            "history": appointment_doc.get("history", []),
            "created_at": appointment_doc.get("created_at"),
            "updated_at": appointment_doc.get("updated_at")
        }

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
        "status": v.get("status", OverallVerificationStatus.PENDING_VERIFICATION),
        "stage1_status": v.get("stage1_status", Stage1Status.PENDING_REVIEW),
        "stage2_status": v.get("stage2_status", Stage2Status.NOT_SCHEDULED),
        "rejection_reason": v.get("rejection_reason"),
        "submitted_at": v.get("submitted_at"),
        "reviewed_at": v.get("reviewed_at"),
        "verified_at": v.get("verified_at"),
        "appointment": appointment_data
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


# =============================================================================
# STAGE 1: DOCUMENT APPROVAL & REJECTION
# =============================================================================

@worker_verification_router.post("/admin/worker-verifications/{verification_id}/approve-documents")
async def approve_worker_documents(
    verification_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin approves Stage 1 documents; Stage 2 In-Person Verification scheduling becomes available."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    now = datetime.now(timezone.utc)
    worker_id = v["worker_id"]

    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "status": OverallVerificationStatus.DOCUMENTS_APPROVED,
            "stage1_status": Stage1Status.APPROVED,
            "stage2_status": v.get("stage2_status") or Stage2Status.NOT_SCHEDULED,
            "reviewed_at": now,
            "reviewed_by": current_user.id,
            "updated_at": now
        }}
    )

    await db.users.update_one(
        {"id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.DOCUMENTS_APPROVED, "is_verified": False}}
    )
    await db.worker_profiles.update_one(
        {"user_id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.DOCUMENTS_APPROVED, "is_verified": False}}
    )

    await send_worker_notification(
        db,
        worker_id,
        title="Documents Approved!",
        message="Your identity documents have been approved by admin. Your in-person verification appointment will be scheduled shortly."
    )

    await log_audit(
        db,
        action="WORKER_DOCUMENTS_APPROVED",
        user_id=worker_id,
        admin_id=current_user.id,
        details={"verification_id": verification_id}
    )

    return {
        "message": "Worker documents approved successfully. In-person verification can now be scheduled.",
        "status": OverallVerificationStatus.DOCUMENTS_APPROVED,
        "stage1_status": Stage1Status.APPROVED
    }


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/reject")
async def reject_worker_verification(
    verification_id: str,
    payload: AdminRejectRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin rejects worker identity documents with a reason."""
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
    worker_id = v["worker_id"]

    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "status": OverallVerificationStatus.REJECTED,
            "stage1_status": Stage1Status.REJECTED,
            "rejection_reason": reason,
            "reviewed_at": now,
            "reviewed_by": current_user.id,
            "updated_at": now
        }}
    )

    await db.users.update_one({"id": worker_id}, {"$set": {"verification_status": OverallVerificationStatus.REJECTED, "is_verified": False}})
    await db.worker_profiles.update_one({"user_id": worker_id}, {"$set": {"verification_status": OverallVerificationStatus.REJECTED, "is_verified": False}})

    await send_worker_notification(
        db,
        worker_id,
        title="Verification Update Needed",
        message=f"Your worker identity verification requires changes: {reason}"
    )

    await log_audit(
        db,
        action="WORKER_REJECTED",
        user_id=worker_id,
        admin_id=current_user.id,
        details={"verification_id": verification_id, "rejection_reason": reason}
    )

    return {"message": "Worker verification rejected with reason.", "status": OverallVerificationStatus.REJECTED}


# =============================================================================
# STAGE 2: IN-PERSON APPOINTMENT SCHEDULING, RESCHEDULING, CANCELLATION & OUTCOME
# =============================================================================

@worker_verification_router.post("/admin/worker-verifications/{verification_id}/schedule-appointment")
async def schedule_in_person_verification(
    verification_id: str,
    payload: ScheduleAppointmentRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin schedules in-person identity verification appointment for a worker whose documents are approved."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    # Business Rule 1: Scheduling is permitted only after document approval
    stage1 = v.get("stage1_status")
    overall = v.get("status")
    if stage1 != Stage1Status.APPROVED and overall not in (
        OverallVerificationStatus.DOCUMENTS_APPROVED,
        OverallVerificationStatus.IN_PERSON_SCHEDULED,
        OverallVerificationStatus.IN_PERSON_RESCHEDULED,
        OverallVerificationStatus.IN_PERSON_FAILED,
        OverallVerificationStatus.NO_SHOW,
        OverallVerificationStatus.CANCELLED
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule in-person verification until worker documents have been approved."
        )

    validate_appointment_schedule(payload.appointment_date, payload.start_time, payload.end_time)

    # Business Rule 8: Prevent duplicate active appointments
    existing_active = await db.verification_appointments.find_one({
        "verification_id": verification_id,
        "status": {"$in": [Stage2Status.SCHEDULED, Stage2Status.RESCHEDULED]}
    })
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active verification appointment is already scheduled. Please use reschedule or cancel instead."
        )

    now = datetime.now(timezone.utc)
    appt_id = str(uuid.uuid4())
    appt_doc = {
        "id": appt_id,
        "verification_id": verification_id,
        "worker_id": v["worker_id"],
        "worker_name": v.get("worker_name", "Worker"),
        "worker_phone": v.get("worker_phone", ""),
        "location_name": payload.location_name.strip(),
        "venue_address": payload.venue_address.strip(),
        "appointment_date": payload.appointment_date.strip(),
        "start_time": payload.start_time.strip(),
        "end_time": payload.end_time.strip(),
        "officer_name": payload.officer_name.strip(),
        "officer_phone": payload.officer_phone.strip(),
        "officer_photo_url": payload.officer_photo_url or "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=256&q=80",
        "instructions": payload.instructions.strip(),
        "admin_notes": payload.admin_notes.strip() if payload.admin_notes else None,
        "status": Stage2Status.SCHEDULED,
        "outcome": None,
        "outcome_reason": None,
        "outcome_recorded_at": None,
        "outcome_recorded_by": None,
        "cancellation_reason": None,
        "cancelled_at": None,
        "cancelled_by": None,
        "reschedule_reason": None,
        "history": [
            {
                "action": "SCHEDULED",
                "timestamp": now.isoformat(),
                "admin_id": current_user.id,
                "details": {
                    "appointment_date": payload.appointment_date.strip(),
                    "start_time": payload.start_time.strip(),
                    "end_time": payload.end_time.strip(),
                    "location_name": payload.location_name.strip()
                }
            }
        ],
        "created_at": now,
        "updated_at": now
    }

    await db.verification_appointments.insert_one(appt_doc)

    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "current_appointment_id": appt_id,
            "stage2_status": Stage2Status.SCHEDULED,
            "status": OverallVerificationStatus.IN_PERSON_SCHEDULED,
            "updated_at": now
        }}
    )

    worker_id = v["worker_id"]
    await db.users.update_one(
        {"id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.IN_PERSON_SCHEDULED, "is_verified": False}}
    )
    await db.worker_profiles.update_one(
        {"user_id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.IN_PERSON_SCHEDULED, "is_verified": False}}
    )

    await send_worker_notification(
        db,
        worker_id,
        title="In-Person Verification Scheduled",
        message=f"Your in-person verification has been scheduled for {payload.appointment_date} from {payload.start_time} to {payload.end_time} at {payload.location_name}."
    )

    await log_audit(
        db,
        action="IN_PERSON_APPOINTMENT_SCHEDULED",
        user_id=worker_id,
        admin_id=current_user.id,
        details={"verification_id": verification_id, "appointment_id": appt_id}
    )

    # Return sanitized copy if needed or full appt_doc (admin caller)
    appt_doc.pop("_id", None)
    return appt_doc


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/reschedule-appointment")
async def reschedule_in_person_verification(
    verification_id: str,
    payload: RescheduleAppointmentRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin reschedules an in-person verification appointment, updating the existing record and preserving history."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    appt = None
    if v.get("current_appointment_id"):
        appt = await db.verification_appointments.find_one({"id": v["current_appointment_id"]})
    if not appt:
        appt = await db.verification_appointments.find_one(
            {"verification_id": verification_id},
            sort=[("created_at", -1)]
        )

    if not appt:
        raise HTTPException(status_code=404, detail="No appointment found to reschedule.")

    if appt.get("status") == Stage2Status.PASSED:
        raise HTTPException(status_code=400, detail="Cannot reschedule an appointment that has already passed verification.")

    validate_appointment_schedule(payload.appointment_date, payload.start_time, payload.end_time)

    now = datetime.now(timezone.utc)
    history_entry = {
        "action": "RESCHEDULED",
        "timestamp": now.isoformat(),
        "admin_id": current_user.id,
        "previous": {
            "appointment_date": appt.get("appointment_date"),
            "start_time": appt.get("start_time"),
            "end_time": appt.get("end_time"),
            "location_name": appt.get("location_name")
        },
        "new": {
            "appointment_date": payload.appointment_date.strip(),
            "start_time": payload.start_time.strip(),
            "end_time": payload.end_time.strip(),
            "location_name": payload.location_name.strip() if payload.location_name else appt.get("location_name")
        },
        "reason": payload.reschedule_reason.strip()
    }

    update_fields = {
        "appointment_date": payload.appointment_date.strip(),
        "start_time": payload.start_time.strip(),
        "end_time": payload.end_time.strip(),
        "reschedule_reason": payload.reschedule_reason.strip(),
        "status": Stage2Status.RESCHEDULED,
        "updated_at": now
    }
    if payload.location_name:
        update_fields["location_name"] = payload.location_name.strip()
    if payload.venue_address:
        update_fields["venue_address"] = payload.venue_address.strip()
    if payload.officer_name:
        update_fields["officer_name"] = payload.officer_name.strip()
    if payload.officer_phone:
        update_fields["officer_phone"] = payload.officer_phone.strip()
    if payload.officer_photo_url:
        update_fields["officer_photo_url"] = payload.officer_photo_url.strip()
    if payload.instructions:
        update_fields["instructions"] = payload.instructions.strip()
    if payload.admin_notes:
        update_fields["admin_notes"] = payload.admin_notes.strip()

    await db.verification_appointments.update_one(
        {"id": appt["id"]},
        {
            "$set": update_fields,
            "$push": {"history": history_entry}
        }
    )

    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "current_appointment_id": appt["id"],
            "stage2_status": Stage2Status.RESCHEDULED,
            "status": OverallVerificationStatus.IN_PERSON_RESCHEDULED,
            "updated_at": now
        }}
    )

    worker_id = v["worker_id"]
    await db.users.update_one(
        {"id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.IN_PERSON_RESCHEDULED, "is_verified": False}}
    )
    await db.worker_profiles.update_one(
        {"user_id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.IN_PERSON_RESCHEDULED, "is_verified": False}}
    )

    await send_worker_notification(
        db,
        worker_id,
        title="Verification Appointment Rescheduled",
        message=f"Your in-person verification has been rescheduled to {payload.appointment_date} ({payload.start_time} - {payload.end_time}). Reason: {payload.reschedule_reason.strip()}"
    )

    await log_audit(
        db,
        action="IN_PERSON_APPOINTMENT_RESCHEDULED",
        user_id=worker_id,
        admin_id=current_user.id,
        details={"verification_id": verification_id, "appointment_id": appt["id"], "reason": payload.reschedule_reason}
    )

    updated_appt = await db.verification_appointments.find_one({"id": appt["id"]})
    if updated_appt:
        updated_appt.pop("_id", None)
    return updated_appt


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/cancel-appointment")
async def cancel_in_person_verification(
    verification_id: str,
    payload: CancelAppointmentRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin cancels an in-person verification appointment with a reason."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    appt = None
    if v.get("current_appointment_id"):
        appt = await db.verification_appointments.find_one({"id": v["current_appointment_id"]})
    if not appt:
        appt = await db.verification_appointments.find_one(
            {"verification_id": verification_id},
            sort=[("created_at", -1)]
        )

    if not appt:
        raise HTTPException(status_code=404, detail="No appointment found to cancel.")

    if appt.get("status") == Stage2Status.CANCELLED:
        raise HTTPException(status_code=400, detail="Appointment is already cancelled.")

    if appt.get("status") == Stage2Status.PASSED:
        raise HTTPException(status_code=400, detail="Cannot cancel an appointment that has already passed verification.")

    now = datetime.now(timezone.utc)
    history_entry = {
        "action": "CANCELLED",
        "timestamp": now.isoformat(),
        "admin_id": current_user.id,
        "reason": payload.cancellation_reason.strip()
    }

    await db.verification_appointments.update_one(
        {"id": appt["id"]},
        {
            "$set": {
                "status": Stage2Status.CANCELLED,
                "cancellation_reason": payload.cancellation_reason.strip(),
                "cancelled_at": now,
                "cancelled_by": current_user.id,
                "updated_at": now
            },
            "$push": {"history": history_entry}
        }
    )

    await db.worker_verifications.update_one(
        {"id": verification_id},
        {"$set": {
            "stage2_status": Stage2Status.CANCELLED,
            "status": OverallVerificationStatus.CANCELLED,
            "updated_at": now
        }}
    )

    worker_id = v["worker_id"]
    await db.users.update_one(
        {"id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.CANCELLED, "is_verified": False}}
    )
    await db.worker_profiles.update_one(
        {"user_id": worker_id},
        {"$set": {"verification_status": OverallVerificationStatus.CANCELLED, "is_verified": False}}
    )

    await send_worker_notification(
        db,
        worker_id,
        title="Verification Appointment Cancelled",
        message=f"Your in-person verification appointment has been cancelled: {payload.cancellation_reason.strip()}. A new appointment will be scheduled."
    )

    await log_audit(
        db,
        action="IN_PERSON_APPOINTMENT_CANCELLED",
        user_id=worker_id,
        admin_id=current_user.id,
        details={"verification_id": verification_id, "appointment_id": appt["id"], "reason": payload.cancellation_reason}
    )

    return {"message": "Appointment cancelled successfully."}


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/record-outcome")
async def record_verification_outcome(
    verification_id: str,
    payload: RecordOutcomeRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin records the outcome of the offline in-person verification (PASSED, FAILED, NO_SHOW)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    appt = None
    if v.get("current_appointment_id"):
        appt = await db.verification_appointments.find_one({"id": v["current_appointment_id"]})
    if not appt:
        appt = await db.verification_appointments.find_one(
            {"verification_id": verification_id},
            sort=[("created_at", -1)]
        )

    if not appt:
        raise HTTPException(status_code=404, detail="No appointment found to record outcome for.")

    # Business Rule: Failure or No-Show requires an appropriate reason
    if payload.outcome in (Stage2Status.FAILED, Stage2Status.NO_SHOW):
        if not payload.outcome_reason or len(payload.outcome_reason.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An outcome reason (at least 3 characters) is required when marking an appointment as {payload.outcome}."
            )

    now = datetime.now(timezone.utc)
    worker_id = v["worker_id"]

    history_entry = {
        "action": f"OUTCOME_{payload.outcome}",
        "timestamp": now.isoformat(),
        "admin_id": current_user.id,
        "outcome": payload.outcome,
        "reason": payload.outcome_reason.strip() if payload.outcome_reason else None,
        "notes": payload.admin_notes.strip() if payload.admin_notes else None
    }

    if payload.outcome == Stage2Status.PASSED:
        # Business Rule 3: Fully Verified is permitted ONLY when document verification is approved
        if v.get("stage1_status") != Stage1Status.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot mark worker as Fully Verified because Stage 1 document verification is not approved."
            )

        await db.verification_appointments.update_one(
            {"id": appt["id"]},
            {
                "$set": {
                    "status": Stage2Status.PASSED,
                    "outcome": Stage2Status.PASSED,
                    "outcome_reason": payload.outcome_reason.strip() if payload.outcome_reason else "Successfully verified in-person.",
                    "outcome_recorded_at": now,
                    "outcome_recorded_by": current_user.id,
                    "admin_notes": payload.admin_notes.strip() if payload.admin_notes else appt.get("admin_notes"),
                    "updated_at": now
                },
                "$push": {"history": history_entry}
            }
        )

        await db.worker_verifications.update_one(
            {"id": verification_id},
            {"$set": {
                "stage2_status": Stage2Status.PASSED,
                "status": OverallVerificationStatus.FULLY_VERIFIED,
                "verified_at": now,
                "verified_by": current_user.id,
                "updated_at": now
            }}
        )

        await db.users.update_one(
            {"id": worker_id},
            {"$set": {"verification_status": OverallVerificationStatus.FULLY_VERIFIED, "is_verified": True}}
        )
        await db.worker_profiles.update_one(
            {"user_id": worker_id},
            {"$set": {"verification_status": OverallVerificationStatus.FULLY_VERIFIED, "is_verified": True}}
        )

        await send_worker_notification(
            db,
            worker_id,
            title="Congratulations! Fully Verified",
            message="You have successfully passed in-person verification and your Sanyuth worker profile is now Fully Verified!"
        )

        await log_audit(
            db,
            action="IN_PERSON_VERIFICATION_PASSED",
            user_id=worker_id,
            admin_id=current_user.id,
            details={"verification_id": verification_id, "appointment_id": appt["id"]}
        )

        return {
            "message": "Worker in-person verification passed. Worker is now Fully Verified!",
            "status": OverallVerificationStatus.FULLY_VERIFIED,
            "stage2_status": Stage2Status.PASSED
        }

    elif payload.outcome == Stage2Status.FAILED:
        await db.verification_appointments.update_one(
            {"id": appt["id"]},
            {
                "$set": {
                    "status": Stage2Status.FAILED,
                    "outcome": Stage2Status.FAILED,
                    "outcome_reason": payload.outcome_reason.strip(),
                    "outcome_recorded_at": now,
                    "outcome_recorded_by": current_user.id,
                    "admin_notes": payload.admin_notes.strip() if payload.admin_notes else appt.get("admin_notes"),
                    "updated_at": now
                },
                "$push": {"history": history_entry}
            }
        )

        await db.worker_verifications.update_one(
            {"id": verification_id},
            {"$set": {
                "stage2_status": Stage2Status.FAILED,
                "status": OverallVerificationStatus.IN_PERSON_FAILED,
                "updated_at": now
            }}
        )

        await db.users.update_one(
            {"id": worker_id},
            {"$set": {"verification_status": OverallVerificationStatus.IN_PERSON_FAILED, "is_verified": False}}
        )
        await db.worker_profiles.update_one(
            {"user_id": worker_id},
            {"$set": {"verification_status": OverallVerificationStatus.IN_PERSON_FAILED, "is_verified": False}}
        )

        await send_worker_notification(
            db,
            worker_id,
            title="In-Person Verification Failed",
            message=f"Your in-person verification check was not successful: {payload.outcome_reason.strip()}."
        )

        await log_audit(
            db,
            action="IN_PERSON_VERIFICATION_FAILED",
            user_id=worker_id,
            admin_id=current_user.id,
            details={"verification_id": verification_id, "appointment_id": appt["id"], "reason": payload.outcome_reason}
        )

        return {
            "message": "In-person verification recorded as Failed. Identity verification remains incomplete.",
            "status": OverallVerificationStatus.IN_PERSON_FAILED,
            "stage2_status": Stage2Status.FAILED
        }

    elif payload.outcome == Stage2Status.NO_SHOW:
        await db.verification_appointments.update_one(
            {"id": appt["id"]},
            {
                "$set": {
                    "status": Stage2Status.NO_SHOW,
                    "outcome": Stage2Status.NO_SHOW,
                    "outcome_reason": payload.outcome_reason.strip(),
                    "outcome_recorded_at": now,
                    "outcome_recorded_by": current_user.id,
                    "admin_notes": payload.admin_notes.strip() if payload.admin_notes else appt.get("admin_notes"),
                    "updated_at": now
                },
                "$push": {"history": history_entry}
            }
        )

        await db.worker_verifications.update_one(
            {"id": verification_id},
            {"$set": {
                "stage2_status": Stage2Status.NO_SHOW,
                "status": OverallVerificationStatus.NO_SHOW,
                "updated_at": now
            }}
        )

        await db.users.update_one(
            {"id": worker_id},
            {"$set": {"verification_status": OverallVerificationStatus.NO_SHOW, "is_verified": False}}
        )
        await db.worker_profiles.update_one(
            {"user_id": worker_id},
            {"$set": {"verification_status": OverallVerificationStatus.NO_SHOW, "is_verified": False}}
        )

        await send_worker_notification(
            db,
            worker_id,
            title="Verification Appointment Missed",
            message=f"You missed your scheduled in-person verification appointment: {payload.outcome_reason.strip()}."
        )

        await log_audit(
            db,
            action="IN_PERSON_VERIFICATION_NO_SHOW",
            user_id=worker_id,
            admin_id=current_user.id,
            details={"verification_id": verification_id, "appointment_id": appt["id"], "reason": payload.outcome_reason}
        )

        return {
            "message": "In-person verification recorded as No-Show. Identity verification remains incomplete.",
            "status": OverallVerificationStatus.NO_SHOW,
            "stage2_status": Stage2Status.NO_SHOW
        }


@worker_verification_router.post("/admin/worker-verifications/{verification_id}/verify")
async def approve_worker_verification(
    verification_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    """Admin approves worker verification.
    If Stage 1 documents are not yet approved, approves Stage 1 documents (DOCUMENTS_APPROVED).
    If an appointment is scheduled or completed, records in-person verification as PASSED (FULLY_VERIFIED).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    db = get_db()
    v = await db.worker_verifications.find_one({"id": verification_id})
    if not v:
        raise HTTPException(status_code=404, detail="Verification record not found.")

    if v.get("stage1_status") != Stage1Status.APPROVED:
        return await approve_worker_documents(verification_id, current_user)
    else:
        return await record_verification_outcome(
            verification_id,
            RecordOutcomeRequest(outcome="PASSED", outcome_reason="Confirmed in-person verification passed."),
            current_user
        )
