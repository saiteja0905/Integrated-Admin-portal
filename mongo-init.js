// MongoDB initialization script for Shidhaan Marketplace
db = db.getSiblingDB('shidhaan_marketplace');

// Create collections (without strict validation to allow flexibility)
db.createCollection('users');
db.createCollection('worker_profiles');
db.createCollection('jobs');
db.createCollection('applications');
db.createCollection('bids');
db.createCollection('assignments');
db.createCollection('payments');
db.createCollection('reviews');
db.createCollection('chat_messages');
db.createCollection('notifications');
db.createCollection('disputes');
db.createCollection('announcements');
db.createCollection('user_strikes');

// Create indexes for better performance
db.users.createIndex({ "phone": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { sparse: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "id": 1 }, { unique: true });

db.worker_profiles.createIndex({ "user_id": 1 }, { unique: true });
db.worker_profiles.createIndex({ "id": 1 }, { unique: true });

db.jobs.createIndex({ "id": 1 }, { unique: true });
db.jobs.createIndex({ "customer_id": 1 });
db.jobs.createIndex({ "status": 1 });
db.jobs.createIndex({ "category": 1 });
db.jobs.createIndex({ "type": 1 });
db.jobs.createIndex({ "created_at": -1 });

db.applications.createIndex({ "id": 1 }, { unique: true });
db.applications.createIndex({ "job_id": 1 });
db.applications.createIndex({ "worker_id": 1 });
db.applications.createIndex({ "status": 1 });

db.bids.createIndex({ "id": 1 }, { unique: true });
db.bids.createIndex({ "job_id": 1 });
db.bids.createIndex({ "worker_id": 1 });
db.bids.createIndex({ "bid_amount": 1 });

db.assignments.createIndex({ "id": 1 }, { unique: true });
db.assignments.createIndex({ "job_id": 1 }, { unique: true });
db.assignments.createIndex({ "worker_id": 1 });

db.payments.createIndex({ "id": 1 }, { unique: true });
db.payments.createIndex({ "job_id": 1 });
db.payments.createIndex({ "payer_id": 1 });
db.payments.createIndex({ "payee_id": 1 });
db.payments.createIndex({ "status": 1 });

db.reviews.createIndex({ "id": 1 }, { unique: true });
db.reviews.createIndex({ "job_id": 1 });
db.reviews.createIndex({ "reviewer_user_id": 1 });
db.reviews.createIndex({ "reviewee_user_id": 1 });

db.chat_messages.createIndex({ "id": 1 }, { unique: true });
db.chat_messages.createIndex({ "job_id": 1 });
db.chat_messages.createIndex({ "sender_user_id": 1 });
db.chat_messages.createIndex({ "receiver_user_id": 1 });
db.chat_messages.createIndex({ "created_at": -1 });

db.notifications.createIndex({ "id": 1 }, { unique: true });
db.notifications.createIndex({ "user_id": 1 });
db.notifications.createIndex({ "is_read": 1 });
db.notifications.createIndex({ "created_at": -1 });

db.disputes.createIndex({ "id": 1 }, { unique: true });
db.disputes.createIndex({ "job_id": 1 });
db.disputes.createIndex({ "status": 1 });
db.disputes.createIndex({ "created_at": -1 });

db.announcements.createIndex({ "id": 1 }, { unique: true });
db.announcements.createIndex({ "target_audience": 1 });
db.announcements.createIndex({ "created_at": -1 });

db.user_strikes.createIndex({ "id": 1 }, { unique: true });
db.user_strikes.createIndex({ "user_id": 1 });
db.user_strikes.createIndex({ "is_active": 1 });

print("✅ Shidhaan Marketplace database initialized successfully!");
print("📋 Collections created: users, worker_profiles, jobs, applications, bids, assignments, payments, reviews, chat_messages, notifications, disputes, announcements, user_strikes");
print("🔍 Indexes created for optimal query performance");
