# Sanyuth: Technical Product Documentation (PRD & Architecture)

> **Project Name:** Sanyuth (also known as Shidhaan)
> **Version:** 1.0.0 (Production-Ready)
> **Target Market:** Blue-collar services marketplace for India 

---

## 1. Executive Summary & Product Vision

**Sanyuth** is an AI-ready blue-collar marketplace that seamlessly connects individuals and businesses (Customers) with skilled laborers and daily wage workers (Workers). The platform provides robust functionality for standard fixed-rate daily jobs, as well as complex contractual tasks requiring localized bidding and negotiation.

Sanyuth acts as the intermediary handling discovery, secure communication, trust and reputation (via ratings), dispute resolution, and payment flows. 

---

## 2. User Personas & Core Journeys

The platform serves three distinct user groups, each with specialized interfaces and access levels.

### 2.1 The Customer
*Individuals or businesses looking to hire workers.*
- **Job Creation:** Post two types of jobs: "Daily Wage" (fixed rate, direct apply) and "Contractual" (complex tasks, competitive bidding).
- **Job Attachments:** Upload visual references (imgs/photos up to 10MB) to set clear expectations.
- **Secure Interaction:** Use masked in-app chat for private communication prior to job commencement.
- **Checkout:** Fulfill requests seamlessly via digital checkout (Razorpay API) or Cash-on-Delivery (COD).
- **Rating/Reviewing:** Evaluate workers post-job, directly contributing to the worker's average trust and skill rating on the platform.

### 2.2 The Worker
*Skilled tradespeople or labor seeking immediate or contractual engagements.*
- **Public Profile:** Maintain a professional storefront showcasing skills, experience, and aggregated customer ratings.
- **Discovery Engine:** Find nearby open jobs utilizing location filtering, budget matching, and categorical search.
- **Conversion Flow:** Engage directly using a 1-click apply for daily jobs or submit custom financial bids (with added visiting charges) for contractual posts.

### 2.3 The Enterprise Administrator
*Operators executing platform oversight, moderation, and arbitration.*
- **Central Portal & Secure Login:** Sequestered interface via `/admin-login`.
- **Analytics & Health Tracking:** Live metrics detailing revenue, active users, KYC statuses, and job volumes.
- **User Management & Striking Policy:** The power to suspend user permissions or issue formal "Strikes" due to policy violations (3 strikes trigger an automated suspension).
- **Dispute Resolution:** Tools to intercept and mediate transactional conflicts (e.g., refunds, payout blocking).

---

## 3. Technology Architecture & Stack

Sanyuth relies on a scalable, decoupled architecture combining a modern React SPA and an asynchronous Python backend, adhering strictly to RESTful design patterns.

### 3.1 Frontend (Presentation Layer)
- **Framework:** React 18+ (Single Page Application)
- **Styling Engine:** Tailwind CSS combined with Shadcn UI for accessible, primitive components.
- **Routing:** React Router v6
- **Global State / Data Fetching:** Standard Hooks (`useState`/`useEffect`) and `Axios` for HTTP requests.
- **Icons & Affordances:** Lucide-React and Sonner (Toast notifications).

### 3.2 Backend (API Layer)
- **Framework:** FastAPI (High-performance Async Python)
- **Server:** Uvicorn 
- **Authentication:** JWT (JSON Web Tokens) with `jose`, securely hashing passwords with `passlib[bcrypt]`.
- **Role-Based Access Control (RBAC):** Native role verification directly injected into route dependencies (`/admin/`, `/workers/`).
- **File Handling:** Local volume storage served statically over `/uploads`. Photos are UUID-renamed for security.

### 3.3 Database (Data Layer)
- **System:** MongoDB Atlas (NoSQL)
- **Driver:** `motor` (Asynchronous Python driver)
- **Key Identifiers:** Standardized UUIDs natively resolving over BSON documents. DateTime stored as normalized ISO strings.

### 3.4 Infrastructure & Deployment
- **Containerization:** Docker & Docker Compose configured across local dev environments.
- **Production Host:** Fly.io hosting both frontend static generation and backend execution. 
- **3rd-Party APIs:** Razorpay Sandbox, standard geolocation data structures.

---

## 4. Platform Design System

To preserve a "premium" software feel, Sanyuth executes a rigorous set of design constraints:
- **Primary Focus:** `orange-600` (`#ea580c`) used strictly for Call-to-Actions (CTAs) and primary branding.
- **Status Metrics:** `green-600` for accepted/success states, `red-600` for rejected/alert items, and `blue-600` for daily badge differentiators.
- **Topology:** Generous whitespace inside `rounded-lg` cards backed by a slight `gray-50` backdrop across all dashboards. Dark mode interfaces intentionally built out for the Enterprise Admin Portal.
- **Animations:** Subtle `animate-spin` queues for file uploading and `animate-pulse` application skeleton screens. 

---

## 5. Core System Entities (Database Schema)

| Collection | Schema Description & Core BSON Fields | 
| :--- | :--- |
| **`users`** | `id`, `name`, `phone`, `role` (customer/worker/admin), `password_hash`, `rating_avg`, `reviews_count`, `trust_score`. |
| **`jobs`** | `id`, `customer_id`, `title`, `description`, `type` (daily/contractual), `status`, `photos` (List[str]), `budget_amount`, `applications_count`. |
| **`applications`** | Application instances connecting a single worker to a daily job. `id`, `job_id`, `worker_id`, `status` (pending/accepted/rejected), `message`. |
| **`bids`** | Competitive pricing instance for a contractual job. `id`, `job_id`, `worker_id`, `bid_amount`, `visiting_charge`, `status`. |
| **`reviews`** | Verified customer feedback tied to a finished job index. `id`, `reviewer_user_id`, `reviewee_user_id`, `job_id`, `stars` (1-5 integer), `comment`. |
| **`notifications`** | Platform alerts structure. `id`, `user_id`, `type`, `title`, `content`, `is_read`. |

---

## 6. Global API Reference 

Key architectural components of the `/api` route. All routes (excluding Auth) mandate a Bearer JWT Token in headers.

### 6.1 User / Auth Subsystem
- `POST /auth/register` - Instantiate a new Customer or Worker.
- `POST /auth/login` - Validate credentials to receive a signed JWT payload.
- `GET /workers/profile` / `PUT /workers/profile` - Interacts with Worker discovery details and skill arrays.

### 6.2 Core Job Flows
- `POST /jobs` - Ingest a new Job request struct (Payload configures for `daily` vs `contractual`).
- `POST /upload` - Standardized `multipart/form-data` endpoint handling image verification, UUID translation, mapping to `/uploads/<uuid>.jpg`.

### 6.3 Enterprise Moderation (`/admin`)
- `GET /admin/dashboard` - Consolidate aggregation pipelines outlining revenue, user signups, and job statuses.
- `POST /admin/users/{id}/strike` - Modulate a specific account's strike threshold.
- `POST /admin/disputes/{id}/action` - Issue financial reversals or dismiss claims securely.

---

## 7. Deployment Overview

Sanyuth is optimized for containerized deployments across modern Edge runtimes (i.e., Fly.io).

1. **Pre-requisites:** Live MongoDB Cloud Atlas connection string, valid Razorpay API Key ID/Secret pairing, Flyctl CLI. 
2. **Environment Variable Injection:** Local `.env` mirroring including `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, and `REACT_APP_BACKEND_URL`. 
3. **Execution Pipeline:** 
   - Fly.io initialization generates instances via `fly launch`.
   - `fly secrets set` ensures keys bypass source code entirely.
   - `docker-compose up -d` handles local parity debugging.
4. **Data Hydration:** `/backend/create_demo_users.py` handles auto-seeding of default user categories spanning Customer scenarios, Worker scenarios, and resolving Administrative Superuser credentials.
