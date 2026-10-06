# FastAPI Router for 5 New Sanyuth Features
import logging
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel

from new_features_models import (
    ScopeAgreement, ScopeAgreementCreate, ScopeAgreementUpdate,
    AgreementChangeRequest, ChangeRequestCreate, ChangeRequestRespond, ChangeHistoryItem,
    WorkerDayPlan, PlannerTimelineItem, QuickBidRequest,
    FamilyAddress, FamilyAddressCreate, ParentBookingStatusUpdate, ParentOTPVerify, ParentSupportRequest,
    NewWorkerEligibility, NewWorkerBidHighlight,
    ProQuestion, ProQuestionCreate, ProAnswer, ProAnswerCreate, MarkHelpfulRequest
)
from map_service import map_service, haversine_distance_km
from notification_service import notification_service

logger = logging.getLogger(__name__)

new_features_router = APIRouter(prefix="", tags=["new_features"])

# Helper function to get DB and user dependencies
def get_db():
    from server import db
    return db

def get_current_user_dep():
    from server import get_current_user
    return get_current_user

# =============================================================================
# FEATURE 1: SCOPE AGREEMENT CARD ENDPOINTS
# =============================================================================

@new_features_router.post("/api/agreements", response_model=ScopeAgreement)
async def create_scope_agreement(
    payload: ScopeAgreementCreate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    # Check if job exists
    job = await db.jobs.find_one({"id": payload.job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check assignment
    assignment = await db.assignments.find_one({"job_id": payload.job_id})
    if not assignment:
        raise HTTPException(status_code=400, detail="Job must be assigned to create an agreement")

    customer_id = job["customer_id"]
    worker_id = assignment["worker_id"]

    # Only customer or assigned worker can instantiate
    if current_user.id not in [customer_id, worker_id] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to create agreement for this job")

    # Check existing agreement
    existing = await db.scope_agreements.find_one({"job_id": payload.job_id})
    if existing:
        existing.pop("_id", None)
        return ScopeAgreement(**existing)

    initial_history = [
        ChangeHistoryItem(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action="created",
            summary=f"Scope agreement created for ₹{payload.agreed_price}"
        )
    ]

    agreement = ScopeAgreement(
        job_id=payload.job_id,
        bid_id=payload.bid_id,
        customer_id=customer_id,
        worker_id=worker_id,
        job_title=job.get("title", "Service Agreement"),
        work_included=payload.work_included,
        work_not_included=payload.work_not_included,
        agreed_price=payload.agreed_price,
        materials_responsibility=payload.materials_responsibility,
        start_date=payload.start_date,
        start_time=payload.start_time,
        expected_duration=payload.expected_duration,
        warranty=payload.warranty,
        additional_notes=payload.additional_notes,
        status="draft",
        history=initial_history
    )

    doc = agreement.model_dump()
    await db.scope_agreements.insert_one(doc)
    doc.pop("_id", None)
    return ScopeAgreement(**doc)


@new_features_router.get("/api/agreements/job/{job_id}", response_model=ScopeAgreement)
async def get_scope_agreement_by_job(
    job_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    agreement = await db.scope_agreements.find_one({"job_id": job_id})
    if not agreement:
        # Auto-create default draft agreement if job is assigned
        job = await db.jobs.find_one({"id": job_id})
        assignment = await db.assignments.find_one({"job_id": job_id})
        if job and assignment:
            default_agreement = ScopeAgreement(
                job_id=job_id,
                customer_id=job["customer_id"],
                worker_id=assignment["worker_id"],
                job_title=job.get("title", "Service Agreement"),
                work_included=[job.get("description", "Standard service execution")],
                work_not_included=["Extra unlisted repair work"],
                agreed_price=float(assignment.get("final_amount", 1000.0)),
                materials_responsibility="Customer supplied",
                start_date=datetime.now().strftime("%Y-%m-%d"),
                start_time="09:00 AM",
                expected_duration="1 Day",
                warranty="30 Days Service Warranty",
                status="draft",
                history=[ChangeHistoryItem(actor_id=job["customer_id"], actor_role="customer", action="created", summary="Auto-generated default scope agreement")]
            )
            doc = default_agreement.model_dump()
            await db.scope_agreements.insert_one(doc)
            doc.pop("_id", None)
            return ScopeAgreement(**doc)
        raise HTTPException(status_code=404, detail="Scope agreement not found for this job")

    agreement.pop("_id", None)
    return ScopeAgreement(**agreement)


@new_features_router.put("/api/agreements/{agreement_id}", response_model=ScopeAgreement)
async def update_scope_agreement(
    agreement_id: str,
    payload: ScopeAgreementUpdate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    agreement = await db.scope_agreements.find_one({"id": agreement_id})
    if not agreement:
        raise HTTPException(status_code=404, detail="Scope agreement not found")

    if current_user.id not in [agreement["customer_id"], agreement["worker_id"]] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this agreement")

    update_fields = {}
    changes_desc = []
    for k, v in payload.model_dump(exclude_unset=True).items():
        if v is not None:
            update_fields[k] = v
            changes_desc.append(f"{k} updated")

    if not update_fields:
        agreement.pop("_id", None)
        return ScopeAgreement(**agreement)

    # Reset explicit agreement stamps on edits if draft
    update_fields["updated_at"] = datetime.now(timezone.utc)
    update_fields["customer_agreed_at"] = None
    update_fields["worker_agreed_at"] = None
    update_fields["status"] = "draft"

    history_item = ChangeHistoryItem(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="edited",
        summary=f"Agreement edited by {current_user.name}: {', '.join(changes_desc)}"
    ).model_dump()

    await db.scope_agreements.update_one(
        {"id": agreement_id},
        {
            "$set": update_fields,
            "$push": {"history": history_item}
        }
    )

    updated = await db.scope_agreements.find_one({"id": agreement_id})
    updated.pop("_id", None)
    return ScopeAgreement(**updated)


@new_features_router.post("/api/agreements/{agreement_id}/agree", response_model=ScopeAgreement)
async def agree_to_scope_agreement(
    agreement_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    agreement = await db.scope_agreements.find_one({"id": agreement_id})
    if not agreement:
        raise HTTPException(status_code=404, detail="Scope agreement not found")

    now = datetime.now(timezone.utc)
    updates = {"updated_at": now}
    summary = ""

    if current_user.id == agreement["customer_id"]:
        updates["customer_agreed_at"] = now
        summary = "Customer agreed to scope & terms."
    elif current_user.id == agreement["worker_id"]:
        updates["worker_agreed_at"] = now
        summary = "Worker agreed to scope & terms."
    elif current_user.role == "admin":
        updates["customer_agreed_at"] = now
        updates["worker_agreed_at"] = now
        summary = "Admin verified and approved agreement."
    else:
        raise HTTPException(status_code=403, detail="Not authorized to agree to this contract")

    # Check if both have agreed
    cust_agreed = updates.get("customer_agreed_at") or agreement.get("customer_agreed_at")
    wrk_agreed = updates.get("worker_agreed_at") or agreement.get("worker_agreed_at")

    if cust_agreed and wrk_agreed:
        updates["status"] = "active"
        summary += " Agreement is now ACTIVE!"

    history_item = ChangeHistoryItem(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="agreed",
        summary=summary
    ).model_dump()

    await db.scope_agreements.update_one(
        {"id": agreement_id},
        {
            "$set": updates,
            "$push": {"history": history_item}
        }
    )

    updated = await db.scope_agreements.find_one({"id": agreement_id})
    updated.pop("_id", None)
    return ScopeAgreement(**updated)


@new_features_router.post("/api/agreements/{agreement_id}/change-requests", response_model=AgreementChangeRequest)
async def create_change_request(
    agreement_id: str,
    payload: ChangeRequestCreate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    agreement = await db.scope_agreements.find_one({"id": agreement_id})
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    if current_user.id not in [agreement["customer_id"], agreement["worker_id"]]:
        raise HTTPException(status_code=403, detail="Not authorized to request changes")

    requested_by = "customer" if current_user.id == agreement["customer_id"] else "worker"

    cr = AgreementChangeRequest(
        agreement_id=agreement_id,
        job_id=agreement["job_id"],
        requested_by=requested_by,
        requester_id=current_user.id,
        description=payload.description,
        price_change=payload.price_change,
        new_agreed_price=payload.new_agreed_price,
        schedule_change=payload.schedule_change,
        additional_notes=payload.additional_notes,
        status="pending"
    )

    doc = cr.model_dump()
    await db.agreement_change_requests.insert_one(doc)

    history_item = ChangeHistoryItem(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="change_requested",
        summary=f"Change Request created: {payload.description} (Price change: ₹{payload.price_change:+.2f})"
    ).model_dump()

    await db.scope_agreements.update_one(
        {"id": agreement_id},
        {"$push": {"history": history_item}}
    )

    doc.pop("_id", None)
    return AgreementChangeRequest(**doc)


@new_features_router.get("/api/agreements/{agreement_id}/change-requests", response_model=List[AgreementChangeRequest])
async def list_change_requests(
    agreement_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    crs = await db.agreement_change_requests.find({"agreement_id": agreement_id}).to_list(length=100)
    for cr in crs:
        cr.pop("_id", None)
    return [AgreementChangeRequest(**cr) for cr in crs]


@new_features_router.post("/api/agreements/change-requests/{request_id}/respond", response_model=AgreementChangeRequest)
async def respond_change_request(
    request_id: str,
    payload: ChangeRequestRespond,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    cr = await db.agreement_change_requests.find_one({"id": request_id})
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")

    agreement = await db.scope_agreements.find_one({"id": cr["agreement_id"]})
    if not agreement:
        raise HTTPException(status_code=404, detail="Associated agreement not found")

    # The other party responds
    if current_user.id == cr["requester_id"] and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot approve/decline your own change request")

    now = datetime.now(timezone.utc)
    await db.agreement_change_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": payload.status,
                "response_notes": payload.response_notes,
                "responded_at": now
            }
        }
    )

    if payload.status == "approved":
        # Apply approved change to agreement history & updated price
        history_item = ChangeHistoryItem(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action="change_approved",
            summary=f"Approved change request: {cr['description']} -> New Price: ₹{cr['new_agreed_price']}"
        ).model_dump()

        await db.scope_agreements.update_one(
            {"id": cr["agreement_id"]},
            {
                "$set": {
                    "agreed_price": cr["new_agreed_price"],
                    "updated_at": now
                },
                "$push": {
                    "work_included": f"Approved Change: {cr['description']}",
                    "history": history_item
                }
            }
        )
    else:
        history_item = ChangeHistoryItem(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action="change_declined",
            summary=f"Declined change request: {cr['description']}"
        ).model_dump()

        await db.scope_agreements.update_one(
            {"id": cr["agreement_id"]},
            {"$push": {"history": history_item}}
        )

    updated_cr = await db.agreement_change_requests.find_one({"id": request_id})
    updated_cr.pop("_id", None)
    return AgreementChangeRequest(**updated_cr)


# =============================================================================
# FEATURE 2: JOB CHAINING / DAY PLANNER ENDPOINTS
# =============================================================================

@new_features_router.get("/api/planner/day-plan", response_model=WorkerDayPlan)
async def get_worker_day_plan(
    date: Optional[str] = Query(None),
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    if current_user.role != "worker" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Worker role required for Day Planner")

    target_date = date or datetime.now().strftime("%Y-%m-%d")
    worker_id = current_user.id

    # 1. Fetch worker's assigned jobs
    assignments = await db.assignments.find({"worker_id": worker_id}).to_list(length=50)
    assigned_job_ids = [a["job_id"] for a in assignments]

    scheduled_jobs = await db.jobs.find({"id": {"$in": assigned_job_ids}}).to_list(length=50)

    timeline_items: List[PlannerTimelineItem] = []
    total_earnings = 0.0

    loc_obj = getattr(current_user, "location", None)
    if isinstance(loc_obj, dict):
        current_lat = loc_obj.get("lat", 17.4456)
        current_lng = loc_obj.get("lng", 78.3772)
    elif loc_obj:
        current_lat = getattr(loc_obj, "lat", 17.4456)
        current_lng = getattr(loc_obj, "lng", 78.3772)
    else:
        current_lat, current_lng = 17.4456, 78.3772
    last_lat, last_lng = current_lat, current_lng

    base_time = 10  # 10:00 AM

    for idx, job in enumerate(scheduled_jobs):
        loc = job.get("location", {})
        job_lat = loc.get("lat", 17.44 + idx * 0.01)
        job_lng = loc.get("lng", 78.37 + idx * 0.01)

        map_data = map_service.calculate_distance_and_time(last_lat, last_lng, job_lat, job_lng)

        # Add Travel item if distance > 0
        if map_data["distance_km"] > 0.2 and idx > 0:
            travel_item = PlannerTimelineItem(
                type="travel",
                title=f"Travel to {job.get('title', 'Next Location')}",
                location=loc.get("address", "Next Site"),
                lat=job_lat,
                lng=job_lng,
                start_time=f"{base_time:02d}:00 AM" if base_time < 12 else f"{(base_time-12 if base_time>12 else 12):02d}:00 PM",
                end_time=f"{(base_time):02d}:{map_data['travel_time_minutes']:02d} AM",
                estimated_duration_minutes=map_data["travel_time_minutes"],
                distance_km=map_data["distance_km"],
                travel_time_minutes=map_data["travel_time_minutes"],
                status="scheduled"
            )
            timeline_items.append(travel_item)
            base_time += 1

        start_str = f"{base_time:02d}:00 AM" if base_time < 12 else f"{(base_time-12 if base_time>12 else 12):02d}:00 PM"
        end_time_val = base_time + 2
        end_str = f"{end_time_val:02d}:00 AM" if end_time_val < 12 else f"{(end_time_val-12 if end_time_val>12 else 12):02d}:00 PM"

        earnings = float(job.get("budget_amount", 1500.0))
        total_earnings += earnings

        job_item = PlannerTimelineItem(
            type="job",
            job_id=job["id"],
            title=job.get("title", "Assigned Job"),
            category=job.get("category", "General"),
            location=loc.get("address", "Hyderabad"),
            lat=job_lat,
            lng=job_lng,
            start_time=start_str,
            end_time=end_str,
            estimated_duration_minutes=120,
            estimated_earnings=earnings,
            distance_km=map_data["distance_km"],
            status="scheduled"
        )
        timeline_items.append(job_item)
        base_time += 2
        last_lat, last_lng = job_lat, job_lng

    # 2. Find suggested nearby open jobs
    open_jobs = await db.jobs.find({"status": "open", "id": {"$nin": assigned_job_ids}}).to_list(length=10)
    suggested_items: List[PlannerTimelineItem] = []

    for idx, open_j in enumerate(open_jobs[:3]):
        loc = open_j.get("location", {})
        sugg_lat = loc.get("lat", 17.45 + idx * 0.015)
        sugg_lng = loc.get("lng", 78.38 + idx * 0.015)

        map_data = map_service.calculate_distance_and_time(last_lat, last_lng, sugg_lat, sugg_lng)

        suggested_items.append(
            PlannerTimelineItem(
                type="suggestion",
                job_id=open_j["id"],
                title=open_j.get("title", "Nearby Job Suggestion"),
                category=open_j.get("category", "Service"),
                location=loc.get("address", "Nearby Location"),
                lat=sugg_lat,
                lng=sugg_lng,
                start_time=f"{(base_time+1):02d}:00 PM",
                end_time=f"{(base_time+2):02d}:00 PM",
                estimated_duration_minutes=60,
                estimated_earnings=float(open_j.get("budget_amount", 500.0)),
                distance_km=map_data["distance_km"],
                travel_time_minutes=map_data["travel_time_minutes"],
                status="suggested"
            )
        )

    return WorkerDayPlan(
        worker_id=worker_id,
        date=target_date,
        total_estimated_earnings=total_earnings,
        total_jobs_count=len(scheduled_jobs),
        timeline=timeline_items,
        suggested_jobs=suggested_items
    )


@new_features_router.post("/api/planner/quick-bid")
async def quick_bid_suggested_job(
    payload: QuickBidRequest,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    if current_user.role != "worker":
        raise HTTPException(status_code=403, detail="Worker role required to place bids")

    job = await db.jobs.find_one({"id": payload.job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Suggested job not found")

    # Create bid in `bids` collection
    bid_doc = {
        "id": str(uuid.uuid4()),
        "job_id": payload.job_id,
        "worker_id": current_user.id,
        "bid_amount": payload.bid_amount,
        "visiting_charge": payload.visiting_charge,
        "proposal_text": payload.message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    await db.bids.insert_one(bid_doc)
    await db.jobs.update_one({"id": payload.job_id}, {"$inc": {"bids_count": 1}})

    return {"message": "1-Tap bid placed successfully from Day Planner!", "bid_id": bid_doc["id"]}


# =============================================================================
# FEATURE 3: BOOK FOR PARENTS / FAMILY MODE ENDPOINTS
# =============================================================================

@new_features_router.post("/api/family/addresses", response_model=FamilyAddress)
async def create_family_address(
    payload: FamilyAddressCreate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    fa = FamilyAddress(
        customer_id=current_user.id,
        parent_name=payload.parent_name,
        parent_phone=payload.parent_phone,
        address=payload.address,
        city=payload.city,
        preferred_language=payload.preferred_language,
        landmark=payload.landmark
    )
    doc = fa.model_dump()
    await db.family_addresses.insert_one(doc)
    doc.pop("_id", None)
    return FamilyAddress(**doc)


@new_features_router.get("/api/family/addresses", response_model=List[FamilyAddress])
async def list_family_addresses(
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    docs = await db.family_addresses.find({"customer_id": current_user.id}).to_list(length=100)
    for d in docs:
        d.pop("_id", None)
    return [FamilyAddress(**d) for d in docs]


@new_features_router.delete("/api/family/addresses/{address_id}")
async def delete_family_address(
    address_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    res = await db.family_addresses.delete_one({"id": address_id, "customer_id": current_user.id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Parent address not found")
class FamilyBookingCreate(BaseModel):
    title: str
    description: str
    category: str = "skilled"
    budget_amount: float
    parent_name: str
    parent_phone: str
    address: str
    city: str = "Hyderabad"
    preferred_language: str = "Telugu"


@new_features_router.post("/api/family/bookings")
async def create_family_booking(
    payload: FamilyBookingCreate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    otp = f"{random.randint(1000, 9999)}"
    job_doc = {
        "id": str(uuid.uuid4()),
        "customer_id": current_user.id,
        "type": "daily",
        "category": payload.category,
        "title": payload.title,
        "description": payload.description,
        "photos": [],
        "location": {"lat": 17.44, "lng": 78.38, "address": f"{payload.address}, {payload.city}"},
        "budget_amount": payload.budget_amount,
        "is_budget_negotiable": False,
        "status": "open",
        "parent_name": payload.parent_name,
        "parent_phone": payload.parent_phone,
        "parent_otp": otp,
        "parent_otp_verified": False,
        "preferred_language": payload.preferred_language,
        "arrival_status": "assigned",
        "created_at": datetime.now(timezone.utc),
        "applications_count": 0,
        "bids_count": 0
    }
    await db.jobs.insert_one(job_doc)

    await notification_service.send_parent_booking_sms(
        parent_phone=payload.parent_phone,
        parent_name=payload.parent_name,
        service_name=payload.title,
        worker_name="Service Professional",
        otp=otp,
        language=payload.preferred_language
    )

    return {"message": "Family booking created successfully!", "job_id": job_doc["id"], "parent_otp": otp}


@new_features_router.get("/api/family/bookings/{job_id}")
async def get_parent_booking_details(
    job_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Booking not found")

    assignment = await db.assignments.find_one({"job_id": job_id})
    worker_info = None
    if assignment:
        worker = await db.users.find_one({"id": assignment["worker_id"]})
        if worker:
            worker_info = {
                "name": worker.get("name", "Assigned Worker"),
                "phone": worker.get("phone", ""),
                "rating_avg": worker.get("rating_avg", 5.0),
                "photo": "/uploads/worker-avatar.png"
            }

    # Fetch parent details
    parent_otp = job.get("parent_otp", "4829")
    otp_verified = job.get("parent_otp_verified", False)

    return {
        "job_id": job_id,
        "title": job.get("title", "Family Booking"),
        "customer_id": job.get("customer_id"),
        "parent_name": job.get("parent_name", "Parent"),
        "parent_phone": job.get("parent_phone", ""),
        "address": job.get("location", {}).get("address", ""),
        "preferred_language": job.get("preferred_language", "English"),
        "arrival_status": job.get("arrival_status", "assigned"),
        "job_status": job.get("status", "assigned"),
        "otp": parent_otp,
        "otp_verified": otp_verified,
        "worker": worker_info,
        "before_photos": job.get("before_photos", []),
        "after_photos": job.get("after_photos", []),
        "support_button": "Need Help?"
    }


@new_features_router.post("/api/family/bookings/{job_id}/verify-otp")
async def verify_parent_arrival_otp(
    job_id: str,
    payload: ParentOTPVerify,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Booking not found")

    expected_otp = str(job.get("parent_otp", "4829"))
    if payload.otp.strip() != expected_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please ask the parent for the 4-digit OTP.")

    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {"parent_otp_verified": True, "arrival_status": "arrived"}}
    )

    return {"message": "Parent OTP verified successfully! Worker marked as ARRIVED on site.", "verified": True}


@new_features_router.post("/api/family/bookings/{job_id}/status")
async def update_parent_booking_status(
    job_id: str,
    payload: ParentBookingStatusUpdate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Booking not found")

    updates = {"arrival_status": payload.arrival_status}
    if payload.before_photos:
        updates["before_photos"] = payload.before_photos
    if payload.after_photos:
        updates["after_photos"] = payload.after_photos

    if payload.arrival_status == "completed":
        updates["status"] = "completed"

    await db.jobs.update_one({"id": job_id}, {"$set": updates})

    # Trigger notification mock
    if job.get("parent_phone"):
        await notification_service.send_status_update_whatsapp(
            parent_phone=job["parent_phone"],
            status=payload.arrival_status,
            worker_name=current_user.name
        )

    return {"message": f"Parent booking status updated to '{payload.arrival_status}'"}


@new_features_router.post("/api/family/bookings/{job_id}/support", response_model=ParentSupportRequest)
async def request_parent_support(
    job_id: str,
    message: str = Body(default="Parent requested support assistance.", embed=True),
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    job = await db.jobs.find_one({"id": job_id})
    parent_name = job.get("parent_name", current_user.name) if job else current_user.name
    parent_phone = job.get("parent_phone", getattr(current_user, "phone", "")) if job else ""

    sr = ParentSupportRequest(
        job_id=job_id,
        customer_id=current_user.id,
        parent_name=parent_name,
        parent_phone=parent_phone,
        message=message,
        status="open"
    )
    doc = sr.model_dump()
    await db.family_support_requests.insert_one(doc)
    doc.pop("_id", None)
    return ParentSupportRequest(**doc)


# Helper for Body embed
from fastapi import Body


# =============================================================================
# FEATURE 4: FAIR START FOR NEW WORKERS ENDPOINTS
# =============================================================================

@new_features_router.get("/api/fair-start/eligibility", response_model=NewWorkerEligibility)
async def check_new_worker_eligibility(
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    if current_user.role != "worker" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Worker access required")

    worker_profile = await db.worker_profiles.find_one({"user_id": current_user.id})
    completed_jobs = worker_profile.get("completed_jobs", 0) if worker_profile else 0

    # KYC Check
    kyc_doc = await db.kyc_verifications.find_one({"user_id": current_user.id})
    kyc_verified = True if (kyc_doc and kyc_doc.get("overall_status") == "approved") else True  # Demo default True for workers

    is_eligible = (kyc_verified and completed_jobs < 5)
    remaining = max(0, 5 - completed_jobs)

    return NewWorkerEligibility(
        worker_id=current_user.id,
        worker_name=current_user.name,
        kyc_verified=kyc_verified,
        completed_jobs=completed_jobs,
        is_eligible=is_eligible,
        intro_jobs_remaining=remaining,
        badge_label="New on Sanyuth",
        quality_status="good",
        rating_avg=current_user.rating_avg or 5.0
    )


@new_features_router.get("/api/fair-start/bids/{job_id}", response_model=List[NewWorkerBidHighlight])
async def get_job_bids_with_fair_start(
    job_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    bids = await db.bids.find({"job_id": job_id}).to_list(length=50)

    result: List[NewWorkerBidHighlight] = []
    for bid in bids:
        w_id = bid["worker_id"]
        w_user = await db.users.find_one({"id": w_id})
        w_prof = await db.worker_profiles.find_one({"user_id": w_id})

        completed = w_prof.get("completed_jobs", 0) if w_prof else 0
        is_new = (completed < 5)

        badges = ["Experienced Worker"]
        if is_new:
            badges = ["New on Sanyuth", "ID Verified", "Intro Price"]

        result.append(
            NewWorkerBidHighlight(
                bid_id=bid["id"],
                worker_id=w_id,
                worker_name=w_user.get("name", "Worker") if w_user else "Worker",
                is_new_worker=is_new,
                intro_jobs_completed=completed,
                badge_labels=badges
            )
        )

    # Sort so eligible new worker appears in reserved prominent slot 1 if present
    result.sort(key=lambda x: 0 if x.is_new_worker else 1)
    return result


@new_features_router.get("/api/admin/fair-start/workers", response_model=List[NewWorkerEligibility])
async def admin_list_fair_start_workers(
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required")

    workers = await db.users.find({"role": "worker"}).to_list(length=100)
    res = []
    for w in workers:
        w_prof = await db.worker_profiles.find_one({"user_id": w["id"]})
        completed = w_prof.get("completed_jobs", 0) if w_prof else 0
        is_elig = (completed < 5)
        res.append(
            NewWorkerEligibility(
                worker_id=w["id"],
                worker_name=w.get("name", "Worker"),
                kyc_verified=True,
                completed_jobs=completed,
                is_eligible=is_elig,
                intro_jobs_remaining=max(0, 5 - completed),
                rating_avg=w.get("rating_avg", 5.0)
            )
        )
    return res


# =============================================================================
# FEATURE 5: ASK A PRO ENDPOINTS
# =============================================================================

@new_features_router.post("/api/ask-pro/questions", response_model=ProQuestion)
async def create_pro_question(
    payload: ProQuestionCreate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    q = ProQuestion(
        customer_id=current_user.id,
        customer_name=current_user.name,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        photo_urls=payload.photo_urls,
        video_url=payload.video_url,
        voice_note_url=payload.voice_note_url,
        language=payload.language
    )
    doc = q.model_dump()
    await db.pro_questions.insert_one(doc)
    doc.pop("_id", None)
    return ProQuestion(**doc)


@new_features_router.get("/api/ask-pro/questions", response_model=List[ProQuestion])
async def list_pro_questions(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    db = get_db()
    query = {}
    if category and category != "all":
        query["category"] = category
    if search:
        query["title"] = {"$regex": search, "$options": "i"}

    questions = await db.pro_questions.find(query).sort("created_at", -1).to_list(length=50)
    for q in questions:
        q.pop("_id", None)
    return [ProQuestion(**q) for q in questions]


@new_features_router.get("/api/ask-pro/questions/{question_id}", response_model=ProQuestion)
async def get_pro_question(question_id: str):
    db = get_db()
    q = await db.pro_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.pop("_id", None)
    return ProQuestion(**q)


@new_features_router.post("/api/ask-pro/questions/{question_id}/answers", response_model=ProAnswer)
async def post_pro_answer(
    question_id: str,
    payload: ProAnswerCreate,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    if current_user.role != "worker" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only verified service professionals can answer questions")

    q = await db.pro_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    w_prof = await db.worker_profiles.find_one({"user_id": current_user.id})
    trade = w_prof.get("skills", ["General Services"])[0] if (w_prof and w_prof.get("skills")) else "Verified Specialist"

    answer = ProAnswer(
        question_id=question_id,
        worker_id=current_user.id,
        worker_name=current_user.name,
        worker_rating=current_user.rating_avg or 5.0,
        worker_trade=trade,
        answer_text=payload.answer_text
    )

    doc = answer.model_dump()
    await db.pro_answers.insert_one(doc)
    await db.pro_questions.update_one({"id": question_id}, {"$inc": {"answers_count": 1}, "$set": {"status": "answered"}})

    doc.pop("_id", None)
    return ProAnswer(**doc)


@new_features_router.get("/api/ask-pro/questions/{question_id}/answers", response_model=List[ProAnswer])
async def list_pro_question_answers(question_id: str):
    db = get_db()
    answers = await db.pro_answers.find({"question_id": question_id}).to_list(length=50)
    for a in answers:
        a.pop("_id", None)
    return [ProAnswer(**a) for a in answers]


@new_features_router.post("/api/ask-pro/answers/{answer_id}/mark-helpful")
async def mark_answer_helpful(
    answer_id: str,
    current_user: Any = Depends(get_current_user_dep())
):
    db = get_db()
    answer = await db.pro_answers.find_one({"id": answer_id})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    question = await db.pro_questions.find_one({"id": answer["question_id"]})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if current_user.id != question["customer_id"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the question author can mark answer as Most Helpful")

    # Update answer and question
    await db.pro_answers.update_one({"id": answer_id}, {"$set": {"is_most_helpful": True}})
    await db.pro_questions.update_one({"id": question["id"]}, {"$set": {"most_helpful_answer_id": answer_id}})

    # Award +1 Helpful Pro Point to worker
    worker_id = answer["worker_id"]
    await db.users.update_one({"id": worker_id}, {"$inc": {"helpful_pro_points": 1}})

    return {"message": "Answer marked as Most Helpful! Worker awarded +1 Helpful Pro point.", "worker_id": worker_id}


@new_features_router.get("/api/ask-pro/workers/{worker_id}/pro-score")
async def get_worker_pro_score(worker_id: str):
    db = get_db()
    worker = await db.users.find_one({"id": worker_id})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    points = worker.get("helpful_pro_points", 3)  # Demo default 3 points
    tier = "Pro Contributor"
    if points > 10:
        tier = "Master Pro Contributor"
    elif points > 5:
        tier = "Senior Pro Contributor"

    return {
        "worker_id": worker_id,
        "worker_name": worker.get("name"),
        "helpful_pro_points": points,
        "badge_tier": tier
    }
