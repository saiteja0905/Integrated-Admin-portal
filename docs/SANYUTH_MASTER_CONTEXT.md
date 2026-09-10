# 💎 Sanyuth: Master Project Context (LLM Source of Truth)

**Project Name**: Sanyuth / Shidhaan
**Version**: 1.0.0 (Demo Ready - April 2026)
**Target Market**: Blue-collar marketplace for India (Connecting Workers & Customers)

---

## 🛠 1. Technology Stack

### Frontend (React Single Page App)
- **Framework**: React 18+
- **Styling**: Tailwind CSS (Utility-first) + Shadcn UI (Component primitives)
- **Routing**: React Router DOM v6
- **Icons**: Lucide-React (e.g., `Camera`, `Briefcase`, `Zap`, `Loader2`)
- **State/Data**: Axios (API requests), standard React `useState`/`useEffect`.
- **Feedback**: Sonner (Toast notifications)
- **Base URL Config**: `REACT_APP_BACKEND_URL` environment variable.

### Backend (FastAPI / Python)
- **Framework**: FastAPI (Asynchronous Python)
- **Database**: MongoDB (NoSQL) using `motor` (Async driver)
- **Auth**: JWT (JSON Web Tokens) with `jose`, password hashing with `passlib[bcrypt]`.
- **Server**: Uvicorn
- **Utilities**: `dotenv` (Environment config), `uuid` (Unique IDs), `razorpay` (Payment integration).

### Infrastructure
- **Containerization**: Docker & Docker Compose.
- **Serving**: Backend serves the built React frontend as static files from `/static`.
- **File Handling**: Local storage (`/uploads`) served via `StaticFiles`.

---

## 🎨 2. Design System & Aesthetics

### Brand Colors
- **Primary**: `orange-600` (`#ea580c`) - Used for CTAs, critical buttons, and branding.
- **Secondary**: `blue-600` - Used for Daily Job badges and application states.
- **Success**: `green-600` - Used for "Accepted" states and profile completion.
- **Alert**: `red-600` - Used for "Rejected" states and negative actions.
- **Background**: Light gray (`gray-50`) for main layout; White (`#ffffff`) for cards/containment.

### Typography & UI
- **Font Stack**: Modern Sans-Serif (system defaults).
- **Aesthetic**: Clean, modern, high-contrast, "premium" feel.
- **Components**:
  - `StarRating`: A reusable utility for rendering 1-5 gold stars (display and interactive modes).
  - `ReviewModal`: A popup for customers to submit feedback after job completion.
- **Animations**:
  - `animate-spin`: Used for the image upload loader (`Loader2`).
  - `animate-pulse`: Used for loading skeletons.
  - `transition-all`: Applied to hover states on cards and buttons.

### Layout Principles
- **Grid System**: 3-column layouts for dashboards; 1-column responsive for mobile.
- **Card Design**: Rounded corners (`rounded-lg`), subtle borders (`border-gray-200`), and light shadows.

---

## 👥 3. User Personas & Permissions

### A. Customer
- **Role**: `customer`
- **Dashboard**: High-level stats, quick actions (Post Job), and recent postings.
- **Capabilities**:
  - Post **Daily Jobs** (Fixed price, direct application).
  - Post **Contractual Jobs** (Bidding based).
  - Review applications/bids.
  - Hire/Select workers.
  - Make payments (Razorpay/COD simulation).

### B. Worker
- **Role**: `worker`
- **Dashboard**: Available jobs count, Applied Jobs stats, Profile completion, and **Reputation Stats** (Average rating + Review count).
- **Capabilities**:
  - Search/Filter jobs (by distance, category, budget).
  - Apply for Daily Jobs.
  - Place Bids for Contractual Jobs.
  - View "Recent Applications" list with real-time status updates (**New!**).
  - Open full Job Details (including photos) to check requirements.
  - **View Feedback**: Read recent customer reviews and ratings on their dashboard.

### C. Administrator
- **Role**: `admin`
- **Dashboard**: Global analytics (Revenue, Users, Active Jobs).
- **Capabilities**:
  - Manage all users (Active/Suspend).
  - Issue "Strikes" to problematic users.
  - Moderate job postings.
  - Manage disputes and announcements.

---

## 🔄 4. Core Platform Flows

### I. The "Daily Job" Flow
1. **Post**: Customer creates a job with a fixed budget.
2. **Apply**: Worker sees the job and clicks "Apply Now" (sends a message).
3. **Select**: Customer views all applications and clicks "Select Worker".
4. **Complete**: Job moves to assigned/completed after work is done.

### II. The "Contractual" Flow
1. **Post**: Customer posts a job marked as `contractual`.
2. **Bid**: Workers place bids (e.g., ₹5000 + ₹200 visiting charge).
3. **Compare**: Customer compares bids (and worker ratings) and selects the best candidate.
4. **Negotiate**: In-app chat facilitates negotiation.

### III. The Reputation & Review Flow (**New!**)
1. **Trigger**: Once a job status is set to `completed`.
2. **Action**: Customer is prompted with a "Rate Worker" button in the job details.
3. **Submit**: Customer opens `ReviewModal`, selects stars (1-5), and adds an optional comment.
4. **Update**: Backend saves the `Review` and automatically updates the Worker's `rating_avg` and `reviews_count`.
5. **Display**: The updated rating is now visible to other customers during the application process.

### III. Image Management Flow
1. **Upload**: During "Post Job", images are sent via `multipart/form-data` to `/api/upload`.
2. **Rename**: Backend renames files with UUIDs for security.
3. **Store**: Relative path (e.g., `/uploads/uuid.png`) is stored in the `Job.photos` array.
4. **Serve**: Frontend prepends `BACKEND_URL` to serve the image.

---

## 💾 5. Database Schema (BSON Key Fields)

### Collections:
- **`users`**: `id`, `name`, `phone`, `role`, `password_hash`, `rating_avg`, `reviews_count`, `trust_score`.
- **`jobs`**: `id`, `customer_id`, `title`, `description`, `type` (daily|contractual), `status`, `photos` (List[str]), `budget_amount`, `applications_count`.
- **`applications`**: `id`, `job_id`, `worker_id`, `status` (pending|accepted|rejected), `message`, `created_at`.
- **`bids`**: `id`, `job_id`, `worker_id`, `bid_amount`, `visiting_charge`, `status`.
- **`reviews`**: `id`, `reviewer_user_id`, `reviewee_user_id`, `job_id`, `stars` (1-5), `comment`, `created_at`.
- **`notifications`**: `id`, `user_id`, `type`, `title`, `content`, `is_read`.

---

## 📍 6. Low-Level Development Notes

- **Port Mapping**: Container runs on `8000`. Native MongoDB on `27017`.
- **URL Handling**: Frontend uses absolute URLs for images (`${BACKEND_URL}${photo}`) but relative slugs for API calls.
- **Security Check**: CSRF is bypassed for demo, but JWT Bearer tokens must be present in `Authorization` headers for all protected routes.
- **Auto-Seeding**: The `server.py` contains a `seed_demo_data()` function that ensures the system is never empty during a demo.

> [!TIP]
> **Context for Future LLMs**: When modifying `App.js`, remember it is a monolithic file (~2500 lines). Always verify JSX nesting, as the code uses complex ternary routing. 
