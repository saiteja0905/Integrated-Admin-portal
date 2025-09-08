# Admin Portal Routes for Shidhaan Marketplace
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from admin_models import *
from server import get_current_user, User, UserRole, db

admin_router = APIRouter(prefix="/admin", tags=["admin"])

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
    
    # Get dispute counts
    pending_disputes = await db.disputes.count_documents({"status": {"$in": ["open", "under_review"]}}) if await db.list_collection_names() and 'disputes' in await db.list_collection_names() else 0
    
    # Get KYC counts
    pending_kyc = await db.kyc_verifications.count_documents({"overall_status": "pending"}) if await db.list_collection_names() and 'kyc_verifications' in await db.list_collection_names() else 0
    
    # Get revenue data
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)
    
    # Calculate revenue (from payments collection)
    revenue_today_pipeline = [
        {"$match": {"created_at": {"$gte": today}, "status": "succeeded"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    
    revenue_month_pipeline = [
        {"$match": {"created_at": {"$gte": month_start}, "status": "succeeded"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    
    revenue_today_result = await db.payments.aggregate(revenue_today_pipeline).to_list(1) if await db.list_collection_names() and 'payments' in await db.list_collection_names() else []
    revenue_month_result = await db.payments.aggregate(revenue_month_pipeline).to_list(1) if await db.list_collection_names() and 'payments' in await db.list_collection_names() else []
    
    revenue_today = revenue_today_result[0]["total"] if revenue_today_result else 0.0
    revenue_month = revenue_month_result[0]["total"] if revenue_month_result else 0.0
    
    # Get top performing workers
    top_workers_pipeline = [
        {"$match": {"role": "worker"}},
        {"$sort": {"rating_avg": -1, "reviews_count": -1}},
        {"$limit": 5},
        {"$project": {"name": 1, "rating_avg": 1, "reviews_count": 1}}
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

@admin_router.get("/users", response_model=List[User])
async def get_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, le=100),
    skip: int = 0,
    current_user: User = Depends(require_admin_role())
):
    """Get all users with filtering and search"""
    filter_dict = {}
    
    if role:
        filter_dict["role"] = role
    
    if search:
        filter_dict["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    users = await db.users.find(filter_dict).skip(skip).limit(limit).to_list(limit)
    return [User(**{k: v for k, v in user.items() if k != 'password_hash'}) for user in users]

@admin_router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    current_user: User = Depends(require_admin_role())
):
    """Get user activity timeline"""
    
    # Get user info
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    
    return {
        "user": {k: v for k, v in user.items() if k != 'password_hash'},
        "jobs_posted": len(jobs) if user["role"] == "customer" else 0,
        "applications_sent": len(applications),
        "bids_placed": len(bids),
        "payments_made": len([p for p in payments if p["payer_id"] == user_id]),
        "payments_received": len([p for p in payments if p["payee_id"] == user_id]),
        "reviews_given": len(reviews_given),
        "reviews_received": len(reviews_received),
        "recent_jobs": jobs[:5],
        "recent_applications": applications[:5],
        "recent_reviews": reviews_received[:5]
    }

@admin_router.post("/users/{user_id}/strike")
async def issue_user_strike(
    user_id: str,
    strike_data: dict,
    current_user: User = Depends(require_admin_role())
):
    """Issue a strike/warning to a user"""
    
    strike = UserStrike(
        user_id=user_id,
        reason=strike_data["reason"],
        description=strike_data["description"],
        severity=strike_data.get("severity", "medium"),
        issued_by=current_user.id
    )
    
    await db.user_strikes.insert_one(strike.model_dump())
    
    # Update user's strike count
    strike_count = await db.user_strikes.count_documents({"user_id": user_id, "is_active": True})
    
    # Auto-suspend if too many strikes
    if strike_count >= 3:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"status": "suspended", "suspended_at": datetime.now(timezone.utc)}}
        )
    
    return {"message": "Strike issued successfully", "total_strikes": strike_count}

# =============================================================================
# KYC MANAGEMENT
# =============================================================================

@admin_router.get("/kyc/pending", response_model=List[KYCVerification])
async def get_pending_kyc(
    limit: int = 20,
    skip: int = 0,
    current_user: User = Depends(require_admin_role())
):
    """Get all pending KYC verifications"""
    
    kyc_docs = await db.kyc_verifications.find(
        {"overall_status": "pending"}
    ).skip(skip).limit(limit).to_list(limit)
    
    return [KYCVerification(**kyc) for kyc in kyc_docs]

@admin_router.put("/kyc/{kyc_id}/verify")
async def verify_kyc(
    kyc_id: str,
    verification_data: dict,
    current_user: User = Depends(require_admin_role())
):
    """Approve or reject KYC verification"""
    
    status = verification_data["status"]  # "approved" or "rejected"
    notes = verification_data.get("notes", "")
    
    await db.kyc_verifications.update_one(
        {"id": kyc_id},
        {"$set": {
            "overall_status": status,
            "verification_notes": notes,
            "verified_by": current_user.id,
            "verified_at": datetime.now(timezone.utc)
        }}
    )
    
    # Update user verification status
    kyc_doc = await db.kyc_verifications.find_one({"id": kyc_id})
    if kyc_doc:
        await db.users.update_one(
            {"id": kyc_doc["user_id"]},
            {"$set": {"kyc_verified": status == "approved"}}
        )
    
    return {"message": f"KYC {status} successfully"}

# =============================================================================
# JOB MANAGEMENT
# =============================================================================

@admin_router.get("/jobs/moderation")
async def get_jobs_for_moderation(
    status: str = "pending",
    limit: int = 20,
    skip: int = 0,
    current_user: User = Depends(require_admin_role())
):
    """Get jobs that need content moderation"""
    
    # Get flagged jobs
    flagged_content = await db.content_flags.find({
        "content_type": "job_post",
        "status": status
    }).skip(skip).limit(limit).to_list(limit)
    
    job_ids = [flag["content_id"] for flag in flagged_content]
    
    if job_ids:
        jobs = await db.jobs.find({"id": {"$in": job_ids}}).to_list(len(job_ids))
    else:
        jobs = []
    
    # Combine job data with flag information
    result = []
    for flag in flagged_content:
        job = next((j for j in jobs if j["id"] == flag["content_id"]), None)
        if job:
            result.append({
                "flag": flag,
                "job": job
            })
    
    return result

@admin_router.put("/jobs/{job_id}/moderate")
async def moderate_job_content(
    job_id: str,
    moderation_data: dict,
    current_user: User = Depends(require_admin_role())
):
    """Approve, reject, or flag job content"""
    
    action = moderation_data["action"]  # "approve", "reject", "flag"
    reason = moderation_data.get("reason", "")
    
    # Update content flag status
    await db.content_flags.update_many(
        {"content_id": job_id, "content_type": "job_post"},
        {"$set": {
            "status": "resolved" if action == "approve" else "rejected",
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.now(timezone.utc),
            "action_taken": action
        }}
    )
    
    # Take action on the job
    if action == "reject":
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {"status": "rejected", "moderation_reason": reason}}
        )
    elif action == "flag":
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {"is_flagged": True, "flag_reason": reason}}
        )
    
    return {"message": f"Job {action}ed successfully"}

# =============================================================================
# DISPUTE MANAGEMENT
# =============================================================================

@admin_router.get("/disputes", response_model=List[Dispute])
async def get_disputes(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
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
    
    disputes = await db.disputes.find(filter_dict).skip(skip).limit(limit).to_list(limit)
    return [Dispute(**dispute) for dispute in disputes]

@admin_router.put("/disputes/{dispute_id}/assign")
async def assign_dispute(
    dispute_id: str,
    assignment_data: dict,
    current_user: User = Depends(require_admin_role())
):
    """Assign dispute to an admin"""
    
    await db.disputes.update_one(
        {"id": dispute_id},
        {"$set": {
            "assigned_to": assignment_data["admin_id"],
            "status": "under_review"
        }}
    )
    
    return {"message": "Dispute assigned successfully"}

@admin_router.post("/disputes/{dispute_id}/action")
async def take_dispute_action(
    dispute_id: str,
    action_data: dict,
    current_user: User = Depends(require_admin_role())
):
    """Take action on a dispute"""
    
    action = DisputeAction(
        dispute_id=dispute_id,
        admin_id=current_user.id,
        action_type=action_data["action_type"],
        action_details=action_data.get("details", {}),
        notes=action_data.get("notes", "")
    )
    
    await db.dispute_actions.insert_one(action.model_dump())
    
    # Update dispute status
    new_status = "resolved" if action_data["action_type"] in ["refund", "resolve"] else "under_review"
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
            "status": "succeeded"
        }},
        {"$group": {
            "_id": group_by,
            "total_revenue": {"$sum": "$amount"},
            "transaction_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = await db.payments.aggregate(pipeline).to_list(100) if await db.list_collection_names() and 'payments' in await db.list_collection_names() else []
    
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
    
    configs = await db.platform_config.find(filter_dict).to_list(100) if await db.list_collection_names() and 'platform_config' in await db.list_collection_names() else []
    
    return configs

@admin_router.put("/config/{config_key}")
async def update_platform_config(
    config_key: str,
    config_data: dict,
    current_user: User = Depends(require_admin_role(AdminRole.OPERATIONS_ADMIN))
):
    """Update platform configuration"""
    
    config = PlatformConfig(
        key=config_key,
        value=config_data["value"],
        category=config_data["category"],
        description=config_data.get("description", ""),
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
    announcement_data: dict,
    current_user: User = Depends(require_admin_role())
):
    """Create platform-wide announcement"""
    
    announcement = Announcement(
        title=announcement_data["title"],
        message=announcement_data["message"],
        target_audience=announcement_data.get("target_audience", "all"),
        target_user_ids=announcement_data.get("target_user_ids", []),
        announcement_type=announcement_data.get("type", "info"),
        priority=announcement_data.get("priority", "normal"),
        start_date=datetime.fromisoformat(announcement_data["start_date"]),
        end_date=datetime.fromisoformat(announcement_data["end_date"]) if announcement_data.get("end_date") else None,
        created_by=current_user.id
    )
    
    await db.announcements.insert_one(announcement.model_dump())
    
    # Create notifications for target users
    target_users = []
    if announcement.target_audience == "all":
        target_users = await db.users.find({}, {"id": 1}).to_list(1000)
    elif announcement.target_audience in ["customers", "workers"]:
        target_users = await db.users.find({"role": announcement.target_audience[:-1]}, {"id": 1}).to_list(1000)
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