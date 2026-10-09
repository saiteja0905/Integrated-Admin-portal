# Pydantic models for Sanyuth Features 1 - 5
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
import uuid

# =============================================================================
# FEATURE 1: SCOPE AGREEMENT CARD MODELS
# =============================================================================

class AgreementStatus(str):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ChangeRequestStatus(str):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"

class ChangeHistoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str
    actor_role: str  # "customer" or "worker" or "admin"
    action: str  # "created", "agreed", "change_requested", "change_approved", "change_declined"
    summary: str
    details: Dict[str, Any] = {}

class ScopeAgreement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    bid_id: Optional[str] = None
    customer_id: str
    worker_id: str
    job_title: str
    work_included: List[str] = []
    work_not_included: List[str] = []
    agreed_price: float
    materials_responsibility: str = "Customer supplied"  # "Customer supplied", "Worker supplied", "Shared"
    start_date: str  # e.g., "2026-10-05"
    start_time: str  # e.g., "10:00 AM"
    expected_duration: str = "1 Day"
    warranty: str = "30 Days Service Warranty"
    additional_notes: str = ""
    status: str = "draft"  # "draft", "active", "completed", "cancelled"
    customer_agreed_at: Optional[datetime] = None
    worker_agreed_at: Optional[datetime] = None
    history: List[ChangeHistoryItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScopeAgreementCreate(BaseModel):
    job_id: str
    bid_id: Optional[str] = None
    work_included: List[str]
    work_not_included: List[str] = []
    agreed_price: float
    materials_responsibility: str = "Customer supplied"
    start_date: str
    start_time: str = "09:00 AM"
    expected_duration: str = "1 Day"
    warranty: str = "30 Days Service Warranty"
    additional_notes: str = ""

class ScopeAgreementUpdate(BaseModel):
    work_included: Optional[List[str]] = None
    work_not_included: Optional[List[str]] = None
    agreed_price: Optional[float] = None
    materials_responsibility: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    expected_duration: Optional[str] = None
    warranty: Optional[str] = None
    additional_notes: Optional[str] = None

class AgreementChangeRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agreement_id: str
    job_id: str
    requested_by: str  # "customer" or "worker"
    requester_id: str
    description: str
    price_change: float = 0.0  # e.g. +500 or -200
    new_agreed_price: float
    schedule_change: Optional[str] = None
    additional_notes: str = ""
    status: str = "pending"  # "pending", "approved", "declined"
    response_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None

class ChangeRequestCreate(BaseModel):
    description: str
    price_change: float = 0.0
    new_agreed_price: float
    schedule_change: Optional[str] = None
    additional_notes: str = ""

class ChangeRequestRespond(BaseModel):
    status: Literal["approved", "declined"]
    response_notes: str = ""


# =============================================================================
# FEATURE 2: JOB CHAINING / DAY PLANNER MODELS
# =============================================================================

class PlannerTimelineItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["job", "travel", "suggestion"]
    job_id: Optional[str] = None
    title: str
    category: Optional[str] = None
    location: str
    lat: float
    lng: float
    start_time: str  # e.g., "10:00 AM"
    end_time: str    # e.g., "12:00 PM"
    estimated_duration_minutes: int
    estimated_earnings: float = 0.0
    distance_km: float = 0.0
    travel_time_minutes: int = 0
    status: str = "scheduled"  # "scheduled", "completed", "suggested"

class WorkerDayPlan(BaseModel):
    worker_id: str
    date: str  # e.g., "2026-10-04"
    total_estimated_earnings: float
    total_jobs_count: int
    timeline: List[PlannerTimelineItem]
    suggested_jobs: List[PlannerTimelineItem]

class QuickBidRequest(BaseModel):
    job_id: str
    bid_amount: float
    visiting_charge: float = 0.0
    message: str = "1-Tap Day Planner Bid"


# =============================================================================
# FEATURE 3: BOOK FOR PARENTS / FAMILY MODE MODELS
# =============================================================================

class FamilyAddress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    parent_name: str
    parent_phone: str
    address: str
    city: str
    preferred_language: Literal["Telugu", "Hindi", "English"] = "English"
    landmark: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FamilyAddressCreate(BaseModel):
    parent_name: str
    parent_phone: str
    address: str
    city: str
    preferred_language: Literal["Telugu", "Hindi", "English"] = "English"
    landmark: Optional[str] = ""

class ParentBookingStatusUpdate(BaseModel):
    arrival_status: Literal["assigned", "on_the_way", "arrived", "started", "completed"]
    before_photos: Optional[List[str]] = None
    after_photos: Optional[List[str]] = None
    notes: Optional[str] = ""

class ParentOTPVerify(BaseModel):
    otp: str

class ParentSupportRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    customer_id: str
    parent_name: str
    parent_phone: str
    message: str = "Parent requested assistance with the booking."
    status: str = "open"  # "open", "resolved"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


# =============================================================================
# FEATURE 4: FAIR START FOR NEW WORKERS MODELS
# =============================================================================

class NewWorkerEligibility(BaseModel):
    worker_id: str
    worker_name: str
    kyc_verified: bool
    completed_jobs: int
    is_eligible: bool
    intro_jobs_remaining: int
    badge_label: str = "New on Sanyuth"
    quality_status: str = "good"  # "good", "paused_rating_too_low"
    rating_avg: float = 5.0

class NewWorkerBidHighlight(BaseModel):
    bid_id: str
    worker_id: str
    worker_name: str
    is_new_worker: bool
    intro_jobs_completed: int
    badge_labels: List[str] = ["New on Sanyuth", "ID Verified", "Intro Price"]


# =============================================================================
# FEATURE 5: ASK A PRO MODELS
# =============================================================================

class ProQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    customer_name: str
    title: str
    description: str
    category: str  # "plumbing", "electrical", "ac_service", "carpentry", etc.
    photo_urls: List[str] = []
    video_url: Optional[str] = None
    voice_note_url: Optional[str] = None
    language: str = "English"
    status: str = "open"  # "open", "answered", "closed"
    most_helpful_answer_id: Optional[str] = None
    answers_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProQuestionCreate(BaseModel):
    title: str
    description: str
    category: str
    photo_urls: List[str] = []
    video_url: Optional[str] = None
    voice_note_url: Optional[str] = None
    language: str = "English"

class ProAnswer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    worker_id: str
    worker_name: str
    worker_rating: float = 5.0
    worker_trade: str = "Service Professional"
    answer_text: str
    is_most_helpful: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProAnswerCreate(BaseModel):
    answer_text: str

class MarkHelpfulRequest(BaseModel):
    answer_id: str
