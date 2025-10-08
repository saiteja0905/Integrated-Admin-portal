// MongoDB initialization script for Shidhaan Marketplace
db = db.getSiblingDB('shidhaan_marketplace');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "role", "created_at"],
      properties: {
        email: { bsonType: "string" },
        role: { enum: ["Customer", "Worker", "Admin"] },
        created_at: { bsonType: "date" }
      }
    }
  }
});

db.createCollection('jobs');
db.createCollection('applications');
db.createCollection('bids');
db.createCollection('payments');
db.createCollection('reviews');
db.createCollection('chats');
db.createCollection('notifications');
db.createCollection('disputes');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "phone": 1 });
db.users.createIndex({ "role": 1 });

db.jobs.createIndex({ "status": 1 });
db.jobs.createIndex({ "category": 1 });
db.jobs.createIndex({ "job_type": 1 });
db.jobs.createIndex({ "location": "2dsphere" });
db.jobs.createIndex({ "created_at": -1 });

db.applications.createIndex({ "job_id": 1 });
db.applications.createIndex({ "worker_id": 1 });
db.applications.createIndex({ "status": 1 });

db.bids.createIndex({ "job_id": 1 });
db.bids.createIndex({ "worker_id": 1 });
db.bids.createIndex({ "amount": 1 });

db.payments.createIndex({ "job_id": 1 });
db.payments.createIndex({ "user_id": 1 });
db.payments.createIndex({ "status": 1 });

db.reviews.createIndex({ "job_id": 1 });
db.reviews.createIndex({ "reviewer_id": 1 });
db.reviews.createIndex({ "reviewee_id": 1 });

db.chats.createIndex({ "job_id": 1 });
db.chats.createIndex({ "participants": 1 });
db.chats.createIndex({ "created_at": -1 });

db.notifications.createIndex({ "user_id": 1 });
db.notifications.createIndex({ "read": 1 });
db.notifications.createIndex({ "created_at": -1 });

db.disputes.createIndex({ "job_id": 1 });
db.disputes.createIndex({ "status": 1 });
db.disputes.createIndex({ "created_at": -1 });

print("Shidhaan Marketplace database initialized successfully!");
