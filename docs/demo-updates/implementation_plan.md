# Worker Dashboard & Applied Jobs Fix

The current "Worker Dashboard" is a static placeholder with hardcoded numbers. This plan implements the necessary backend support and frontend logic to show workers their actual statistics and the list of jobs they have applied for.

## User Review Required

> [!IMPORTANT]
> **Data Privacy**: The new dashboard endpoint will be restricted to users with the `worker` role, ensuring they can only see their own applications.

## Proposed Changes

### [Component] Backend (server.py)

#### [MODIFY] [server.py](file:///Users/saitejagurajala/Desktop/App-SDN/webapp%20updates/Integrated-Admin-portal/backend/server.py)
*   **New Endpoint**: Add `GET /api/worker/dashboard-data`. 
    *   Fetch all `applications` and `bids` belonging to the current worker.
    *   For each application/bid, fetch the corresponding `job` details (title, status, budget).
    *   Calculate dashboard stats: 
        *   `availableJobsCount` (Total "open" jobs in system).
        *   `appliedJobsCount` (Count of unique jobs with pending/active applications/bids).
        *   `activeJobsCount` (Count of jobs where application/bid status is "accepted").

---

### [Component] Frontend (App.js)

#### [MODIFY] [App.js](file:///Users/saitejagurajala/Desktop/App-SDN/webapp%20updates/Integrated-Admin-portal/frontend/src/App.js)
*   **WorkerDashboard Component**:
    *   Add `useState` for `stats` and `appliedJobs`.
    *   Add `useEffect` to fetch data from `/api/worker/dashboard-data` on mount.
    *   Update the "Available Jobs" card to show the real count.
    *   Update the "Applied Jobs" card to show the real count.
    *   **New Section**: Add a "Recent Applications" list below the stats cards to show the last 5 jobs applied for, including the job title, date, and status.

## Open Questions

1.  **Job Selection**: Should clicking an applied job in the dashboard take the worker to the Job Details page? (Currently, workers have limited detail view access).

## Verification Plan

### Automated Tests
*   Verify the new API endpoint using `curl` with a worker's JWT token.

### Manual Verification
1.  Log in as a Worker.
2.  Go to "Find Jobs" and apply to 1-2 jobs.
3.  Return to the Dashboard and verify:
    *   The "Applied Jobs" count increased.
    *   The jobs appear in the "Recent Applications" list with the correct status (Pending).
4.  Log in as a Customer/Admin and "Accept" one of the applications.
5.  Return to the Worker Dashboard and verify the status updated to "Accepted".
