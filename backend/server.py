from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
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
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(title="Shidhaan API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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

class WorkerProfileCreate(BaseModel):
    skills: List[str] = []
    experience_years: int = 0
    certifications: List[str] = []
    preferred_locations: List[Location] = []

# Job Models
class TimeWindow(BaseModel):
    start: str  # e.g., "09:00"
    end: str    # e.g., "17:00"

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
                detail=f"Access denied. Required role: {required_role}"
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
            status_code=400,
            detail="User with this phone number already exists"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.model_dump()
    user_dict['password_hash'] = hashed_password
    del user_dict['password']
    
    user = User(**user_dict)
    user_doc = user.model_dump()
    user_doc['password_hash'] = hashed_password
    
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
    if not user_doc or not verify_password(credentials.password, user_doc.get('password_hash')):
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
async def get_worker_profile(current_user: User = Depends(require_role(UserRole.WORKER))):
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
    current_user: User = Depends(require_role(UserRole.WORKER))
):
    update_data = profile_data.model_dump()
    
    await db.worker_profiles.update_one(
        {"user_id": current_user.id},
        {"$set": update_data},
        upsert=True
    )
    
    profile_doc = await db.worker_profiles.find_one({"user_id": current_user.id})
    return WorkerProfile(**profile_doc)

# =============================================================================
# JOB ROUTES
# =============================================================================

@api_router.post("/jobs", response_model=Job)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER))
):
    job_dict = job_data.model_dump()
    job_dict['customer_id'] = current_user.id
    job = Job(**job_dict)
    
    await db.jobs.insert_one(job.model_dump())
    return job

@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(
    status: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    skip: int = 0
):
    filter_dict = {}
    if status:
        filter_dict['status'] = status
    if type:
        filter_dict['type'] = type
    if category:
        filter_dict['category'] = category
    
    jobs = await db.jobs.find(filter_dict).skip(skip).limit(limit).to_list(length=None)
    return [Job(**job) for job in jobs]

@api_router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**job_doc)

@api_router.put("/jobs/{job_id}/publish")
async def publish_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_doc['customer_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {"status": JobStatus.OPEN}}
    )
    
    return {"message": "Job published successfully"}

# =============================================================================
# APPLICATION ROUTES (Daily Jobs)
# =============================================================================

@api_router.post("/jobs/{job_id}/apply", response_model=Application)
async def apply_to_job(
    job_id: str,
    application_data: ApplicationBase,
    current_user: User = Depends(require_role(UserRole.WORKER))
):
    # Check if job exists and is daily type
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_doc['type'] != JobType.DAILY:
        raise HTTPException(status_code=400, detail="Can only apply to daily jobs")
    
    if job_doc['status'] != JobStatus.OPEN:
        raise HTTPException(status_code=400, detail="Job is not accepting applications")
    
    # Check if already applied
    existing_app = await db.applications.find_one({
        "job_id": job_id,
        "worker_id": current_user.id
    })
    if existing_app:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    # Create application
    app_dict = application_data.model_dump()
    app_dict['job_id'] = job_id
    app_dict['worker_id'] = current_user.id
    application = Application(**app_dict)
    
    await db.applications.insert_one(application.model_dump())
    
    # Update job applications count
    await db.jobs.update_one(
        {"id": job_id},
        {"$inc": {"applications_count": 1}}
    )
    
    return application

@api_router.get("/jobs/{job_id}/applications", response_model=List[Application])
async def get_job_applications(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    # Verify job ownership or admin access
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_doc['customer_id'] != current_user.id and current_user.role != UserRole.ADMIN:
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
    current_user: User = Depends(require_role(UserRole.WORKER))
):
    # Check if job exists and is contractual type
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_doc['type'] != JobType.CONTRACTUAL:
        raise HTTPException(status_code=400, detail="Can only bid on contractual jobs")
    
    if job_doc['status'] != JobStatus.OPEN:
        raise HTTPException(status_code=400, detail="Job is not accepting bids")
    
    # Update existing bid or create new one
    bid_dict = bid_data.model_dump()
    bid_dict['job_id'] = job_id
    bid_dict['worker_id'] = current_user.id
    
    existing_bid = await db.bids.find_one({
        "job_id": job_id,
        "worker_id": current_user.id
    })
    
    if existing_bid:
        # Update existing bid
        await db.bids.update_one(
            {"job_id": job_id, "worker_id": current_user.id},
            {"$set": bid_dict}
        )
        bid_dict['id'] = existing_bid['id']
        bid_dict['created_at'] = existing_bid['created_at']
    else:
        # Create new bid
        bid = Bid(**bid_dict)
        await db.bids.insert_one(bid.model_dump())
        
        # Update job bids count
        await db.jobs.update_one(
            {"id": job_id},
            {"$inc": {"bids_count": 1}}
        )
        
        return bid
    
    return Bid(**bid_dict)

@api_router.get("/jobs/{job_id}/bids", response_model=List[Bid])
async def get_job_bids(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    # Verify job ownership or admin access
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_doc['customer_id'] != current_user.id and current_user.role != UserRole.ADMIN:
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
    current_user: User = Depends(require_role(UserRole.CUSTOMER))
):
    # Verify job ownership
    job_doc = await db.jobs.find_one({"id": job_id})
    if not job_doc or job_doc['customer_id'] != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_doc['status'] != JobStatus.OPEN:
        raise HTTPException(status_code=400, detail="Job is not available for assignment")
    
    # Determine final amount based on job type
    if job_doc['type'] == JobType.DAILY:
        # For daily jobs, use the fixed budget
        final_amount = job_doc['budget_amount']
        
        # Verify application exists
        app_doc = await db.applications.find_one({
            "job_id": job_id,
            "worker_id": worker_id,
            "status": ApplicationStatus.PENDING
        })
        if not app_doc:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Update application status
        await db.applications.update_one(
            {"job_id": job_id, "worker_id": worker_id},
            {"$set": {"status": ApplicationStatus.ACCEPTED}}
        )
        
        # Reject other applications
        await db.applications.update_many(
            {"job_id": job_id, "worker_id": {"$ne": worker_id}},
            {"$set": {"status": ApplicationStatus.REJECTED}}
        )
        
    else:  # CONTRACTUAL
        # For contractual jobs, use the bid amount
        bid_doc = await db.bids.find_one({
            "job_id": job_id,
            "worker_id": worker_id,
            "status": ApplicationStatus.PENDING
        })
        if not bid_doc:
            raise HTTPException(status_code=404, detail="Bid not found")
        
        final_amount = bid_doc['bid_amount'] + bid_doc.get('visiting_charge', 0)
        
        # Update bid status
        await db.bids.update_one(
            {"job_id": job_id, "worker_id": worker_id},
            {"$set": {"status": ApplicationStatus.ACCEPTED}}
        )
        
        # Reject other bids
        await db.bids.update_many(
            {"job_id": job_id, "worker_id": {"$ne": worker_id}},
            {"$set": {"status": ApplicationStatus.REJECTED}}
        )
    
    # Create assignment
    assignment = Assignment(
        job_id=job_id,
        worker_id=worker_id,
        final_amount=final_amount
    )
    
    await db.assignments.insert_one(assignment.model_dump())
    
    # Update job status
    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {"status": JobStatus.ASSIGNED}}
    )
    
    return {"message": "Job assigned successfully", "assignment_id": assignment.id}

# =============================================================================
# BASIC ROUTES
# =============================================================================

@api_router.get("/")
async def root():
    return {"message": "Shidhaan API v1.0.0 - Blue Collar Marketplace"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Include the router
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()