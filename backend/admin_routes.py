# Admin Portal Routes for Shidhaan Marketplace
import logging
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, ValidationError

from admin_models import (
    AdminRole,
    AdminDashboardStats,
    Announcement,
    Dispute,
    DisputeAction,
    KYCVerification,
    PlatformConfig,
    UserStrike,
)
from server import get_current_user, User, UserRole, db

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Payments that count as platform revenue
REVENUE_PAYMENT_STATUSES = ["succeeded", "recorded_cod"]
# Active strikes at which a user is suspended automatically
MAX_ACTIVE_STRIKES = 3


# Admin role validation
def require_admin_role(min_role: AdminRole = AdminRole.SUPPORT_STAFF):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        # In production, check specific admin role levels
        # For now, any admin can access
        return current_user
    return role_checker


def clean(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Drop MongoDB's ObjectId so the document can be serialized to JSON."""
    doc.pop("_id", None)
    return doc


async def get_user_or_404(user_id: str) -> Dict[str, Any]:
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Request / response models
class AdminUserView(User):
    status: str = "active"
    kyc_verified: bool = False


class StrikeRequest(BaseModel):
    reason: str = Field(default="policy_violation", max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class SuspendRequest(BaseModel):
    suspend: bool = True
    reason: str = Field(default="", max_length=500)


class VerifyRequest(BaseModel):
    verified: bool = True


class KYCDecision(BaseModel):
    status: Literal["approved", "rejected"]
    notes: str = Field(default="", max_length=2000)


class ModerationRequest(BaseModel):
    action: Literal["approve", "reject", "flag"]
    reason: str = Field(default="", max_length=500)


class AssignDisputeRequest(BaseModel):
    admin_id: str


class DisputeActionRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=50)
    details: Dict[str, Any] = {}
    notes: str = Field(default="", max_length=2000)


class ConfigUpdate(BaseModel):
    value: Any
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)


class AnnouncementRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    target_audience: Literal["all", "customers", "workers", "specific_users"] = "all"
    target_user_ids: List[str] = []
    type: str = "info"
    priority: Literal["low", "normal", "high"] = "normal"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# =============================================================================
# DASHBOARD & ANALYTICS
# =============================================================================

@admin_router.get("/dashboard", response_model=AdminDashboardStats)
async def get_admin_dashboard(current_user: User = Depends(require_admin_role())):
    """Get comprehensive admin dashboard statistics"""

    # Get user counts
    total_users = await db.users.count_documents({})
    total_customers = await db.users.count_documents({"role": "customer"})
    total_workers = await db.users.count_documents({"role": "worker"})

    # Get job counts
    active_jobs = await db.jobs.count_documents({"status": {"$in": ["open", "assigned", "in_progress"]}})
    completed_jobs = await db.jobs.count_documents({"status": "completed"})

    # Counting a collection that doesn't exist yet simply returns 0
    pending_disputes = await db.disputes.count_documents({"status": {"$in": ["open", "under_review"]}})
    pending_kyc = await db.kyc_verifications.count_documents({"overall_status": "pending"})

    # Get revenue data
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)

    async def revenue_since(start: datetime) -> float:
        result = await db.payments.aggregate([
            {"$match": {"created_at": {"$gte": start}, "status": {"$in": REVENUE_PAYMENT_STATUSES}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(1)
        return float(result[0]["total"]) if result else 0.0

    revenue_today = await revenue_since(today)
    revenue_month = await revenue_since(month_start)

    # Get top performing workers (exclude _id: ObjectId is not JSON serializable)
    top_workers_pipeline = [
        {"$match": {"role": "worker"}},
        {"$sort": {"rating_avg": -1, "reviews_count": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "id": 1, "name": 1, "rating_avg": 1, "reviews_count": 1}}
    ]

    top_workers = await db.users.aggregate(top_workers_pipeline).to_list(5)

    # Get recent activities
    recent_activities = [
        {"type": "job_posted", "description": "New plumbing job posted", "time": "2 hours ago"},
        {"type": "worker_joined", "description": "New worker registered", "time": "4 hours ago"},
        {"type": "payment_completed", "description": "Payment of ₹2500 completed", "time": "6 hours ago"}
    ]

    return AdminDashboardStats(
        total_users=total_users,
        total_customers=total_customers,
        total_workers=total_workers,
        active_jobs=active_jobs,
        completed_jobs=completed_jobs,
        pending_disputes=pending_disputes,
        pending_kyc=pending_kyc,
        total_revenue_today=revenue_today,
        total_revenue_month=revenue_month,
        top_performing_workers=top_workers,
        recent_activities=recent_activities
    )

# =============================================================================
# USER MANAGEMENT
# =============================================================================

@admin_router.get("/users", response_model=List[AdminUserView])
async def get_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_admin_role())
):
    """Get all users with filtering and search"""
    filter_dict: Dict[str, Any] = {}

    if role:
        filter_dict["role"] = role

    if status == "suspended":
        filter_dict["status"] = "suspended"
    elif status == "active":
        filter_dict["status"] = {"$ne": "suspended"}
    elif status == "pending_verification":
        filter_dict["kyc_verified"] = {"$ne": True}

    if search and search.strip():
        pattern = re.escape(search.strip())
        filter_dict["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"phone": {"$regex": pattern, "$options": "i"}},
            {"email": {"$regex": pattern, "$options": "i"}}
        ]

    users = (
        await db.users.find(filter_dict, {"_id": 0, "password_hash": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    return [
        AdminUserView(**{**user, "status": user.get("status") or "active"})
        for user in users
    ]

@admin_router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    current_user: User = Depends(require_admin_role())
):
    """Get user activity timeline"""

    # Get user info
    user = await get_user_or_404(user_id)

    # Get user's jobs
    jobs = []
    if user["role"] == "customer":
        jobs = await db.jobs.find({"customer_id": user_id}).sort("created_at", -1).limit(10).to_list(10)

    # Get applications/bids
    applications = await db.applications.find({"worker_id": user_id}).sort("created_at", -1).limit(10).to_list(10)
    bids = await db.bids.find({"worker_id": user_id}).sort("created_at", -1).limit(10).to_list(10)

    # Get payments
    payments = await db.payments.find({
        "$or": [{"payer_id": user_id}, {"payee_id": user_id}]
    }).sort("created_at", -1).limit(10).to_list(10)

    # Get reviews
    reviews_given = await db.reviews.find({"reviewer_user_id": user_id}).sort("created_at", -1).limit(5).to_list(5)
    reviews_received = await db.reviews.find({"reviewee_user_id": user_id}).sort("created_at", -1).limit(5).to_list(5)

    active_strikes = await db.user_strikes.count_documents({"user_id": user_id, "is_active": True})

    user_view = {k: v for k, v in user.items() if k not in ("password_hash", "_id")}
    user_view["status"] = user.get("status") or "active"

    return {
        "user": user_view,
        "active_strikes": active_strikes,
        "jobs_posted": len(jobs) if user["role"] == "customer" else 0,
        "applications_sent": len(applications),
        "bids_placed": len(bids),
        "payments_made": len([p for p in payments if p["payer_id"] == user_id]),
        "payments_received": len([p for p in payments if p["payee_id"] == user_id]),
        "reviews_given": len(reviews_given),
        "reviews_received": len(reviews_received),
        "recent_jobs": [clean(j) for j in jobs[:5]],
        "recent_applications": [clean(a) for a in applications[:5]],
        "recent_reviews": [clean(r) for r in reviews_received[:5]]
    }

@admin_router.post("/users/{user_id}/strike")
async def issue_user_strike(
    user_id: str,
    strike_data: StrikeRequest,
    current_user: User = Depends(require_admin_role())
):
    """Issue a strike/warning to a user"""
    target = await get_user_or_404(user_id)
    if target.get("role") == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Admins cannot receive strikes")

    strike = UserStrike(
        user_id=user_id,
        reason=strike_data.reason,
        description=strike_data.description,
        severity=strike_data.severity,
        issued_by=current_user.id
    )

    await db.user_strikes.insert_one(strike.model_dump())

    # Update user's strike count
    strike_count = await db.user_strikes.count_documents({"user_id": user_id, "is_active": True})

    # Auto-suspend if too many strikes
    suspended = strike_count >= MAX_ACTIVE_STRIKES
    if suspended:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"status": "suspended", "suspended_at": datetime.now(timezone.utc)}}
        )

    return {
        "message": "Strike issued successfully",
        "total_strikes": strike_count,
        "suspended": suspended,
    }

@admin_router.put("/users/{user_id}/suspend")
async def set_user_suspension(
    user_id: str,
    request: SuspendRequest,
    current_user: User = Depends(require_admin_role())
):
    """Suspend or reactivate a user account"""
    target = await get_user_or_404(user_id)
    if target["id"] == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot suspend your own account")

    if request.suspend:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "status": "suspended",
                "suspended_at": datetime.now(timezone.utc),
                "suspended_by": current_user.id,
                "suspension_reason": request.reason,
            }}
        )
        return {"message": "User suspended successfully", "status": "suspended"}

    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {"status": "active"},
            "$unset": {"suspended_at": "", "suspended_by": "", "suspension_reason": ""},
        }
    )
    # Clear active strikes so the next strike doesn't immediately re-suspend the user
    await db.user_strikes.update_many(
        {"user_id": user_id, "is_active": True}, {"$set": {"is_active": False}}
    )
    return {"message": "User reactivated successfully", "status": "active"}

@admin_router.put("/users/{user_id}/verify")
async def set_user_verification(
    user_id: str,
    request: VerifyRequest,
    current_user: User = Depends(require_admin_role())
):
    """Mark a user as verified (or remove verification)"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "kyc_verified": request.verified,
            "verified_by": current_user.id,
            "verified_at": datetime.now(timezone.utc),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "User verified successfully" if request.verified else "User verification removed",
        "kyc_verified": request.verified,
    }

# =============================================================================
# KYC MANAGEMENT
# =============================================================================

@admin_router.get("/kyc/pending", response_model=List[KYCVerification])
async def get_pending_kyc(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_admin_role())
):
    """Get all pending KYC verifications"""

    kyc_docs = await db.kyc_verifications.find(
        {"overall_status": "pending"}
    ).skip(skip).limit(limit).to_list(limit)

    results = []
    for kyc in kyc_docs:
        try:
            results.append(KYCVerification(**clean(kyc)))
        except ValidationError as e:
            logger.warning(f"Skipping malformed KYC record {kyc.get('id')}: {e}")
    return results

@admin_router.put("/kyc/{kyc_id}/verify")
async def verify_kyc(
    kyc_id: str,
    decision: KYCDecision,
    current_user: User = Depends(require_admin_role())
):
    """Approve or reject KYC verification"""

    kyc_doc = await db.kyc_verifications.find_one({"id": kyc_id})
    if not kyc_doc:
        raise HTTPException(status_code=404, detail="KYC record not found")

    await db.kyc_verifications.update_one(
        {"id": kyc_id},
        {"$set": {
            "overall_status": decision.status,
            "verification_notes": decision.notes,
            "verified_by": current_user.id,
            "verified_at": datetime.now(timezone.utc)
        }}
    )

    # Update user verification status
    await db.users.update_one(
        {"id": kyc_doc["user_id"]},
        {"$set": {"kyc_verified": decision.status == "approved"}}
    )

    return {"message": f"KYC {decision.status} successfully"}

# =============================================================================
# JOB MANAGEMENT
# =============================================================================

@admin_router.get("/jobs/moderation")
async def get_jobs_for_moderation(
    status: str = "pending",
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_admin_role())
):
    """Get jobs that need content moderation"""

    # Get flagged jobs
    flagged_content = await db.content_flags.find({
        "content_type": "job_post",
        "status": status
    }).skip(skip).limit(limit).to_list(limit)

    job_ids = [flag["content_id"] for flag in flagged_content]

    jobs = {}
    if job_ids:
        job_docs = await db.jobs.find({"id": {"$in": job_ids}}).to_list(len(job_ids))
        jobs = {job["id"]: clean(job) for job in job_docs}

    # Combine job data with flag information
    return [
        {"flag": clean(flag), "job": jobs[flag["content_id"]]}
        for flag in flagged_content
        if flag["content_id"] in jobs
    ]

@admin_router.put("/jobs/{job_id}/moderate")
async def moderate_job_content(
    job_id: str,
    moderation: ModerationRequest,
    current_user: User = Depends(require_admin_role())
):
    """Approve, reject, or flag job content"""

    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update content flag status
    await db.content_flags.update_many(
        {"content_id": job_id, "content_type": "job_post"},
        {"$set": {
            "status": "resolved" if moderation.action == "approve" else "rejected",
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.now(timezone.utc),
            "action_taken": moderation.action
        }}
    )

    # Take action on the job
    if moderation.action == "reject":
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "rejected", "moderation_reason": moderation.reason}}
        )
    elif moderation.action == "flag":
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {"is_flagged": True, "flag_reason": moderation.reason}}
        )

    past_tense = {"approve": "approved", "reject": "rejected", "flag": "flagged"}
    return {"message": f"Job {past_tense[moderation.action]} successfully"}

# =============================================================================
# DISPUTE MANAGEMENT
# =============================================================================

def normalize_dispute(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Map legacy field names (raised_by/against) onto the Dispute model."""
    clean(doc)
    doc.setdefault("complainant_id", doc.get("raised_by", ""))
    doc.setdefault("respondent_id", doc.get("against", ""))
    doc.setdefault("category", "other")
    return doc


@admin_router.get("/disputes", response_model=List[Dispute])
async def get_disputes(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(require_admin_role())
):
    """Get disputes with filtering"""

    filter_dict = {}
    if status:
        filter_dict["status"] = status
    if severity:
        filter_dict["severity"] = severity
    if assigned_to:
        filter_dict["assigned_to"] = assigned_to

    disputes = await db.disputes.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    results = []
    for dispute in disputes:
        try:
            results.append(Dispute(**normalize_dispute(dispute)))
        except ValidationError as e:
            # One malformed record must not take down the whole list
            logger.warning(f"Skipping malformed dispute {dispute.get('id')}: {e}")
    return results

@admin_router.put("/disputes/{dispute_id}/assign")
async def assign_dispute(
    dispute_id: str,
    assignment: AssignDisputeRequest,
    current_user: User = Depends(require_admin_role())
):
    """Assign dispute to an admin"""

    result = await db.disputes.update_one(
        {"id": dispute_id},
        {"$set": {
            "assigned_to": assignment.admin_id,
            "status": "under_review"
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dispute not found")

    return {"message": "Dispute assigned successfully"}

@admin_router.post("/disputes/{dispute_id}/action")
async def take_dispute_action(
    dispute_id: str,
    action_data: DisputeActionRequest,
    current_user: User = Depends(require_admin_role())
):
    """Take action on a dispute"""

    dispute = await db.disputes.find_one({"id": dispute_id})
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    action = DisputeAction(
        dispute_id=dispute_id,
        admin_id=current_user.id,
        action_type=action_data.action_type,
        action_details=action_data.details,
        notes=action_data.notes
    )

    await db.dispute_actions.insert_one(action.model_dump())

    # Update dispute status
    new_status = "resolved" if action_data.action_type in ["refund", "resolve"] else "under_review"
    await db.disputes.update_one(
        {"id": dispute_id},
        {"$set": {
            "status": new_status,
            "resolved_by": current_user.id if new_status == "resolved" else None,
            "resolved_at": datetime.now(timezone.utc) if new_status == "resolved" else None
        }}
    )

    return {"message": "Action taken successfully"}

# =============================================================================
# ANALYTICS
# =============================================================================

@admin_router.get("/analytics/revenue")
async def get_revenue_analytics(
    period: str = "month",  # "day", "week", "month", "year"
    current_user: User = Depends(require_admin_role())
):
    """Get revenue analytics for different time periods"""

    now = datetime.now(timezone.utc)

    if period == "day":
        start_date = now - timedelta(days=30)
        group_by = {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}
    elif period == "week":
        start_date = now - timedelta(weeks=12)
        group_by = {"$dateToString": {"format": "%Y-W%V", "date": "$created_at"}}
    elif period == "month":
        start_date = now - timedelta(days=365)
        group_by = {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}}
    else:  # year
        start_date = now - timedelta(days=365*3)
        group_by = {"$dateToString": {"format": "%Y", "date": "$created_at"}}

    pipeline = [
        {"$match": {
            "created_at": {"$gte": start_date},
            "status": {"$in": REVENUE_PAYMENT_STATUSES}
        }},
        {"$group": {
            "_id": group_by,
            "total_revenue": {"$sum": "$amount"},
            "transaction_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    results = await db.payments.aggregate(pipeline).to_list(100)

    return {
        "period": period,
        "data": results,
        "total_revenue": sum(r["total_revenue"] for r in results),
        "total_transactions": sum(r["transaction_count"] for r in results)
    }

@admin_router.get("/analytics/jobs")
async def get_job_analytics(current_user: User = Depends(require_admin_role())):
    """Get job-related analytics"""

    # Job completion rates
    total_jobs = await db.jobs.count_documents({})
    completed_jobs = await db.jobs.count_documents({"status": "completed"})
    completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

    # Average job values by category
    category_pipeline = [
        {"$group": {
            "_id": "$category",
            "avg_amount": {"$avg": "$budget_amount"},
            "job_count": {"$sum": 1}
        }},
        {"$sort": {"job_count": -1}}
    ]

    category_stats = await db.jobs.aggregate(category_pipeline).to_list(100)

    # Jobs by status
    status_pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]

    status_stats = await db.jobs.aggregate(status_pipeline).to_list(100)

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "completion_rate": round(completion_rate, 2),
        "category_stats": category_stats,
        "status_distribution": status_stats
    }

# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================

@admin_router.get("/config")
async def get_platform_config(
    category: Optional[str] = None,
    current_user: User = Depends(require_admin_role())
):
    """Get platform configuration"""

    filter_dict = {}
    if category:
        filter_dict["category"] = category

    configs = await db.platform_config.find(filter_dict, {"_id": 0}).to_list(100)

    return configs

@admin_router.put("/config/{config_key}")
async def update_platform_config(
    config_key: str,
    config_data: ConfigUpdate,
    current_user: User = Depends(require_admin_role(AdminRole.OPERATIONS_ADMIN))
):
    """Update platform configuration"""

    config = PlatformConfig(
        key=config_key,
        value=config_data.value,
        category=config_data.category,
        description=config_data.description,
        updated_by=current_user.id
    )

    await db.platform_config.update_one(
        {"key": config_key},
        {"$set": config.model_dump()},
        upsert=True
    )

    return {"message": "Configuration updated successfully"}

# =============================================================================
# COMMUNICATION TOOLS
# =============================================================================

@admin_router.post("/announcements")
async def create_announcement(
    announcement_data: AnnouncementRequest,
    current_user: User = Depends(require_admin_role())
):
    """Create platform-wide announcement"""

    announcement = Announcement(
        title=announcement_data.title,
        message=announcement_data.message,
        target_audience=announcement_data.target_audience,
        target_user_ids=announcement_data.target_user_ids,
        announcement_type=announcement_data.type,
        priority=announcement_data.priority,
        start_date=announcement_data.start_date or datetime.now(timezone.utc),
        end_date=announcement_data.end_date,
        created_by=current_user.id
    )

    await db.announcements.insert_one(announcement.model_dump())

    # Create notifications for target users
    target_users = []
    if announcement.target_audience == "all":
        target_users = await db.users.find({}, {"_id": 0, "id": 1}).to_list(length=None)
    elif announcement.target_audience in ["customers", "workers"]:
        target_users = await db.users.find(
            {"role": announcement.target_audience[:-1]}, {"_id": 0, "id": 1}
        ).to_list(length=None)
    elif announcement.target_user_ids:
        target_users = [{"id": uid} for uid in announcement.target_user_ids]

    # Create notifications (batch insert)
    notifications = []
    for user in target_users:
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "type": "announcement",
            "title": announcement.title,
            "message": announcement.message,
            "data": {"announcement_id": announcement.id},
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        }
        notifications.append(notification)

    if notifications:
        await db.notifications.insert_many(notifications)

    return {"message": "Announcement created successfully", "notification_count": len(notifications)}
