# Admin-specific models for Shidhaan Admin Portal
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# Admin Role Enums
class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    OPERATIONS_ADMIN = "operations_admin"
    SUPPORT_STAFF = "support_staff"

class KYCStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class DisputeSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ContentModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"

# KYC Models
class KYCDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    document_type: str  # "aadhaar", "pan", "driving_license", "voter_id"
    document_number: str
    document_url: str  # File upload path
    status: str = KYCStatus.PENDING
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KYCVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    overall_status: str = KYCStatus.PENDING
    documents: List[KYCDocument] = []
    verification_notes: str = ""
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# User Management Models
class UserVerificationStatus(BaseModel):
    email_verified: bool = False
    phone_verified: bool = False
    kyc_verified: bool = False
    profile_complete: bool = False
    background_check: bool = False

class UserActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str  # "login", "job_posted", "application_submitted", "payment_made"
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserStrike(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    reason: str
    description: str
    severity: str = "medium"
    issued_by: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = True

class UserSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan_name: str
    status: str  # "active", "expired", "grace_period", "cancelled"
    started_at: datetime
    expires_at: datetime
    auto_renewal: bool = True
    payment_history: List[str] = []  # Payment IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Dispute Management Models
class Dispute(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    complainant_id: str  # User who raised the dispute
    respondent_id: str   # User being complained about
    title: str
    description: str
    category: str  # "payment", "quality", "behavior", "fraud"
    severity: str = DisputeSeverity.MEDIUM
    status: str = DisputeStatus.OPEN
    evidence_files: List[str] = []
    chat_logs_included: bool = True
    resolution_notes: str = ""
    assigned_to: Optional[str] = None  # Admin user ID
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DisputeAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dispute_id: str
    admin_id: str
    action_type: str  # "refund", "suspend_worker", "ban_customer", "escalate", "resolve"
    action_details: Dict[str, Any] = {}
    notes: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Content Moderation Models
class ContentFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_type: str  # "job_post", "message", "review", "profile"
    content_id: str
    flag_reason: str  # "offensive", "spam", "duplicate", "inappropriate"
    flagged_by: Optional[str] = None  # User ID or "system"
    flag_details: str = ""
    status: str = ContentModerationStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Analytics Models
class PlatformAnalytics(BaseModel):
    date: datetime
    total_users: int
    active_users_daily: int
    active_users_monthly: int
    total_jobs_posted: int
    total_jobs_completed: int
    total_revenue: float
    average_job_value: float
    top_categories: List[Dict[str, Any]] = []
    city_wise_stats: Dict[str, Any] = {}

class UserAnalytics(BaseModel):
    user_id: str
    total_jobs: int
    completed_jobs: int
    cancelled_jobs: int
    average_rating: float
    total_earnings: float
    response_rate: float
    completion_rate: float
    last_activity: datetime

# Configuration Models
class PlatformConfig(BaseModel):
    key: str
    value: Any
    category: str  # "general", "payment", "job", "user"
    description: str = ""
    updated_by: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_active: bool = True
    skills_required: List[str] = []
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Announcement Models
class Announcement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message: str
    target_audience: str  # "all", "customers", "workers", "specific_users"
    target_user_ids: List[str] = []
    announcement_type: str  # "info", "warning", "promotion", "maintenance"
    priority: str = "normal"  # "low", "normal", "high"
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Fraud Detection Models
class FraudAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str  # "multiple_accounts", "suspicious_payments", "fake_reviews"
    severity: str = "medium"
    description: str
    affected_users: List[str] = []
    evidence: Dict[str, Any] = {}
    status: str = "open"  # "open", "investigating", "resolved", "false_positive"
    investigated_by: Optional[str] = None
    resolution_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Admin Dashboard Models
class AdminDashboardStats(BaseModel):
    total_users: int
    total_customers: int
    total_workers: int
    active_jobs: int
    completed_jobs: int
    pending_disputes: int
    pending_kyc: int
    total_revenue_today: float
    total_revenue_month: float
    top_performing_workers: List[Dict[str, Any]] = []
    recent_activities: List[Dict[str, Any]] = []