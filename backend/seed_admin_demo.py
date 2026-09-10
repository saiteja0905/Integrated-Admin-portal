import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(mongo_url)
db = client.shidhaan

async def seed_admin_dashboard_data():
    print("🚀 Seeding Admin Dashboard Demo Data...")
    
    # 1. Fetch some existing users to attach data to
    demousers = await db.users.find({}).to_list(10)
    if not demousers:
        print("❌ No users found. Please run create_demo_users.py first or start the server to auto-seed.")
        return

    worker = next((u for u in demousers if u.get("role") == "worker"), demousers[0])
    customer = next((u for u in demousers if u.get("role") == "customer"), demousers[1])

    # 2. Add fake disputes
    print("=> Injecting Mock Disputes...")
    await db.disputes.delete_many({}) # Clear old ones if running multiple times
    disputes = [
        {
            "id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
            "raised_by": customer["id"],
            "against": worker["id"],
            "title": "Worker did not show up",
            "description": "I hired this worker for a daily wage job but they never arrived and are ignoring my calls.",
            "category": "no_show",
            "severity": "high",
            "status": "open",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2)
        },
        {
            "id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
            "raised_by": worker["id"],
            "against": customer["id"],
            "title": "Customer refusing to pay full amount",
            "description": "I completed the plumbing work but the customer is only paying half of the agreed digital bid.",
            "category": "payment_issue",
            "severity": "medium",
            "status": "under_review",
            "created_at": datetime.now(timezone.utc) - timedelta(days=1)
        }
    ]
    await db.disputes.insert_many(disputes)

    # 3. Add fake KYC verifications
    print("=> Injecting Mock KYC Verifications...")
    await db.kyc_verifications.delete_many({})
    kyc_docs = [
        {
            "id": str(uuid.uuid4()),
            "user_id": worker["id"],
            "document_type": "national_id",
            "document_url": "mock_id_card.jpg",
            "overall_status": "pending",
            "submitted_at": datetime.now(timezone.utc) - timedelta(hours=5)
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()), # Fake user for variation
            "document_type": "driving_license",
            "document_url": "mock_license.jpg",
            "overall_status": "pending",
            "submitted_at": datetime.now(timezone.utc) - timedelta(hours=10)
        }
    ]
    await db.kyc_verifications.insert_many(kyc_docs)

    # 4. Add fake Payment Revenue Data
    print("=> Injecting Mock Revenue History...")
    await db.payments.delete_many({})
    
    payments = []
    for i in range(15):
        days_ago = i * 2 # Spread payments over last 30 days
        payments.append({
            "id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
            "payer_id": customer["id"],
            "payee_id": worker["id"],
            "amount": 1000.0 + (i * 250), # Varying amounts
            "currency": "INR",
            "status": "succeeded",
            "payment_method": "online",
            "created_at": datetime.now(timezone.utc) - timedelta(days=days_ago)
        })
    await db.payments.insert_many(payments)

    print("🎉 Admin Demo Data Seeded Successfully!")
    print("   Data injected: 2 Disputes, 2 KYC requests, 15 Historical Payments")

if __name__ == "__main__":
    asyncio.run(seed_admin_dashboard_data())
