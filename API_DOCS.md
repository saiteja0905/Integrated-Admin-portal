# Shidhaan API Documentation

This document describes the primary RESTful API endpoints exposed by the Shidhaan FastAPI backend. The API handles authentication, job management, admin operations, and file uploads. 

## Base URL
In local development, the API is accessible at:
`http://localhost:8000/api`

## Authentication

The application uses standard JWT Bearer tokens for authentication (`Authorization: Bearer <token>`).

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/auth/register` | Register a new user (Customer or Worker) | No |
| `POST` | `/auth/login`    | Login to receive JWT access token | No |
| `GET`  | `/auth/me`       | Retrieve the currently authenticated user | Yes |

## Core Application (Jobs & Profiles)

These endpoints run the core functional experience for Customers and Workers.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET`  | `/users/{user_id}` | Fetch limited profile info for a user | Yes |
| `GET`  | `/workers/profile` | Retrieve the authenticated worker's public profile | Yes (Worker) |
| `PUT`  | `/workers/profile` | Update the worker's skills/certifications | Yes (Worker) |
| `POST` | `/jobs` | Create a new job (Daily or Contractual) | Yes (Customer) |
| `POST` | `/upload` | Upload photos directly for job attachments | Yes |

### Image Attachments (`POST /upload`)
- **Input:** Multipart `FormData` containing a `file` field.
- **Output:** Returns JSON containing the relative host path e.g., `{"url": "/uploads/<secure-uuid>.jpg", "filename": "<secure-uuid>.jpg"}`.
- **Limits:** Hard limited to 10MB per file. Only accepts `.jpg`, `.png`, and `.webp`.

## Admin & Enterprise Routings

The Enterprise Admin Portal relies on these secured endpoints to moderate behavior, jobs, and finances on the platform. All routes under `/admin/` require the `admin` user role.

### Dashboard & Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/admin/dashboard` | Generate top-level platform analytics |
| `GET`  | `/admin/users` | Fetch all users with custom filtering |
| `GET`  | `/admin/users/{user_id}/activity` | Load a granular timeline of user actions |
| `POST` | `/admin/users/{user_id}/strike` | Issue moderate actions/warnings on an account |

### KYC & Dispute Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/admin/kyc/pending` | List pending KYC ID checks |
| `PUT`  | `/admin/kyc/{kyc_id}/verify` | Accept or reject verification tasks |
| `GET`  | `/admin/disputes` | List active platform disputes |
| `PUT`  | `/admin/disputes/{dispute_id}/assign` | Claim a dispute for review |
| `POST` | `/admin/disputes/{dispute_id}/action` | Refund or resolve a dispute ticket |

### Job Moderation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/admin/jobs/moderation` | Retrieve jobs triggered by platform flags |
| `PUT`  | `/admin/jobs/{job_id}/moderate` | Remove or reinstate flagged content |

## Web Sockets (Future Readiness)
The platform is heavily structured to ingest real-time messaging using websockets (`/api/ws/chat`), although standard polling is actively used where websocket integrations are partially implemented. 

## Data Types

### Standard Job Requirements
When utilizing `/api/jobs` directly, the payload must conform to the following JSON structure:
```json
{
  "type": "daily", // or "contractual"
  "category": "skilled",
  "title": "Need an urgent plumber",
  "description": "Fix my bathroom pipes.",
  "photos": ["/uploads/example-123.jpg"], 
  "location": {
    "lat": 28.6139,
    "lng": 77.2090,
    "address": "Delhi"
  },
  "budget_amount": 2000,
  "is_budget_negotiable": false
}
```
