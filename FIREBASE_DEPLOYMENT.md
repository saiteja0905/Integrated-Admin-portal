# Sanyuth Marketplace - Firebase Deployment Guide

This guide provides step-by-step instructions for hosting and deploying the full-stack Sanyuth application using **Firebase Hosting** for the React frontend, **Google Cloud Run / Cloud Functions** (part of Firebase platform) for the Python FastAPI backend, and **MongoDB Atlas** for the database.

---

## 🏗️ Deployment Architecture Overview

```
 ┌─────────────────────────────────────────────────────────┐
 │                   FIREBASE PLATFORM                     │
 │                                                         │
 │  ┌───────────────────────┐   ┌───────────────────────┐  │
 │  │   Firebase Hosting    │   │  Google Cloud Run /   │  │
 │  │    (React Frontend)   │───▶   Cloud Functions     │  │
 │  │    `*.web.app`        │   │   (FastAPI Backend)   │  │
 │  └───────────────────────┘   └───────────┬───────────┘  │
 └──────────────────────────────────────────┼──────────────┘
                                            │
                                            ▼
                                ┌───────────────────────┐
                                │     MongoDB Atlas     │
                                │   (Cloud Database)    │
                                └───────────────────────┘
```

---

## 📋 Prerequisites

1. **Node.js & npm** (installed locally).
2. **Google / Firebase Account** ([Firebase Console](https://console.firebase.google.com/)).
3. **MongoDB Atlas Account** ([MongoDB Atlas](https://cloud.mongodb.com/)).
4. **Firebase CLI**:
   ```bash
   npx -y firebase-tools@latest --version
   ```

---

## Step 1: Firebase Project Setup & Authentication

### 1.1 Log into Firebase CLI
Run the following command in your terminal to log in with your Google account:

```bash
npx -y firebase-tools@latest login
```

*(Note: On Windows PowerShell, if execution policy blocks scripts, run: `cmd.exe /c "npx -y firebase-tools@latest login"`)*

### 1.2 Select or Create a Firebase Project
To set up your project context, run:

```bash
# Option A: Connect an existing project
npx -y firebase-tools@latest use <YOUR_FIREBASE_PROJECT_ID>

# Option B: Create a new project via CLI
npx -y firebase-tools@latest projects:create sanyuth-marketplace --display-name "Sanyuth Marketplace"
```

---

## Step 2: Build & Deploy React Frontend to Firebase Hosting

### 2.1 Set Production Backend URL (Optional)
If your FastAPI backend is already hosted (e.g. Cloud Run, Render, or Fly.io), update `frontend/.env.production`:

```env
REACT_APP_BACKEND_URL=https://your-backend-api-url.a.run.app
```

### 2.2 Build the Frontend Production Assets
Navigate to the `frontend/` directory and build the web application:

```bash
cd frontend
npm run build
cd ..
```

### 2.3 Deploy Frontend to Firebase Hosting
Deploy your compiled static assets directly to Firebase Hosting:

```bash
npx -y firebase-tools@latest deploy --only hosting
```

Once deployment completes, Firebase will provide your live URL:
`https://<YOUR_PROJECT_ID>.web.app`

---

## Step 3: Deploy FastAPI Backend (Python) to Google Cloud Run

Since Firebase Hosting serves static assets & SPAs natively, Python backends (FastAPI) are deployed to **Google Cloud Run** (Google Cloud's serverless container runner, fully integrated with Firebase).

### 3.1 Install Google Cloud CLI
Install the `gcloud` CLI from [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).

### 3.2 Deploy Backend Container
Run the following command from the root of your project directory:

```bash
gcloud run deploy sanyuth-backend \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net/",DB_NAME="sanyuth_db",JWT_SECRET="your-secret-key"
```

### 3.3 Route API Requests via Firebase Hosting (Optional Rewrite)
You can route `/api/**` traffic seamlessly through your Firebase Hosting domain by adding a rewrite rule to `firebase.json`:

```json
{
  "hosting": {
    "public": "frontend/build",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "sanyuth-backend",
          "region": "asia-south1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

---

## ⚡ Useful Firebase Commands Summary

| Command | Purpose |
| :--- | :--- |
| `npx -y firebase-tools@latest login` | Authenticate CLI with Google/Firebase |
| `npx -y firebase-tools@latest projects:list` | List all available Firebase projects |
| `npx -y firebase-tools@latest use <PROJECT_ID>` | Switch active Firebase project |
| `npx -y firebase-tools@latest emulators:start --only hosting` | Test Firebase Hosting locally |
| `npx -y firebase-tools@latest deploy --only hosting` | Deploy frontend live to Firebase Hosting |

---

## 🔑 Default Admin & Test Credentials

After initializing your database instance with `create_demo_users.py`:
- **Admin Phone**: `9876543212`
- **Password**: `admin123`
