from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
import secrets
import uuid
import re
import razorpay
import math
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Uploads directory (override with UPLOAD_DIR to point at a persistent volume)
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR") or ROOT_DIR / "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# MongoDB connection
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# Security
# Secrets that have been published in this repository must never be used to sign tokens.
_PUBLISHED_JWT_SECRETS = {
    "",
    "your-secret-key-change-in-production",
    "your-super-secret-jwt-key-change-this-in-production",
}
SECRET_KEY = os.environ.get("JWT_SECRET", "").strip()
if SECRET_KEY in _PUBLISHED_JWT_SECRETS:
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning(
        "JWT_SECRET is not set or uses a published default. Using a random per-process "
        "secret: sessions end on restart and are not shared between instances. "
        "Set JWT_SECRET to a long random value (e.g. `openssl rand -hex 32`)."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
# auto_error=False so a missing token yields 401 (not FastAPI's default 403)
security = HTTPBearer(auto_error=False)

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


async def ensure_indexes():
    """Create the indexes the app relies on for correctness, not just speed."""
    index_specs = [
        ("users", "phone", {"unique": True}),
        ("users", "id", {"unique": True}),
        ("jobs", "id", {"unique": True}),
        ("jobs", "customer_id", {}),
        ("assignments", "job_id", {"unique": True}),
        ("notifications", "user_id", {}),
    ]
    for collection, key, options in index_specs:
        try:
            await db[collection].create_index(key, **options)
        except Exception as e:
            logger.warning(f"Could not create index on {collection}.{key}: {e}")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Starting Shidhaan API...")
    await ensure_indexes()
    await seed_demo_data()


# CORS middleware. Auth uses bearer tokens (not cookies), so credentials are not needed.
cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

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
    NEW_JOB = "new_job"
    JOB_APPLICATION = "job_application"
    JOB_ASSIGNED = "job_assigned"
    BID_RECEIVED = "bid_received"
    PAYMENT_RECEIVED = "payment_received"
    JOB_COMPLETED = "job_completed"
    MESSAGE_RECEIVED = "message_received"


def normalize_phone(raw: str) -> str:
    """Reduce a phone number to its 10 national digits (drops spaces, dashes, +91, leading 0)."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


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

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class UserCreate(BaseModel):
    name: str = Field(max_length=100)
    phone: str
    email: Optional[EmailStr] = None
    languages: List[str] = ["en"]
    location: Optional[Location] = None
    password: str = Field(min_length=6, max_length=72)
    # Admin accounts can only be created by operators, never through self sign-up.
    role: Literal["customer", "worker"]

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value):
        phone = normalize_phone(value)
        if len(phone) != 10:
            raise ValueError("Enter a valid 10-digit phone number")
        return phone

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value):
        # bcrypt only uses the first 72 bytes; reject rather than silently truncate
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long")
        return value


class UserLogin(BaseModel):
    phone: str
    password: str


class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    rating_avg: float = 0.0
    reviews_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PublicUser(BaseModel):
    """User fields that are safe to show to other users (no phone or email)."""

    id: str
    name: str
    role: str
    languages: List[str] = ["en"]
    rating_avg: float = 0.0
    reviews_count: int = 0
    created_at: datetime


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
    experience_years: int = Field(default=0, ge=0, le=80)
    certifications: List[str] = []
    preferred_locations: List[Location] = []
    service_radius_km: int = Field(default=10, ge=1, le=200)


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
    # Strict input validation lives here so existing documents still load through Job.
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    category: Literal["skilled", "daily_wage"]
    budget_amount: float = Field(gt=0, le=10_000_000)
    photos: List[str] = Field(default_factory=list, max_length=10)
    type: Literal["daily", "contractual"]

    @field_validator("photos")
    @classmethod
    def photos_are_uploads(cls, value):
        for url in value:
            if not isinstance(url, str) or not url.startswith("/uploads/"):
                raise ValueError("Photos must be uploaded through /api/upload")
        return value


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


class WorkerInfo(BaseModel):
    name: str
    rating_avg: float = 0.0
    reviews_count: int = 0


class ApplicationWithWorker(Application):
    worker_info: Optional[WorkerInfo] = None


# Bid Models (for Contractual jobs)
class BidBase(BaseModel):
    bid_amount: float
    visiting_charge: float = 0.0
    message: str = ""


class BidInput(BaseModel):
    bid_amount: float = Field(gt=0, le=10_000_000)
    visiting_charge: float = Field(default=0.0, ge=0, le=1_000_000)
    message: str = Field(default="", max_length=2000)


class BidCreate(BidBase):
    job_id: str


class Bid(BidBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    worker_id: str
    status: str = ApplicationStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BidWithWorker(Bid):
    worker_info: Optional[WorkerInfo] = None


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
    comment: str = Field(default="", max_length=2000)


class ReviewCreate(ReviewBase):
    # Both are optional: the server derives the reviewee from the job's assignment.
    job_id: Optional[str] = None
    reviewee_user_id: Optional[str] = None


class Review(ReviewBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    reviewer_user_id: str
    reviewee_user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Payment Models
class PaymentCreate(BaseModel):
    job_id: str
    # Optional and only used as a consistency check: the server charges the agreed amount.
    amount: Optional[float] = None
    method: Literal["cod", "upi", "card"] = "cod"


class PaymentVerify(BaseModel):
    payment_id: str
    razorpay_payment_id: str
    razorpay_signature: str


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
    content: str = Field(min_length=1, max_length=2000)
    # "system" messages can only be created by the server
    message_type: Literal["text", "location"] = "text"


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


# A run of digits that may be broken up by spaces, dashes, dots or brackets, e.g.
# "9876543210", "98765 43210", "+91-98765-43210", "(987) 654 3210"
PHONE_CANDIDATE_RE = re.compile(r"(?<!\w)\+?\d[\d\s\-().]{8,}\d(?!\w)")


def mask_phone_numbers(text: str) -> str:
    """Mask every phone-number-like sequence (10+ digits) in free text."""

    def _mask(match):
        digits = re.sub(r"\D", "", match.group())
        if len(digits) < 10:
            return match.group()
        return mask_phone_number(digits)

    return PHONE_CANDIDATE_RE.sub(_mask, text)


def strip_mongo_id(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Remove MongoDB's ObjectId so the document can be JSON-serialized."""
    if doc is not None:
        doc.pop("_id", None)
    return doc


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


async def get_worker_info_map(worker_ids: List[str]) -> Dict[str, WorkerInfo]:
    """Fetch display info for many workers in one query."""
    if not worker_ids:
        return {}
    workers = await db.users.find(
        {"id": {"$in": list(set(worker_ids))}},
        {"_id": 0, "id": 1, "name": 1, "rating_avg": 1, "reviews_count": 1},
    ).to_list(length=None)
    return {
        w["id"]: WorkerInfo(
            name=w.get("name", "Worker"),
            rating_avg=w.get("rating_avg", 0.0),
            reviews_count=w.get("reviews_count", 0),
        )
        for w in workers
    }


# =============================================================================
# AUTH UTILITIES
# =============================================================================


def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
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

    if user_doc.get("status") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended by an administrator."
        )

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


def issue_token(user: User) -> Token:
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer", user=user)


# =============================================================================
# AUTH ROUTES
# =============================================================================


@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists (phone is already normalized by UserCreate)
    existing_user = await db.users.find_one({"phone": user_data.phone})
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this phone number already exists"
        )

    if user_data.email:
        existing_email = await db.users.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(
                status_code=400, detail="User with this email already exists"
            )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.model_dump(exclude={"password"})

    user = User(**user_dict)
    user_doc = user.model_dump()
    user_doc["password_hash"] = hashed_password
    user_doc["status"] = "active"

    try:
        await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400, detail="User with this phone number already exists"
        )

    # Create worker profile if role is worker
    if user.role == UserRole.WORKER:
        worker_profile = WorkerProfile(user_id=user.id)
        await db.worker_profiles.insert_one(worker_profile.model_dump())

    return issue_token(user)


@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    # Accept any formatting of the number; fall back to the raw value for legacy accounts.
    user_doc = await db.users.find_one({"phone": normalize_phone(credentials.phone)})
    if not user_doc:
        user_doc = await db.users.find_one({"phone": credentials.phone.strip()})

    if not user_doc or not verify_password(
        credentials.password, user_doc.get("password_hash")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_doc.get("status") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended by an administrator.",
        )

    return issue_token(User(**user_doc))


@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


# =============================================================================
# USER ROUTES
# =============================================================================


@api_router.get("/users/{user_id}", response_model=PublicUser)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return PublicUser(**user_doc)


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
    # Only overwrite fields the client actually sent, so omitted fields keep their values
    update_data = profile_data.model_dump(exclude_unset=True)

    update: Dict[str, Any] = {"$setOnInsert": {"id": str(uuid.uuid4())}}
    if update_data:
        update["$set"] = update_data
    await db.worker_profiles.update_one(
        {"user_id": current_user.id}, update, upsert=True
    )

    profile_doc = await db.worker_profiles.find_one({"user_id": current_user.id})
    return WorkerProfile(**profile_doc)


# =============================================================================
# FILE UPLOADS
# =============================================================================

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024


def looks_like_image(file_ext: str, head: bytes) -> bool:
    """Check the file's magic bytes match its extension."""
    if file_ext in (".jpg", ".jpeg"):
        return head.startswith(b"\xff\xd8\xff")
    if file_ext == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if file_ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return False


@api_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    """Upload an image securely and return its URL"""
    file_ext = os.path.splitext(file.filename or "")[1].lower()

    # Validate extension
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and WEBP files are allowed.")

    safe_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename

    # Stream to disk so a large upload is rejected without being held in memory
    error_detail = None
    size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_BYTES)
            if not chunk:
                break
            if size == 0 and not looks_like_image(file_ext, chunk[:12]):
                error_detail = "File content is not a valid JPG, PNG, or WEBP image."
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                error_detail = "File too large. Max 10MB allowed."
                break
            f.write(chunk)

    if error_detail is None and size == 0:
        error_detail = "Uploaded file is empty."

    if error_detail:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=error_detail)

    return {"url": f"/uploads/{safe_filename}", "filename": safe_filename}


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

    # Workers are notified when the job is published, not while it is a draft
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

    # Only load the fields needed for matching
    workers = await db.worker_profiles.find(
        {},
        {
            "_id": 0,
            "user_id": 1,
            "skills": 1,
            "preferred_locations": 1,
            "service_radius_km": 1,
        },
    ).to_list(length=None)

    notifications = []
    for worker_profile in workers:
        # Check if worker has matching skills or is in service radius
        worker_skills = [s.lower() for s in worker_profile.get("skills", [])]
        has_matching_skills = any(skill in worker_skills for skill in job_skills)

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
            notifications.append(
                Notification(
                    user_id=worker_profile["user_id"],
                    type=NotificationType.NEW_JOB,
                    title="New Job Available",
                    message=f"A new {job.type} job '{job.title}' is available in your area",
                    data={"job_id": job.id, "job_type": job.type},
                ).model_dump()
            )

    if notifications:
        await db.notifications.insert_many(notifications)


@api_router.post("/jobs/search", response_model=List[Job])
async def search_jobs(
    filters: JobSearchFilters, current_user: User = Depends(get_current_user)
):
    # Build MongoDB query
    query = {"status": JobStatus.OPEN}

    if filters.search_term:
        pattern = re.escape(filters.search_term)
        query["$or"] = [
            {"title": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
        ]

    if filters.job_type:
        query["type"] = filters.job_type

    if filters.category:
        query["category"] = filters.category

    if filters.min_budget is not None:
        query["budget_amount"] = {"$gte": filters.min_budget}

    if filters.max_budget is not None:
        if "budget_amount" in query:
            query["budget_amount"]["$lte"] = filters.max_budget
        else:
            query["budget_amount"] = {"$lte": filters.max_budget}

    # Execute query
    jobs = await db.jobs.find(query).to_list(length=1000)
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


JOB_SORTS = {
    "recent": [("created_at", -1)],
    "budget_high": [("budget_amount", -1), ("created_at", -1)],
    "budget_low": [("budget_amount", 1), ("created_at", -1)],
}


@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(
    status: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    mine: bool = False,
    sort: str = "recent",
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """List jobs.

    - mine=true: the caller's own jobs (customers: jobs they posted, any status;
      workers: jobs assigned to them).
    - otherwise: the public marketplace, which only ever shows open jobs
      (admins may filter by any non-draft status).
    """
    filter_dict: Dict[str, Any] = {}

    if mine:
        if current_user.role == UserRole.CUSTOMER:
            filter_dict["customer_id"] = current_user.id
        elif current_user.role == UserRole.WORKER:
            assignments = await db.assignments.find(
                {"worker_id": current_user.id}, {"_id": 0, "job_id": 1}
            ).to_list(length=None)
            filter_dict["id"] = {"$in": [a["job_id"] for a in assignments]}
        else:
            return []
        if status:
            filter_dict["status"] = status
    elif current_user.role == UserRole.ADMIN:
        if status == JobStatus.DRAFT:
            return []
        filter_dict["status"] = status if status else {"$ne": JobStatus.DRAFT}
    else:
        filter_dict["status"] = JobStatus.OPEN

    if type:
        filter_dict["type"] = type
    if category:
        filter_dict["category"] = category
    if search:
        pattern = re.escape(search)
        filter_dict["$or"] = [
            {"title": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
        ]

    jobs = (
        await db.jobs.find(filter_dict)
        .sort(JOB_SORTS.get(sort, JOB_SORTS["recent"]))
        .skip(skip)
        .limit(limit)
        .to_list(length=None)
    )
    return [Job(**job) for job in jobs]


@api_router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, current_user: User = Depends(get_current_user)):
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    if (
        job_doc.get("status") == JobStatus.DRAFT
        and job_doc["customer_id"] != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**job_doc)


@api_router.get("/jobs/{job_id}/participants")
async def get_job_participants(
    job_id: str, current_user: User = Depends(get_current_user)
):
    """Names of the customer and assigned worker, for the two of them (and admins)."""
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    assignment = await db.assignments.find_one({"job_id": job_id})
    worker_id = assignment["worker_id"] if assignment else None

    if (
        current_user.id not in (job_doc["customer_id"], worker_id)
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    async def public_name(user_id: Optional[str]):
        if not user_id:
            return None
        doc = await db.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "name": 1})
        return doc or {"id": user_id, "name": "User"}

    return {
        "customer": await public_name(job_doc["customer_id"]),
        "worker": await public_name(worker_id),
        "assignment": (
            {
                "id": assignment["id"],
                "final_amount": assignment["final_amount"],
                "status": assignment.get("status"),
            }
            if assignment
            else None
        ),
    }


@api_router.put("/jobs/{job_id}/publish")
async def publish_job(job_id: str, current_user: User = Depends(get_current_user)):
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only drafts can be published; this must never reopen an assigned/completed job
    result = await db.jobs.update_one(
        {"id": job_id, "status": JobStatus.DRAFT},
        {"$set": {"status": JobStatus.OPEN}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Only draft jobs can be published")

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
    app_dict["message"] = app_dict["message"][:2000]
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


@api_router.get(
    "/jobs/{job_id}/applications", response_model=List[ApplicationWithWorker]
)
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
    workers = await get_worker_info_map([a["worker_id"] for a in applications])

    return [
        ApplicationWithWorker(**app, worker_info=workers.get(app["worker_id"]))
        for app in applications
    ]


# =============================================================================
# BID ROUTES (Contractual Jobs)
# =============================================================================


@api_router.post("/jobs/{job_id}/bid", response_model=Bid)
async def place_bid(
    job_id: str,
    bid_data: BidInput,
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
        bid_dict["status"] = existing_bid.get("status", ApplicationStatus.PENDING)
        return Bid(**bid_dict)

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


@api_router.get("/jobs/{job_id}/bids", response_model=List[BidWithWorker])
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
    workers = await get_worker_info_map([b["worker_id"] for b in bids])

    return [
        BidWithWorker(**bid, worker_info=workers.get(bid["worker_id"])) for bid in bids
    ]


# =============================================================================
# WORKER DASHBOARD ROUTES
# =============================================================================


async def build_worker_applications(worker_id: str) -> List[Dict[str, Any]]:
    """Every job a worker applied to or bid on, newest first."""
    applications = await db.applications.find({"worker_id": worker_id}).to_list(
        length=None
    )
    bids = await db.bids.find({"worker_id": worker_id}).to_list(length=None)

    job_ids = list({a["job_id"] for a in applications} | {b["job_id"] for b in bids})
    jobs = {}
    if job_ids:
        job_docs = await db.jobs.find({"id": {"$in": job_ids}}).to_list(length=None)
        jobs = {job["id"]: job for job in job_docs}

    applied_jobs = []
    seen_job_ids = set()
    for entry in applications + bids:
        job = jobs.get(entry["job_id"])
        if not job or job["id"] in seen_job_ids:
            continue
        seen_job_ids.add(job["id"])
        applied_jobs.append(
            {
                "id": job["id"],
                "title": job["title"],
                "status": job["status"],
                "application_status": entry["status"],
                "type": job["type"],
                "budget_amount": job["budget_amount"],
                "applied_at": entry["created_at"],
            }
        )

    applied_jobs.sort(key=lambda x: x["applied_at"], reverse=True)
    return applied_jobs


@api_router.get("/worker/applications")
async def get_worker_applications(
    current_user: User = Depends(require_role(UserRole.WORKER)),
):
    return await build_worker_applications(current_user.id)


@api_router.get("/worker/dashboard-data")
async def get_worker_dashboard_data(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.WORKER:
        raise HTTPException(status_code=403, detail="Only workers can access this data")

    applied_jobs = await build_worker_applications(current_user.id)

    # Calculate stats
    # 1. Available jobs (total open jobs in system)
    available_jobs_count = await db.jobs.count_documents({"status": JobStatus.OPEN})

    # 2. Applied jobs count (total unique jobs worker applied to)
    applied_count = len(applied_jobs)

    # 3. Active/Won jobs count (jobs where application/bid is accepted)
    active_count = len([j for j in applied_jobs if j["application_status"] == ApplicationStatus.ACCEPTED])

    # 4. Profile completion (simple check for now)
    profile = await db.worker_profiles.find_one({"user_id": current_user.id})
    profile_completion = 40 if not profile else 100 # Simplistic for demo

    # 5. Get recent reviews for the worker
    recent_reviews = await db.reviews.find({"reviewee_user_id": current_user.id}).sort("created_at", -1).limit(5).to_list(length=None)
    reviewer_ids = list({r["reviewer_user_id"] for r in recent_reviews})
    reviewers = {}
    if reviewer_ids:
        reviewer_docs = await db.users.find(
            {"id": {"$in": reviewer_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(length=None)
        reviewers = {r["id"]: r["name"] for r in reviewer_docs}

    return {
        "stats": {
            "availableJobs": available_jobs_count,
            "appliedJobs": applied_count,
            "activeJobs": active_count,
            "profileCompletion": profile_completion,
            "ratingAvg": current_user.rating_avg,
            "reviewsCount": current_user.reviews_count,
        },
        "recentApplications": applied_jobs[:5],
        "recentReviews": [
            {
                "stars": r["stars"],
                "comment": r["comment"],
                "reviewer_name": reviewers.get(r["reviewer_user_id"], "Customer"),
                "created_at": r["created_at"]
            } for r in recent_reviews
        ]
    }


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

    # Find the worker's pending application (daily) or bid (contractual)
    if job_doc["type"] == JobType.DAILY:
        offers, not_found = db.applications, "Application not found"
    else:
        offers, not_found = db.bids, "Bid not found"

    offer = await offers.find_one(
        {"job_id": job_id, "worker_id": worker_id, "status": ApplicationStatus.PENDING}
    )
    if not offer:
        raise HTTPException(status_code=404, detail=not_found)

    if job_doc["type"] == JobType.DAILY:
        # For daily jobs, use the fixed budget
        final_amount = job_doc["budget_amount"]
    else:
        # For contractual jobs, use the bid amount
        final_amount = offer["bid_amount"] + offer.get("visiting_charge", 0)

    # Claim the job atomically so two concurrent assignments cannot both succeed
    claimed = await db.jobs.update_one(
        {"id": job_id, "status": JobStatus.OPEN},
        {"$set": {"status": JobStatus.ASSIGNED}},
    )
    if claimed.modified_count == 0:
        raise HTTPException(
            status_code=409, detail="Job is no longer available for assignment"
        )

    # Accept this offer, reject the others
    await offers.update_one(
        {"job_id": job_id, "worker_id": worker_id},
        {"$set": {"status": ApplicationStatus.ACCEPTED}},
    )
    await offers.update_many(
        {"job_id": job_id, "worker_id": {"$ne": worker_id}},
        {"$set": {"status": ApplicationStatus.REJECTED}},
    )

    # Create assignment (replacing any stale one left by older builds)
    assignment = Assignment(
        job_id=job_id, worker_id=worker_id, final_amount=final_amount
    )
    await db.assignments.replace_one(
        {"job_id": job_id}, assignment.model_dump(), upsert=True
    )

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

PAYABLE_JOB_STATUSES = [JobStatus.ASSIGNED, JobStatus.IN_PROGRESS]
SETTLED_PAYMENT_STATUSES = [PaymentStatus.SUCCEEDED, PaymentStatus.RECORDED_COD]


@api_router.post("/payments/create-order")
async def create_payment_order(
    payment_data: PaymentCreate, current_user: User = Depends(get_current_user)
):
    job_doc = await db.jobs.find_one({"id": payment_data.job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify user is customer for this job
    if job_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Verify job assignment exists
    assignment = await db.assignments.find_one({"job_id": payment_data.job_id})
    if not assignment:
        raise HTTPException(status_code=404, detail="Job assignment not found")

    if job_doc["status"] not in PAYABLE_JOB_STATUSES:
        raise HTTPException(
            status_code=400, detail="Payment can only be made for an assigned job"
        )

    already_paid = await db.payments.find_one(
        {"job_id": payment_data.job_id, "status": {"$in": SETTLED_PAYMENT_STATUSES}}
    )
    if already_paid:
        raise HTTPException(status_code=400, detail="This job has already been paid")

    # The amount is always the one agreed at assignment time
    amount = float(assignment["final_amount"])
    if payment_data.amount is not None and abs(payment_data.amount - amount) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount must equal the agreed amount of ₹{amount:g}",
        )

    # Create payment record
    payment = Payment(
        job_id=payment_data.job_id,
        payer_id=current_user.id,
        payee_id=assignment["worker_id"],
        method=payment_data.method,
        amount=amount,
    )

    if payment_data.method == PaymentMethod.COD:
        # Complete the job atomically so a double submit cannot record two payments
        completed = await db.jobs.update_one(
            {"id": payment_data.job_id, "status": {"$in": PAYABLE_JOB_STATUSES}},
            {"$set": {"status": JobStatus.COMPLETED}},
        )
        if completed.modified_count == 0:
            raise HTTPException(status_code=409, detail="This job has already been paid")

        payment.status = PaymentStatus.RECORDED_COD
        await db.payments.insert_one(payment.model_dump())

        # Notify worker
        await create_notification(
            assignment["worker_id"],
            NotificationType.PAYMENT_RECEIVED,
            "Payment Recorded - COD",
            f"Cash payment of ₹{amount:g} has been recorded for job '{job_doc['title']}'",
            {
                "job_id": payment_data.job_id,
                "payment_id": payment.id,
                "amount": amount,
            },
        )

        return {
            "payment_id": payment.id,
            "status": "cod_recorded",
            "message": "COD payment recorded successfully",
        }

    # Online payments (UPI / card) go through Razorpay
    if not razorpay_client:
        raise HTTPException(
            status_code=503, detail="Online payments are not configured. Please use cash (COD)."
        )

    try:
        order_data = {
            "amount": int(round(amount * 100)),  # Convert to paise
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "job_id": payment_data.job_id,
                "customer_id": current_user.id,
                "worker_id": assignment["worker_id"],
            },
        }
        razorpay_order = razorpay_client.order.create(order_data)
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to create payment order")

    payment.razorpay_order_id = razorpay_order["id"]
    await db.payments.insert_one(payment.model_dump())

    return {
        "payment_id": payment.id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": razorpay_order["amount"],
        "currency": razorpay_order["currency"],
        "key_id": RAZORPAY_KEY_ID,
    }


@api_router.post("/payments/verify")
async def verify_payment(
    verification: PaymentVerify,
    current_user: User = Depends(get_current_user),
):
    # Find payment record
    payment_doc = await db.payments.find_one({"id": verification.payment_id})
    if not payment_doc or payment_doc["payer_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment_doc["status"] == PaymentStatus.SUCCEEDED:
        return {"status": "success", "message": "Payment already verified"}

    if not razorpay_client or not payment_doc.get("razorpay_order_id"):
        raise HTTPException(status_code=400, detail="Payment cannot be verified")

    try:
        razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": payment_doc["razorpay_order_id"],
                "razorpay_payment_id": verification.razorpay_payment_id,
                "razorpay_signature": verification.razorpay_signature,
            }
        )
    except Exception as e:
        await db.payments.update_one(
            {"id": verification.payment_id}, {"$set": {"status": PaymentStatus.FAILED}}
        )
        logger.warning(f"Payment signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Payment verification failed")

    await db.payments.update_one(
        {"id": verification.payment_id},
        {
            "$set": {
                "status": PaymentStatus.SUCCEEDED,
                "razorpay_payment_id": verification.razorpay_payment_id,
            }
        },
    )

    # Update job status to completed
    await db.jobs.update_one(
        {"id": payment_doc["job_id"], "status": {"$in": PAYABLE_JOB_STATUSES}},
        {"$set": {"status": JobStatus.COMPLETED}},
    )

    # Notify worker
    job_doc = await db.jobs.find_one({"id": payment_doc["job_id"]})
    await create_notification(
        payment_doc["payee_id"],
        NotificationType.PAYMENT_RECEIVED,
        "Payment Received!",
        f"You have received ₹{payment_doc['amount']:g} for job '{job_doc['title'] if job_doc else ''}'",
        {
            "job_id": payment_doc["job_id"],
            "payment_id": verification.payment_id,
            "amount": payment_doc["amount"],
        },
    )

    return {"status": "success", "message": "Payment verified successfully"}


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
        # New messages are masked when stored; this also covers older, unmasked ones
        if chat_msg.message_type == MessageType.TEXT:
            chat_msg.content = mask_phone_numbers(chat_msg.content)
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

    content = message_data.content
    if message_data.message_type == MessageType.TEXT:
        # Store the masked text so raw phone numbers never reach the database
        content = mask_phone_numbers(content)

    # Create message
    message = ChatMessage(
        job_id=job_id,
        sender_user_id=current_user.id,
        receiver_user_id=receiver_id,
        content=content,
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
    if review_data.job_id and review_data.job_id != job_id:
        raise HTTPException(status_code=400, detail="Job ID mismatch")

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

    # Each party can only review the other party on the same job
    if current_user.id == job_doc["customer_id"]:
        reviewee_id = assignment["worker_id"]
    elif current_user.id == assignment["worker_id"]:
        reviewee_id = job_doc["customer_id"]
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    if review_data.reviewee_user_id and review_data.reviewee_user_id != reviewee_id:
        raise HTTPException(
            status_code=400, detail="You can only review the other party on this job"
        )

    # Check if already reviewed
    existing_review = await db.reviews.find_one(
        {"job_id": job_id, "reviewer_user_id": current_user.id}
    )
    if existing_review:
        raise HTTPException(
            status_code=400, detail="You have already reviewed this job"
        )

    # Create review
    review = Review(
        job_id=job_id,
        reviewer_user_id=current_user.id,
        reviewee_user_id=reviewee_id,
        stars=review_data.stars,
        comment=review_data.comment,
    )

    await db.reviews.insert_one(review.model_dump())

    # Update user's rating
    user_reviews = await db.reviews.find(
        {"reviewee_user_id": reviewee_id}, {"_id": 0, "stars": 1}
    ).to_list(length=None)
    avg_rating = sum(r["stars"] for r in user_reviews) / len(user_reviews)

    await db.users.update_one(
        {"id": reviewee_id},
        {"$set": {"rating_avg": avg_rating, "reviews_count": len(user_reviews)}},
    )

    # Update worker trust score when the customer reviews the worker
    if current_user.id == job_doc["customer_id"]:
        trust_increase = (review_data.stars - 3) * 2  # -4 to +4 points
        await db.worker_profiles.update_one(
            {"user_id": reviewee_id},
            {"$inc": {"trust_score": trust_increase}},
        )

    return review


@api_router.get("/users/{user_id}/reviews", response_model=List[Review])
async def get_user_reviews(
    user_id: str, limit: int = Query(10, ge=1, le=50), skip: int = Query(0, ge=0)
):
    reviews = (
        await db.reviews.find({"reviewee_user_id": user_id})
        .sort("created_at", -1)
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
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
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


@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    await db.notifications.update_many(
        {"user_id": current_user.id, "is_read": False}, {"$set": {"is_read": True}}
    )

    return {"status": "all_notifications_marked_as_read"}


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
        "payment_methods": ["cod", "upi", "card"] if razorpay_client else ["cod"],
        "razorpay_key_id": RAZORPAY_KEY_ID if razorpay_client else None,
        "maps_enabled": True,  # Placeholder for Google Maps
        "chat_enabled": True,
        "notifications_enabled": True,
    }


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================
# All API routers must be registered before the SPA catch-all below: routes match
# in registration order, so anything added after it would be shadowed.

app.include_router(api_router)

from admin_routes import admin_router  # noqa: E402  (imports names defined above)

app.include_router(admin_router, prefix="/api")


# =============================================================================
# STATIC FILE SERVING (for React frontend) - must stay last
# =============================================================================

STATIC_DIR = (Path(__file__).parent / "static").resolve()
if STATIC_DIR.exists():
    # Serve React app for all non-API routes
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        # Don't serve index.html for API routes
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Serve real files (static/js/*, static/css/*, ...) but never outside STATIC_DIR
        file_path = (STATIC_DIR / full_path).resolve()
        if file_path.is_file() and file_path.is_relative_to(STATIC_DIR):
            return FileResponse(file_path)

        # Otherwise serve index.html for client-side routing
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Not found")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
