# Sanyuth User Personas & System Flows

The Sanyuth platform facilitates a robust two-sided marketplace tailored for blue-collar services, governed by a central Enterprise administrative portal. 

## 1. The Customer
**Role:** Individuals or businesses looking to hire skilled labor or daily wage workers.

### Key Features
- **Job Creation (Dual Flow):** 
  - *Daily Wage/Direct Hire:* Post a fixed-rate job and automatically receive direct applications from workers looking for immediate work.
  - *Contractual:* Post a complex job to invite dynamic bidding. Compare incoming quotes and profiles.
- **Image Attachments:** Upload visual references (up to 10MB per image) of the work site so workers know what to expect.
- **Secure Communication:** In-app chat interface with phone number masking guarantees privacy before a job is mutually confirmed.
- **Dynamic Checkouts:** Support for both Cash-on-Delivery (COD) or seamless digital UPI payments via Razorpay.
- **Ratings & Reviews:** Rate workers post-completion, driving their trust scores.

### Primary User Flow
1. **Onboarding:** Registers via Mobile/Email OTP -> Completes basic profile.
2. **Posting:** Navigates to 'Post Job' -> Fills details, location, and photos -> Submits.
3. **Selection:** Waits for applications/bids -> Views Worker profiles and trust scores -> Selects a Worker.
4. **Execution:** Chats securely with Worker -> Job begins -> Job completed.
5. **Closure:** Completes payment (digital or cash) -> Leaves a public review.

---

## 2. The Worker
**Role:** Skilled tradespeople (electricians, plumbers, carpenters) or daily wage laborers seeking employment.

### Key Features
- **Public Profile:** Showcase skills, previous job reviews, ratings, and certifications.
- **Job Discovery Engine:** Advanced filtering to discover open jobs based on proximity (Geo-location), budget, category, or job type.
- **Application & Bidding Console:** 
  - One-click apply for standard daily wage requests.
  - Dynamic bid submissions (featuring custom budget quotes) for contractual work.
- **Trust Scores & KYC:** (Upcoming) Highlighting verified workers to boost selection rates.

### Primary User Flow
1. **Onboarding:** Registers via Mobile/Email OTP -> Fills out skills, categories, and availability. 
2. **Discovery:** Browse the active job board -> Filters by location and expertise.
3. **Engagement:** Submits an application (Fixed price) OR places a competitive bid (Contractual).
4. **Execution:** Customer accepts the bid -> Uses masked chat to organize arrival -> Completes the physical job.
5. **Closure:** Customer confirms completion -> Receives payment offline/online -> Rating boosts their global profile.

---

## 3. The Enterprise Admin
**Role:** Platform operators responsible for maintaining safety, quality, and dispute mediation.

### Key Features
- **Centralized Dashboard (`/admin-login`):** Secure, dedicated metrics page highlighting active jobs, user growth, pending KYC, and revenue.
- **User Management & Striking:** Complete oversight of all users. Ability to issue formal "Strikes" internally, leading to automated suspensions at a 3-strike limit.
- **Content Moderation:** Authority to flag and review specific questionable job listings.
- **Dispute Resolution:** Claim and actively mediate disputes raised between Customers and Workers (e.g., payment issues, no-shows) offering refund capabilities.
- **Platform Configuration & Broadcasts:** Alter overarching app settings or send platform-wide announcement push notifications dynamically.

### Primary User Flow
1. **Authentication:** Uses secure credentials to access the sequestered `/admin-login` route.
2. **Monitoring:** Reviews top-level analytics and pending KYC or Moderation queues from the Dashboard.
3. **Intervention:** Navigates to a raised Dispute -> Reviews attached chat logs/images -> Issues a resolution (refund or strike).
4. **Growth:** Identifies top performers via analytics algorithms -> Uses the announcement tool to promote platform updates.
