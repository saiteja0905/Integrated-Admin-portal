from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
import uuid
import re
import razorpay
import math
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB connection
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# Security
SECRET_KEY = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Razorpay Setup (using placeholder keys for demo)
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_placeholder")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "test_secret_placeholder")

# Initialize Razorpay client (with error handling for missing keys)
razorpay_client = None
try:
    if (
        RAZORPAY_KEY_ID != "rzp_test_placeholder"
        and RAZORPAY_KEY_SECRET != "test_secret_placeholder"
    ):
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception as e:
    logging.warning(f"Razorpay client initialization failed: {e}")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(title="Shidhaan API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# =============================================================================
# STARTUP EVENT - AUTO SEED DEMO DATA
# =============================================================================


async def seed_demo_data():
    """Auto-seed demo users and data on startup if database is empty"""
    try:
        # Check if any users exist
        user_count = await db.users.count_documents({})

        if user_count == 0:
            logger.info("🌱 Database is empty. Seeding demo data...")

            # Demo users data
            demo_users = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Rajesh Kumar",
                    "phone": "9876543210",
                    "email": "customer@demo.com",
                    "role": "customer",
                    "languages": ["en", "hi"],
                    "location": {
                        "lat": 28.6139,
                        "lng": 77.2090,
                        "address": "Connaught Place, New Delhi, India",
                    },
                    "rating_avg": 4.5,
                    "reviews_count": 12,
                    "created_at": datetime.now(timezone.utc),
                    "password_hash": pwd_context.hash("password123"),
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Priya Sharma",
                    "phone": "9876543211",
                    "email": "worker@demo.com",
                    "role": "worker",
                    "languages": ["en", "hi"],
                    "location": {
                        "lat": 28.5355,
                        "lng": 77.3910,
                        "address": "Noida, Uttar Pradesh, India",
                    },
                    "rating_avg": 4.7,
                    "reviews_count": 25,
                    "created_at": datetime.now(timezone.utc),
                    "password_hash": pwd_context.hash("password123"),
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Admin User",
                    "phone": "9876543212",
                    "email": "admin@shidhaan.com",
                    "role": "admin",
                    "languages": ["en", "hi"],
                    "rating_avg": 5.0,
                    "reviews_count": 0,
                    "created_at": datetime.now(timezone.utc),
                    "password_hash": pwd_context.hash("admin123"),
                },
            ]

            # Insert demo users
            for user in demo_users:
                await db.users.insert_one(user)
                logger.info(
                    f"✅ Created {user['role']}: {user['name']} ({user['phone']})"
                )

                # Create worker profile for worker user
                if user["role"] == "worker":
                    worker_profile = {
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "skills": ["Plumbing", "Electrical Work", "Carpentry"],
                        "experience_years": 5,
                        "certifications": ["ITI Certificate", "Safety Training"],
                        "preferred_locations": [user["location"]],
                        "completed_jobs": 18,
                        "cancelled_jobs": 1,
                        "trust_score": 85.5,
                        "service_radius_km": 10,
                    }
                    await db.worker_profiles.insert_one(worker_profile)
                    logger.info(f"✅ Created worker profile for {user['name']}")

            # Create demo jobs
            demo_jobs = [
                {
                    "id": str(uuid.uuid4()),
                    "customer_id": demo_users[0]["id"],
                    "type": "daily",
                    "category": "skilled",
                    "title": "Bathroom Plumbing Repair",
                    "description": "Need experienced plumber to fix leaking pipes in bathroom. Urgent work required.",
                    "photos": [],
                    "location": {
                        "lat": 28.6139,
                        "lng": 77.2090,
                        "address": "Connaught Place, New Delhi, India",
                    },
                    "preferred_time_window": {"start": "09:00", "end": "17:00"},
                    "budget_amount": 2500.0,
                    "is_budget_negotiable": False,
                    "status": "open",
                    "created_at": datetime.now(timezone.utc),
                    "applications_count": 0,
                    "bids_count": 0,
                },
                {
                    "id": str(uuid.uuid4()),
                    "customer_id": demo_users[0]["id"],
                    "type": "contractual",
                    "category": "skilled",
                    "title": "Kitchen Renovation Work",
                    "description": "Looking for skilled workers for complete kitchen renovation. Need carpentry and electrical work.",
                    "photos": [],
                    "location": {
                        "lat": 28.6139,
                        "lng": 77.2090,
                        "address": "Connaught Place, New Delhi, India",
                    },
                    "preferred_time_window": {"start": "08:00", "end": "18:00"},
                    "budget_amount": 50000.0,
                    "is_budget_negotiable": True,
                    "status": "open",
                    "created_at": datetime.now(timezone.utc),
                    "applications_count": 0,
                    "bids_count": 0,
                },
            ]

            for job in demo_jobs:
                await db.jobs.insert_one(job)
                logger.info(f"✅ Created job: {job['title']} ({job['type']})")

            logger.info("🎉 Demo data seeded successfully!")
            logger.info("\n📋 Demo Login Credentials:")
            logger.info("   Customer: 9876543210 / password123")
            logger.info("   Worker: 9876543211 / password123")
            logger.info("   Admin: 9876543212 / admin123")
        else:
            logger.info(f"✓ Database already has {user_count} users. Skipping seed.")
    except Exception as e:
        logger.error(f"❌ Error seeding demo data: {e}")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Starting Shidhaan API...")
    await seed_demo_data()


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELS
# =============================================================================


class UserRole(str):
    CUSTOMER = "customer"
    WORKER = "worker"
    ADMIN = "admin"


class JobType(str):
    DAILY = "daily"
    CONTRACTUAL = "contractual"


class JobCategory(str):
    SKILLED = "skilled"
    DAILY_WAGE = "daily_wage"


class JobStatus(str):
    DRAFT = "draft"
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class ApplicationStatus(str):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PaymentMethod(str):
    UPI = "upi"
    CARD = "card"
    COD = "cod"
    ESCROW = "escrow_future"


class PaymentStatus(str):
    INITIATED = "initiated"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    RECORDED_COD = "recorded_cod"


class MessageType(str):
    TEXT = "text"
    SYSTEM = "system"
    LOCATION = "location"


class NotificationType(str):
    JOB_APPLICATION = "job_application"
    JOB_ASSIGNED = "job_assigned"
    BID_RECEIVED = "bid_received"
    PAYMENT_RECEIVED = "payment_received"
    JOB_COMPLETED = "job_completed"
    MESSAGE_RECEIVED = "message_received"


# User Models
class Location(BaseModel):
    lat: float
    lng: float
    address: str


class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    languages: List[str] = ["en"]
    location: Optional[Location] = None


class UserCreate(UserBase):
    password: str
    role: str


class UserLogin(BaseModel):
    phone: str
    password: str


class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    rating_avg: float = 0.0
    reviews_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


# Worker Profile Models
class WorkerProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    skills: List[str] = []
    experience_years: int = 0
    certifications: List[str] = []
    preferred_locations: List[Location] = []
    completed_jobs: int = 0
    cancelled_jobs: int = 0
    trust_score: float = 50.0  # AI readiness placeholder
    service_radius_km: int = 10  # New field for location-based search


class WorkerProfileCreate(BaseModel):
    skills: List[str] = []
    experience_years: int = 0
    certifications: List[str] = []
    preferred_locations: List[Location] = []
    service_radius_km: int = 10


# Job Models
class TimeWindow(BaseModel):
    start: str  # e.g., "09:00"
    end: str  # e.g., "17:00"


class JobBase(BaseModel):
    title: str
    description: str
    category: str
    photos: List[str] = []
    location: Location
    preferred_time_window: Optional[TimeWindow] = None
    budget_amount: float
    is_budget_negotiable: bool = False


class JobCreate(JobBase):
    type: str  # daily or contractual


class Job(JobBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    type: str
    status: str = JobStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applications_count: int = 0
    bids_count: int = 0


# Application Models (for Daily jobs)
class ApplicationBase(BaseModel):
    message: str = ""


class ApplicationCreate(ApplicationBase):
    job_id: str


class Application(ApplicationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    worker_id: str
    status: str = ApplicationStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Bid Models (for Contractual jobs)
class BidBase(BaseModel):
    bid_amount: float
    visiting_charge: float = 0.0
    message: str = ""


class BidCreate(BidBase):
    job_id: str


class Bid(BidBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    worker_id: str
    status: str = ApplicationStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Assignment Models
class Assignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    worker_id: str
    accepted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_amount: float
    payment_method: str = PaymentMethod.COD
    status: str = JobStatus.ASSIGNED


# Review Models
class ReviewBase(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str = ""


class ReviewCreate(ReviewBase):
    job_id: str
    reviewee_user_id: str


class Review(ReviewBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    reviewer_user_id: str
    reviewee_user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Payment Models
class PaymentCreate(BaseModel):
    job_id: str
    amount: float
    method: str = PaymentMethod.COD


class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    payer_id: str
    payee_id: str
    method: str
    amount: float
    status: str = PaymentStatus.INITIATED
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Chat Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    sender_user_id: str
    receiver_user_id: str
    message_type: str = MessageType.TEXT
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessageCreate(BaseModel):
    content: str
    message_type: str = MessageType.TEXT


# Notification Models
class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    title: str
    message: str
    data: Dict[str, Any] = {}
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Search Models
class JobSearchFilters(BaseModel):
    search_term: Optional[str] = None
    job_type: Optional[str] = None
    category: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    location: Optional[Location] = None
    radius_km: Optional[int] = None
    skills: List[str] = []
    sort_by: str = "recent"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) * math.sin(dlng / 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


def mask_phone_number(phone: str) -> str:
    """Mask phone number for privacy"""
    if len(phone) >= 4:
        return phone[:2] + "****" + phone[-2:]
    return "****"


async def create_notification(
    user_id: str, notification_type: str, title: str, message: str, data: Dict = None
):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        data=data or {},
    )
    await db.notifications.insert_one(notification.model_dump())
    return notification


# =============================================================================
# AUTH UTILITIES
# =============================================================================


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_doc = await db.users.find_one({"id": user_id})
    if user_doc is None:
        raise credentials_exception
    return User(**user_doc)


def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}",
            )
        return current_user

    return role_checker


# =============================================================================
# AUTH ROUTES
# =============================================================================


@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"phone": user_data.phone})
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this phone number already exists"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.model_dump()
    user_dict["password_hash"] = hashed_password
    del user_dict["password"]

    user = User(**user_dict)
    user_doc = user.model_dump()
    user_doc["password_hash"] = hashed_password

    await db.users.insert_one(user_doc)

    # Create worker profile if role is worker
    if user.role == UserRole.WORKER:
        worker_profile = WorkerProfile(user_id=user.id)
        await db.worker_profiles.insert_one(worker_profile.model_dump())

    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer", user=user)


@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"phone": credentials.phone})
    if not user_doc or not verify_password(
        credentials.password, user_doc.get("password_hash")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User(**user_doc)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer", user=user)


@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


# =============================================================================
# USER ROUTES
# =============================================================================


@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_doc)


# =============================================================================
# WORKER PROFILE ROUTES
# =============================================================================


@api_router.get("/workers/profile", response_model=WorkerProfile)
async def get_worker_profile(
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    profile_doc = await db.worker_profiles.find_one({"user_id": current_user.id})
    if not profile_doc:
        # Create default profile if doesn't exist
        profile = WorkerProfile(user_id=current_user.id)
        await db.worker_profiles.insert_one(profile.model_dump())
        return profile
    return WorkerProfile(**profile_doc)


@api_router.put("/workers/profile", response_model=WorkerProfile)
async def update_worker_profile(
    profile_data: WorkerProfileCreate,
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    update_data = profile_data.model_dump()

    await db.worker_profiles.update_one(
        {"user_id": current_user.id}, {"$set": update_data}, upsert=True
    )

    profile_doc = await db.worker_profiles.find_one({"user_id": current_user.id})
    return WorkerProfile(**profile_doc)


# =============================================================================
# JOB ROUTES WITH ADVANCED SEARCH
# =============================================================================


@api_router.post("/jobs", response_model=Job)
async def create_job(
    job_data: JobCreate, current_user: User = Depends(require_role(UserRole.CUSTOMER))
):
    job_dict = job_data.model_dump()
    job_dict["customer_id"] = current_user.id
    job = Job(**job_dict)

    await db.jobs.insert_one(job.model_dump())

    # Create notification for nearby workers (if location-based search is enabled)
    await notify_nearby_workers(job)

    return job


async def notify_nearby_workers(job: Job):
    """Notify workers within service radius about new job"""
    if not job.location:
        return

    # Find workers within radius who have matching skills
    job_skills = []
    if job.category == "skilled":
        # Extract potential skills from job title/description
        job_text = f"{job.title} {job.description}".lower()
        common_skills = [
            "plumbing",
            "electrical",
            "carpentry",
            "painting",
            "cleaning",
            "repair",
        ]
        job_skills = [skill for skill in common_skills if skill in job_text]

    # Query workers within radius
    workers = await db.worker_profiles.find().to_list(length=None)

    for worker_profile in workers:
        # Check if worker has matching skills or is in service radius
        has_matching_skills = any(
            skill.lower() in [s.lower() for s in worker_profile.get("skills", [])]
            for skill in job_skills
        )

        # Check distance for workers with preferred locations
        within_radius = False
        for location in worker_profile.get("preferred_locations", []):
            distance = calculate_distance(
                job.location.lat, job.location.lng, location["lat"], location["lng"]
            )
            if distance <= worker_profile.get("service_radius_km", 10):
                within_radius = True
                break

        if has_matching_skills or within_radius:
            await create_notification(
                worker_profile["user_id"],
                NotificationType.JOB_APPLICATION,
                "New Job Available",
                f"A new {job.type} job '{job.title}' is available in your area",
                {"job_id": job.id, "job_type": job.type},
            )


@api_router.post("/jobs/search", response_model=List[Job])
async def search_jobs(
    filters: JobSearchFilters, current_user: User = Depends(get_current_user)
):
    # Build MongoDB query
    query = {"status": JobStatus.OPEN}

    if filters.search_term:
        query["$or"] = [
            {"title": {"$regex": filters.search_term, "$options": "i"}},
            {"description": {"$regex": filters.search_term, "$options": "i"}},
        ]

    if filters.job_type:
        query["type"] = filters.job_type

    if filters.category:
        query["category"] = filters.category

    if filters.min_budget:
        query["budget_amount"] = {"$gte": filters.min_budget}

    if filters.max_budget:
        if "budget_amount" in query:
            query["budget_amount"]["$lte"] = filters.max_budget
        else:
            query["budget_amount"] = {"$lte": filters.max_budget}

    # Execute query
    jobs = await db.jobs.find(query).to_list(length=None)
    job_list = [Job(**job) for job in jobs]

    # Apply location-based filtering
    if filters.location and filters.radius_km:
        filtered_jobs = []
        for job in job_list:
            if job.location:
                distance = calculate_distance(
                    filters.location.lat,
                    filters.location.lng,
                    job.location.lat,
                    job.location.lng,
                )
                if distance <= filters.radius_km:
                    filtered_jobs.append(job)
        job_list = filtered_jobs

    # Apply skills-based filtering for workers
    if current_user.role == UserRole.WORKER and filters.skills:
        # Get worker profile to match skills
        worker_profile = await db.worker_profiles.find_one({"user_id": current_user.id})
        if worker_profile:
            worker_skills = [
                skill.lower() for skill in worker_profile.get("skills", [])
            ]
            skills_matched_jobs = []

            for job in job_list:
                job_text = f"{job.title} {job.description}".lower()
                if any(skill in job_text for skill in worker_skills):
                    skills_matched_jobs.append(job)

            job_list = skills_matched_jobs

    # Apply sorting
    if filters.sort_by == "budget_high":
        job_list.sort(key=lambda x: x.budget_amount, reverse=True)
    elif filters.sort_by == "budget_low":
        job_list.sort(key=lambda x: x.budget_amount)
    elif filters.sort_by == "distance" and filters.location:
        job_list.sort(
            key=lambda x: calculate_distance(
                filters.location.lat,
                filters.location.lng,
                x.location.lat if x.location else 0,
                x.location.lng if x.location else 0,
            )
        )
    else:  # recent
        job_list.sort(key=lambda x: x.created_at, reverse=True)

    return job_list


@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(
    status: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
):
    filter_dict = {}
    if status:
        filter_dict["status"] = status
    if type:
        filter_dict["type"] = type
    if category:
        filter_dict["category"] = category

    jobs = await db.jobs.find(filter_dict).skip(skip).limit(limit).to_list(length=None)
    return [Job(**job) for job in jobs]


@api_router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**job_doc)


@api_router.put("/jobs/{job_id}/publish")
async def publish_job(job_id: str, current_user: User = Depends(get_current_user)):
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.jobs.update_one({"id": job_id}, {"$set": {"status": JobStatus.OPEN}})

    # Notify nearby workers
    job = Job(**job_doc)
    await notify_nearby_workers(job)

    return {"message": "Job published successfully"}


# =============================================================================
# APPLICATION ROUTES (Daily Jobs)
# =============================================================================


@api_router.post("/jobs/{job_id}/apply", response_model=Application)
async def apply_to_job(
    job_id: str,
    application_data: ApplicationBase,
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    # Check if job exists and is daily type
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_doc["type"] != JobType.DAILY:
        raise HTTPException(status_code=400, detail="Can only apply to daily jobs")

    if job_doc["status"] != JobStatus.OPEN:
        raise HTTPException(status_code=400, detail="Job is not accepting applications")

    # Check if already applied
    existing_app = await db.applications.find_one(
        {"job_id": job_id, "worker_id": current_user.id}
    )
    if existing_app:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    # Create application
    app_dict = application_data.model_dump()
    app_dict["job_id"] = job_id
    app_dict["worker_id"] = current_user.id
    application = Application(**app_dict)

    await db.applications.insert_one(application.model_dump())

    # Update job applications count
    await db.jobs.update_one({"id": job_id}, {"$inc": {"applications_count": 1}})

    # Notify customer
    await create_notification(
        job_doc["customer_id"],
        NotificationType.JOB_APPLICATION,
        "New Application Received",
        f"A worker has applied for your job '{job_doc['title']}'",
        {"job_id": job_id, "application_id": application.id},
    )

    return application


@api_router.get("/jobs/{job_id}/applications", response_model=List[Application])
async def get_job_applications(
    job_id: str, current_user: User = Depends(get_current_user)
):
    # Verify job ownership or admin access
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if (
        job_doc["customer_id"] != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    applications = await db.applications.find({"job_id": job_id}).to_list(length=None)
    return [Application(**app) for app in applications]


# =============================================================================
# BID ROUTES (Contractual Jobs)
# =============================================================================


@api_router.post("/jobs/{job_id}/bid", response_model=Bid)
async def place_bid(
    job_id: str,
    bid_data: BidBase,
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    # Check if job exists and is contractual type
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_doc["type"] != JobType.CONTRACTUAL:
        raise HTTPException(status_code=400, detail="Can only bid on contractual jobs")

    if job_doc["status"] != JobStatus.OPEN:
        raise HTTPException(status_code=400, detail="Job is not accepting bids")

    # Update existing bid or create new one
    bid_dict = bid_data.model_dump()
    bid_dict["job_id"] = job_id
    bid_dict["worker_id"] = current_user.id

    existing_bid = await db.bids.find_one(
        {"job_id": job_id, "worker_id": current_user.id}
    )

    if existing_bid:
        # Update existing bid
        await db.bids.update_one(
            {"job_id": job_id, "worker_id": current_user.id}, {"$set": bid_dict}
        )
        bid_dict["id"] = existing_bid["id"]
        bid_dict["created_at"] = existing_bid["created_at"]
    else:
        # Create new bid
        bid = Bid(**bid_dict)
        await db.bids.insert_one(bid.model_dump())

        # Update job bids count
        await db.jobs.update_one({"id": job_id}, {"$inc": {"bids_count": 1}})

        # Notify customer
        await create_notification(
            job_doc["customer_id"],
            NotificationType.BID_RECEIVED,
            "New Bid Received",
            f"A worker has placed a bid of ₹{bid_data.bid_amount} for your job '{job_doc['title']}'",
            {"job_id": job_id, "bid_id": bid.id, "amount": bid_data.bid_amount},
        )

        return bid

    return Bid(**bid_dict)


@api_router.get("/jobs/{job_id}/bids", response_model=List[Bid])
async def get_job_bids(job_id: str, current_user: User = Depends(get_current_user)):
    # Verify job ownership or admin access
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if (
        job_doc["customer_id"] != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    bids = await db.bids.find({"job_id": job_id}).to_list(length=None)
    return [Bid(**bid) for bid in bids]


# =============================================================================
# ASSIGNMENT ROUTES
# =============================================================================


@api_router.post("/jobs/{job_id}/assign")
async def assign_job(
    job_id: str,
    worker_id: str,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    # Verify job ownership
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc or job_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_doc["status"] != JobStatus.OPEN:
        raise HTTPException(
            status_code=400, detail="Job is not available for assignment"
        )

    # Determine final amount based on job type
    if job_doc["type"] == JobType.DAILY:
        # For daily jobs, use the fixed budget
        final_amount = job_doc["budget_amount"]

        # Verify application exists
        app_doc = await db.applications.find_one(
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "status": ApplicationStatus.PENDING,
            }
        )
        if not app_doc:
            raise HTTPException(status_code=404, detail="Application not found")

        # Update application status
        await db.applications.update_one(
            {"job_id": job_id, "worker_id": worker_id},
            {"$set": {"status": ApplicationStatus.ACCEPTED}},
        )

        # Reject other applications
        await db.applications.update_many(
            {"job_id": job_id, "worker_id": {"$ne": worker_id}},
            {"$set": {"status": ApplicationStatus.REJECTED}},
        )

    else:  # CONTRACTUAL
        # For contractual jobs, use the bid amount
        bid_doc = await db.bids.find_one(
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "status": ApplicationStatus.PENDING,
            }
        )
        if not bid_doc:
            raise HTTPException(status_code=404, detail="Bid not found")

        final_amount = bid_doc["bid_amount"] + bid_doc.get("visiting_charge", 0)

        # Update bid status
        await db.bids.update_one(
            {"job_id": job_id, "worker_id": worker_id},
            {"$set": {"status": ApplicationStatus.ACCEPTED}},
        )

        # Reject other bids
        await db.bids.update_many(
            {"job_id": job_id, "worker_id": {"$ne": worker_id}},
            {"$set": {"status": ApplicationStatus.REJECTED}},
        )

    # Create assignment
    assignment = Assignment(
        job_id=job_id, worker_id=worker_id, final_amount=final_amount
    )

    await db.assignments.insert_one(assignment.model_dump())

    # Update job status
    await db.jobs.update_one({"id": job_id}, {"$set": {"status": JobStatus.ASSIGNED}})

    # Notify worker
    await create_notification(
        worker_id,
        NotificationType.JOB_ASSIGNED,
        "Job Assigned to You!",
        f"You have been selected for the job '{job_doc['title']}' - Amount: ₹{final_amount}",
        {"job_id": job_id, "assignment_id": assignment.id, "amount": final_amount},
    )

    return {"message": "Job assigned successfully", "assignment_id": assignment.id}


# =============================================================================
# PAYMENT ROUTES
# =============================================================================


@api_router.post("/payments/create-order")
async def create_payment_order(
    payment_data: PaymentCreate, current_user: User = Depends(get_current_user)
):
    # Verify job assignment exists
    assignment = await db.assignments.find_one({"job_id": payment_data.job_id})
    if not assignment:
        raise HTTPException(status_code=404, detail="Job assignment not found")

    job_doc = await db.jobs.find_one({"id": payment_data.job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify user is customer for this job
    if job_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create payment record
    payment = Payment(
        job_id=payment_data.job_id,
        payer_id=current_user.id,
        payee_id=assignment["worker_id"],
        method=payment_data.method,
        amount=payment_data.amount,
    )

    if payment_data.method == PaymentMethod.COD:
        # For COD, mark as recorded
        payment.status = PaymentStatus.RECORDED_COD
        await db.payments.insert_one(payment.model_dump())

        # Update job status
        await db.jobs.update_one(
            {"id": payment_data.job_id}, {"$set": {"status": JobStatus.COMPLETED}}
        )

        # Notify worker
        await create_notification(
            assignment["worker_id"],
            NotificationType.PAYMENT_RECEIVED,
            "Payment Recorded - COD",
            f"Cash payment of ₹{payment_data.amount} has been recorded for job '{job_doc['title']}'",
            {
                "job_id": payment_data.job_id,
                "payment_id": payment.id,
                "amount": payment_data.amount,
            },
        )

        return {
            "payment_id": payment.id,
            "status": "cod_recorded",
            "message": "COD payment recorded successfully",
        }

    elif payment_data.method in [PaymentMethod.UPI, PaymentMethod.CARD]:
        # For online payments, create Razorpay order
        if not razorpay_client:
            raise HTTPException(
                status_code=500, detail="Payment gateway not configured"
            )

        try:
            # Create Razorpay order
            order_data = {
                "amount": int(payment_data.amount * 100),  # Convert to paise
                "currency": "INR",
                "payment_capture": 1,
                "notes": {
                    "job_id": payment_data.job_id,
                    "customer_id": current_user.id,
                    "worker_id": assignment["worker_id"],
                },
            }

            razorpay_order = razorpay_client.order.create(order_data)

            # Update payment record with Razorpay order ID
            payment.razorpay_order_id = razorpay_order["id"]
            await db.payments.insert_one(payment.model_dump())

            return {
                "payment_id": payment.id,
                "razorpay_order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
                "key_id": RAZORPAY_KEY_ID,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create payment order: {str(e)}"
            )

    else:
        raise HTTPException(status_code=400, detail="Unsupported payment method")


@api_router.post("/payments/verify")
async def verify_payment(
    payment_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    current_user: User = Depends(get_current_user),
):
    # Find payment record
    payment_doc = await db.payments.find_one({"id": payment_id})
    if not payment_doc:
        raise HTTPException(status_code=404, detail="Payment not found")

    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")

    try:
        # Verify payment signature
        params_dict = {
            "razorpay_order_id": payment_doc["razorpay_order_id"],
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        razorpay_client.utility.verify_payment_signature(params_dict)

        # Update payment status
        await db.payments.update_one(
            {"id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.SUCCEEDED,
                    "razorpay_payment_id": razorpay_payment_id,
                }
            },
        )

        # Update job status to completed
        await db.jobs.update_one(
            {"id": payment_doc["job_id"]}, {"$set": {"status": JobStatus.COMPLETED}}
        )

        # Notify worker
        job_doc = await db.jobs.find_one({"id": payment_doc["job_id"]})
        await create_notification(
            payment_doc["payee_id"],
            NotificationType.PAYMENT_RECEIVED,
            "Payment Received!",
            f"You have received ₹{payment_doc['amount']} for job '{job_doc['title']}'",
            {
                "job_id": payment_doc["job_id"],
                "payment_id": payment_id,
                "amount": payment_doc["amount"],
            },
        )

        return {"status": "success", "message": "Payment verified successfully"}

    except Exception as e:
        # Update payment status to failed
        await db.payments.update_one(
            {"id": payment_id}, {"$set": {"status": PaymentStatus.FAILED}}
        )

        raise HTTPException(
            status_code=400, detail=f"Payment verification failed: {str(e)}"
        )


# =============================================================================
# CHAT ROUTES
# =============================================================================


@api_router.get("/jobs/{job_id}/messages", response_model=List[ChatMessage])
async def get_job_messages(job_id: str, current_user: User = Depends(get_current_user)):
    # Verify user is involved in this job
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    assignment = await db.assignments.find_one({"job_id": job_id})

    # Check if user is customer, assigned worker, or admin
    allowed_users = [job_doc["customer_id"]]
    if assignment:
        allowed_users.append(assignment["worker_id"])

    if current_user.id not in allowed_users and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get messages
    messages = (
        await db.chat_messages.find({"job_id": job_id})
        .sort("created_at", 1)
        .to_list(length=None)
    )

    # Mark messages as read for current user
    await db.chat_messages.update_many(
        {"job_id": job_id, "receiver_user_id": current_user.id},
        {"$set": {"is_read": True}},
    )

    result = []
    for msg in messages:
        chat_msg = ChatMessage(**msg)
        # Mask phone numbers in messages
        if chat_msg.message_type == MessageType.TEXT:
            # Replace phone numbers with masked versions
            import re

            phone_pattern = r"\b\d{10,12}\b"
            chat_msg.content = re.sub(
                phone_pattern, lambda m: mask_phone_number(m.group()), chat_msg.content
            )
        result.append(chat_msg)

    return result


@api_router.post("/jobs/{job_id}/messages")
async def send_message(
    job_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
):
    # Verify user is involved in this job
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    assignment = await db.assignments.find_one({"job_id": job_id})

    # Determine receiver
    receiver_id = None
    if current_user.id == job_doc["customer_id"] and assignment:
        receiver_id = assignment["worker_id"]
    elif assignment and current_user.id == assignment["worker_id"]:
        receiver_id = job_doc["customer_id"]
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create message
    message = ChatMessage(
        job_id=job_id,
        sender_user_id=current_user.id,
        receiver_user_id=receiver_id,
        content=message_data.content,
        message_type=message_data.message_type,
    )

    await db.chat_messages.insert_one(message.model_dump())

    # Notify receiver
    await create_notification(
        receiver_id,
        NotificationType.MESSAGE_RECEIVED,
        "New Message",
        f"You have a new message about job '{job_doc['title']}'",
        {"job_id": job_id, "message_id": message.id},
    )

    return {"message_id": message.id, "status": "sent"}


# =============================================================================
# REVIEW ROUTES
# =============================================================================


@api_router.post("/jobs/{job_id}/review", response_model=Review)
async def create_review(
    job_id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
):
    # Verify job is completed
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_doc["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only review completed jobs")

    # Verify user is involved in this job
    assignment = await db.assignments.find_one({"job_id": job_id})
    if not assignment:
        raise HTTPException(status_code=404, detail="Job assignment not found")

    allowed_users = [job_doc["customer_id"], assignment["worker_id"]]
    if current_user.id not in allowed_users:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if already reviewed
    existing_review = await db.reviews.find_one(
        {
            "job_id": job_id,
            "reviewer_user_id": current_user.id,
            "reviewee_user_id": review_data.reviewee_user_id,
        }
    )

    if existing_review:
        raise HTTPException(
            status_code=400, detail="You have already reviewed this job"
        )

    # Create review
    review = Review(
        job_id=job_id,
        reviewer_user_id=current_user.id,
        reviewee_user_id=review_data.reviewee_user_id,
        stars=review_data.stars,
        comment=review_data.comment,
    )

    await db.reviews.insert_one(review.model_dump())

    # Update user's rating
    user_reviews = await db.reviews.find(
        {"reviewee_user_id": review_data.reviewee_user_id}
    ).to_list(length=None)
    avg_rating = sum(r["stars"] for r in user_reviews) / len(user_reviews)

    await db.users.update_one(
        {"id": review_data.reviewee_user_id},
        {"$set": {"rating_avg": avg_rating, "reviews_count": len(user_reviews)}},
    )

    # Update worker trust score if reviewee is worker
    if current_user.id == job_doc["customer_id"]:  # Customer reviewing worker
        # Increase trust score based on rating
        trust_increase = (review_data.stars - 3) * 2  # -4 to +4 points
        await db.worker_profiles.update_one(
            {"user_id": review_data.reviewee_user_id},
            {"$inc": {"trust_score": trust_increase}},
        )

    return review


@api_router.get("/users/{user_id}/reviews", response_model=List[Review])
async def get_user_reviews(user_id: str, limit: int = 10, skip: int = 0):
    reviews = (
        await db.reviews.find({"reviewee_user_id": user_id})
        .skip(skip)
        .limit(limit)
        .to_list(length=None)
    )
    return [Review(**review) for review in reviews]


# =============================================================================
# NOTIFICATION ROUTES
# =============================================================================


@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    skip: int = 0,
    unread_only: bool = False,
):
    query = {"user_id": current_user.id}
    if unread_only:
        query["is_read"] = False

    notifications = (
        await db.notifications.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(length=None)
    )
    return [Notification(**notif) for notif in notifications]


@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str, current_user: User = Depends(get_current_user)
):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id}, {"$set": {"is_read": True}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"status": "marked_as_read"}


@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    await db.notifications.update_many(
        {"user_id": current_user.id, "is_read": False}, {"$set": {"is_read": True}}
    )

    return {"status": "all_notifications_marked_as_read"}


# =============================================================================
# BASIC ROUTES
# =============================================================================


@api_router.get("/")
async def root():
    return {"message": "Shidhaan API v1.0.0 - Blue Collar Marketplace (Phase 4)"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}


@api_router.get("/config")
async def get_config(current_user: User = Depends(get_current_user)):
    """Get frontend configuration"""
    return {
        "payment_methods": ["cod", "upi", "card"],
        "razorpay_key_id": RAZORPAY_KEY_ID if razorpay_client else None,
        "maps_enabled": True,  # Placeholder for Google Maps
        "chat_enabled": True,
        "notifications_enabled": True,
    }


# Include the router
app.include_router(api_router)

# =============================================================================
# STATIC FILE SERVING (for React frontend)
# =============================================================================

# Check if static directory exists (for production with built frontend)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    # Serve React app for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Don't serve index.html for API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve the requested file (handles static/js/*, static/css/*, etc.)
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Otherwise serve index.html for client-side routing
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Not found")


# =============================================================================
# ADMIN ROUTES
# =============================================================================


# Admin role validation
def require_admin_role():
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
        return current_user

    return role_checker


@api_router.get("/admin/dashboard")
async def get_admin_dashboard(current_user: User = Depends(require_admin_role())):
    """Get comprehensive admin dashboard statistics"""

    # Get user counts
    total_users = await db.users.count_documents({})
    total_customers = await db.users.count_documents({"role": "customer"})
    total_workers = await db.users.count_documents({"role": "worker"})

    # Get job counts
    active_jobs = await db.jobs.count_documents(
        {"status": {"$in": ["open", "assigned", "in_progress"]}}
    )
    completed_jobs = await db.jobs.count_documents({"status": "completed"})

    # Get dispute counts (mock data since collection may not exist)
    pending_disputes = 0
    pending_kyc = 0

    # Get revenue data
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    month_start = today.replace(day=1)

    # Calculate revenue (from payments collection)
    revenue_today = 0.0
    revenue_month = 0.0

    try:
        revenue_today_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": today},
                    "status": {"$in": ["succeeded", "recorded_cod"]},
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]

        revenue_month_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": month_start},
                    "status": {"$in": ["succeeded", "recorded_cod"]},
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]

        revenue_today_result = await db.payments.aggregate(
            revenue_today_pipeline
        ).to_list(1)
        revenue_month_result = await db.payments.aggregate(
            revenue_month_pipeline
        ).to_list(1)

        revenue_today = (
            revenue_today_result[0]["total"] if revenue_today_result else 0.0
        )
        revenue_month = (
            revenue_month_result[0]["total"] if revenue_month_result else 0.0
        )
    except Exception as e:
        logger.warning(f"Revenue calculation failed: {e}")

    # Get top performing workers
    top_workers = []
    try:
        top_workers_pipeline = [
            {"$match": {"role": "worker"}},
            {"$sort": {"rating_avg": -1, "reviews_count": -1}},
            {"$limit": 5},
            {"$project": {"_id": 0, "name": 1, "rating_avg": 1, "reviews_count": 1}},
        ]

        top_workers = await db.users.aggregate(top_workers_pipeline).to_list(5)
    except Exception as e:
        logger.warning(f"Top workers calculation failed: {e}")

    # Get recent activities (mock data)
    recent_activities = [
        {
            "type": "job_posted",
            "description": "New plumbing job posted",
            "time": "2 hours ago",
        },
        {
            "type": "worker_joined",
            "description": "New worker registered",
            "time": "4 hours ago",
        },
        {
            "type": "payment_completed",
            "description": f"Payment of ₹{revenue_today} completed",
            "time": "6 hours ago",
        },
    ]

    return {
        "total_users": total_users,
        "total_customers": total_customers,
        "total_workers": total_workers,
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,
        "pending_disputes": pending_disputes,
        "pending_kyc": pending_kyc,
        "total_revenue_today": revenue_today,
        "total_revenue_month": revenue_month,
        "top_performing_workers": top_workers,
        "recent_activities": recent_activities,
    }


@api_router.get("/admin/users")
async def get_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, le=100),
    skip: int = 0,
    current_user: User = Depends(require_admin_role()),
):
    """Get all users with filtering and search"""
    filter_dict = {}

    if role:
        filter_dict["role"] = role

    if search:
        filter_dict["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    users = await db.users.find(filter_dict).skip(skip).limit(limit).to_list(limit)
    return [
        User(**{k: v for k, v in user.items() if k != "password_hash"})
        for user in users
    ]


@api_router.get("/admin/users/{user_id}/activity")
async def get_user_activity(
    user_id: str, current_user: User = Depends(require_admin_role())
):
    """Get user activity timeline"""

    # Get user info
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's jobs
    jobs = []
    if user["role"] == "customer":
        jobs = (
            await db.jobs.find({"customer_id": user_id})
            .sort("created_at", -1)
            .limit(10)
            .to_list(10)
        )

    # Get applications/bids
    applications = (
        await db.applications.find({"worker_id": user_id})
        .sort("created_at", -1)
        .limit(10)
        .to_list(10)
    )
    bids = (
        await db.bids.find({"worker_id": user_id})
        .sort("created_at", -1)
        .limit(10)
        .to_list(10)
    )

    # Get payments
    payments = (
        await db.payments.find({"$or": [{"payer_id": user_id}, {"payee_id": user_id}]})
        .sort("created_at", -1)
        .limit(10)
        .to_list(10)
    )

    # Get reviews
    reviews_given = (
        await db.reviews.find({"reviewer_user_id": user_id})
        .sort("created_at", -1)
        .limit(5)
        .to_list(5)
    )
    reviews_received = (
        await db.reviews.find({"reviewee_user_id": user_id})
        .sort("created_at", -1)
        .limit(5)
        .to_list(5)
    )

    return {
        "user": {k: v for k, v in user.items() if k not in ["password_hash", "_id"]},
        "jobs_posted": len(jobs) if user["role"] == "customer" else 0,
        "applications_sent": len(applications),
        "bids_placed": len(bids),
        "payments_made": len([p for p in payments if p["payer_id"] == user_id]),
        "payments_received": len([p for p in payments if p["payee_id"] == user_id]),
        "reviews_given": len(reviews_given),
        "reviews_received": len(reviews_received),
        "recent_jobs": [
            {k: v for k, v in job.items() if k != "_id"} for job in jobs[:5]
        ],
        "recent_applications": [
            {k: v for k, v in app.items() if k != "_id"} for app in applications[:5]
        ],
        "recent_reviews": [
            {k: v for k, v in review.items() if k != "_id"}
            for review in reviews_received[:5]
        ],
    }


@api_router.post("/admin/users/{user_id}/strike")
async def issue_user_strike(
    user_id: str, strike_data: dict, current_user: User = Depends(require_admin_role())
):
    """Issue a strike/warning to a user"""

    # Create strike record (simplified)
    strike = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "reason": strike_data["reason"],
        "description": strike_data["description"],
        "severity": strike_data.get("severity", "medium"),
        "issued_by": current_user.id,
        "issued_at": datetime.now(timezone.utc),
        "is_active": True,
    }

    # Insert strike (create collection if doesn't exist)
    await db.user_strikes.insert_one(strike)

    # Count strikes
    strike_count = await db.user_strikes.count_documents(
        {"user_id": user_id, "is_active": True}
    )

    return {"message": "Strike issued successfully", "total_strikes": strike_count}


@api_router.get("/admin/kyc/pending")
async def get_pending_kyc(
    limit: int = 20, skip: int = 0, current_user: User = Depends(require_admin_role())
):
    """Get all pending KYC verifications"""

    # Return empty list for now (KYC system not fully implemented)
    return []


@api_router.get("/admin/jobs/moderation")
async def get_jobs_for_moderation(
    status: str = "pending",
    limit: int = 20,
    skip: int = 0,
    current_user: User = Depends(require_admin_role()),
):
    """Get jobs that need content moderation"""

    # Return empty list for now (moderation system not fully implemented)
    return []


@api_router.get("/admin/disputes")
async def get_disputes(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: User = Depends(require_admin_role()),
):
    """Get disputes with filtering"""

    # Return empty list for now (dispute system not fully implemented)
    return []


@api_router.get("/admin/analytics/revenue")
async def get_revenue_analytics(
    period: str = "month", current_user: User = Depends(require_admin_role())
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
        start_date = now - timedelta(days=365 * 3)
        group_by = {"$dateToString": {"format": "%Y", "date": "$created_at"}}

    try:
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date},
                    "status": {"$in": ["succeeded", "recorded_cod"]},
                }
            },
            {
                "$group": {
                    "_id": group_by,
                    "total_revenue": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await db.payments.aggregate(pipeline).to_list(100)

        return {
            "period": period,
            "data": results,
            "total_revenue": sum(r["total_revenue"] for r in results),
            "total_transactions": sum(r["transaction_count"] for r in results),
        }
    except Exception as e:
        logger.warning(f"Revenue analytics failed: {e}")
        return {
            "period": period,
            "data": [],
            "total_revenue": 0,
            "total_transactions": 0,
        }


@api_router.get("/admin/analytics/jobs")
async def get_job_analytics(current_user: User = Depends(require_admin_role())):
    """Get job-related analytics"""

    # Job completion rates
    total_jobs = await db.jobs.count_documents({})
    completed_jobs = await db.jobs.count_documents({"status": "completed"})
    completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

    # Average job values by category
    try:
        category_pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "avg_amount": {"$avg": "$budget_amount"},
                    "job_count": {"$sum": 1},
                }
            },
            {"$sort": {"job_count": -1}},
        ]

        category_stats = await db.jobs.aggregate(category_pipeline).to_list(100)
    except Exception as e:
        logger.warning(f"Category stats failed: {e}")
        category_stats = []

    # Jobs by status
    try:
        status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]

        status_stats = await db.jobs.aggregate(status_pipeline).to_list(100)
    except Exception as e:
        logger.warning(f"Status stats failed: {e}")
        status_stats = []

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "completion_rate": round(completion_rate, 2),
        "category_stats": category_stats,
        "status_distribution": status_stats,
    }


@api_router.get("/admin/config")
async def get_platform_config(
    category: Optional[str] = None, current_user: User = Depends(require_admin_role())
):
    """Get platform configuration"""

    # Return mock configuration data
    configs = [
        {
            "key": "max_job_budget",
            "value": 100000,
            "category": "job",
            "description": "Maximum job budget allowed",
        },
        {
            "key": "commission_rate",
            "value": 0.05,
            "category": "payment",
            "description": "Platform commission rate",
        },
        {
            "key": "auto_assign_timeout",
            "value": 24,
            "category": "job",
            "description": "Hours before auto-assignment",
        },
    ]

    if category:
        configs = [c for c in configs if c["category"] == category]

    return configs


@api_router.post("/admin/announcements")
async def create_announcement(
    announcement_data: dict, current_user: User = Depends(require_admin_role())
):
    """Create platform-wide announcement"""

    announcement = {
        "id": str(uuid.uuid4()),
        "title": announcement_data["title"],
        "message": announcement_data["message"],
        "target_audience": announcement_data.get("target_audience", "all"),
        "target_user_ids": announcement_data.get("target_user_ids", []),
        "announcement_type": announcement_data.get("type", "info"),
        "priority": announcement_data.get("priority", "normal"),
        "start_date": datetime.fromisoformat(announcement_data["start_date"]),
        "end_date": (
            datetime.fromisoformat(announcement_data["end_date"])
            if announcement_data.get("end_date")
            else None
        ),
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc),
    }

    # Insert announcement
    await db.announcements.insert_one(announcement)

    # Get target users
    target_users = []
    if announcement["target_audience"] == "all":
        target_users = await db.users.find({}, {"id": 1}).to_list(1000)
    elif announcement["target_audience"] in ["customers", "workers"]:
        target_users = await db.users.find(
            {"role": announcement["target_audience"][:-1]}, {"id": 1}
        ).to_list(1000)
    elif announcement["target_user_ids"]:
        target_users = [{"id": uid} for uid in announcement["target_user_ids"]]

    # Create notifications (batch insert)
    notifications = []
    for user in target_users:
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "type": "announcement",
            "title": announcement["title"],
            "message": announcement["message"],
            "data": {"announcement_id": announcement["id"]},
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
        }
        notifications.append(notification)

    if notifications:
        await db.notifications.insert_many(notifications)

    return {
        "message": "Announcement created successfully",
        "notification_count": len(notifications),
    }


# Include admin routes
try:
    from admin_routes import admin_router

    app.include_router(admin_router, prefix="/api")
    print("✅ Admin routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Admin routes not available: {e}")
    pass


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
