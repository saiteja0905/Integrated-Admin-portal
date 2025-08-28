#!/usr/bin/env python3
"""
Script to create demo users for Shidhaan marketplace testing
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_demo_users():
    """Create demo users for testing"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
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
                "address": "Connaught Place, New Delhi, India"
            },
            "rating_avg": 4.5,
            "reviews_count": 12,
            "created_at": datetime.now(timezone.utc),
            "password_hash": pwd_context.hash("password123")
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
                "address": "Noida, Uttar Pradesh, India"
            },
            "rating_avg": 4.7,
            "reviews_count": 25,
            "created_at": datetime.now(timezone.utc),
            "password_hash": pwd_context.hash("password123")
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
            "password_hash": pwd_context.hash("admin123")
        }
    ]
    
    # Insert demo users
    for user in demo_users:
        existing = await db.users.find_one({"phone": user["phone"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"✅ Created {user['role']}: {user['name']} ({user['phone']})")
            
            # Create worker profile for worker user
            if user['role'] == 'worker':
                worker_profile = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "skills": ["Plumbing", "Electrical Work", "Carpentry"],
                    "experience_years": 5,
                    "certifications": ["ITI Certificate", "Safety Training"],
                    "preferred_locations": [user["location"]],
                    "completed_jobs": 18,
                    "cancelled_jobs": 1,
                    "trust_score": 85.5
                }
                await db.worker_profiles.insert_one(worker_profile)
                print(f"✅ Created worker profile for {user['name']}")
        else:
            print(f"⚠️ User {user['phone']} already exists")
    
    # Create some demo jobs
    demo_jobs = [
        {
            "id": str(uuid.uuid4()),
            "customer_id": demo_users[0]["id"],  # Rajesh Kumar (customer)
            "type": "daily",
            "category": "skilled",
            "title": "Bathroom Plumbing Repair",
            "description": "Need experienced plumber to fix leaking pipes in bathroom. Urgent work required.",
            "photos": [],
            "location": {
                "lat": 28.6139,
                "lng": 77.2090,
                "address": "Connaught Place, New Delhi, India"
            },
            "preferred_time_window": {
                "start": "09:00",
                "end": "17:00"
            },
            "budget_amount": 2500.0,
            "is_budget_negotiable": False,
            "status": "open",
            "created_at": datetime.now(timezone.utc),
            "applications_count": 0,
            "bids_count": 0
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
                "address": "Connaught Place, New Delhi, India"
            },
            "preferred_time_window": {
                "start": "08:00",
                "end": "18:00"
            },
            "budget_amount": 50000.0,
            "is_budget_negotiable": True,
            "status": "open", 
            "created_at": datetime.now(timezone.utc),
            "applications_count": 0,
            "bids_count": 0
        }
    ]
    
    # Insert demo jobs
    for job in demo_jobs:
        existing = await db.jobs.find_one({"title": job["title"]})
        if not existing:
            await db.jobs.insert_one(job)
            print(f"✅ Created job: {job['title']} ({job['type']})")
        else:
            print(f"⚠️ Job {job['title']} already exists")
    
    client.close()
    print("\n🎉 Demo data creation completed!")
    print("\nDemo Login Credentials:")
    print("Customer: 9876543210 / password123")
    print("Worker: 9876543211 / password123") 
    print("Admin: 9876543212 / admin123")

if __name__ == "__main__":
    asyncio.run(create_demo_users())