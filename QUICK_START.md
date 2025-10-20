# 🚀 Shidhaan - Quick Start Guide

## One-Command Docker Setup

```bash
# Start everything (first time)
docker-compose up --build -d

# That's it! 🎉
```

## What Happens Automatically

### 1️⃣ **MongoDB Container Starts**
- Creates database `shidhaan_marketplace`
- Creates collections and indexes
- Runs `mongo-init.js` (one-time setup)

### 2️⃣ **Backend Container Starts**
- Builds React frontend (production optimized)
- Starts FastAPI backend on port 8000
- **Automatically seeds demo data** if database is empty
  - ✅ 3 demo users (customer, worker, admin)
  - ✅ 2 sample jobs
  - ✅ Worker profile

### 3️⃣ **Ready to Use!**
- Open: http://localhost:8000
- Login with demo credentials (see below)

---

## 🔑 Demo Credentials

| Role | Phone | Password |
|------|-------|----------|
| **Customer** | 9876543210 | password123 |
| **Worker** | 9876543211 | password123 |
| **Admin** | 9876543212 | admin123 |

---

## 📊 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend & API** | http://localhost:8000 | Main application |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **API Health** | http://localhost:8000/api/health | Health check |
| **MongoDB Express** | http://localhost:8081 | Database admin UI |

**MongoDB Express Login:**
- Username: `admin`
- Password: `admin123`

---

## 🔄 Common Commands

```bash
# View logs
docker-compose logs -f

# View app logs only
docker-compose logs -f app

# Stop everything
docker-compose down

# Stop and delete database (fresh start)
docker-compose down -v

# Restart app (preserves database)
docker-compose restart app

# Rebuild after code changes
docker-compose up --build
```

---

## 🌱 Auto-Seeding Behavior

### **First Startup (Empty Database)**
```
🚀 Starting Shidhaan API...
🌱 Database is empty. Seeding demo data...
✅ Created customer: Rajesh Kumar (9876543210)
✅ Created worker: Priya Sharma (9876543211)
✅ Created worker profile for Priya Sharma
✅ Created admin: Admin User (9876543212)
✅ Created job: Bathroom Plumbing Repair (daily)
✅ Created job: Kitchen Renovation Work (contractual)
🎉 Demo data seeded successfully!
```

### **Subsequent Startups**
```
🚀 Starting Shidhaan API...
✓ Database already has 3 users. Skipping seed.
```

**Key Points:**
- ✅ Fully automatic - no manual commands needed
- ✅ Idempotent - safe to restart multiple times
- ✅ Smart - only seeds when database is empty
- ✅ Fast - seeds in ~2 seconds on startup

---

## 🐛 Troubleshooting

### Backend Not Starting?
```bash
# Check logs
docker-compose logs app

# Common issue: MongoDB not ready
# Solution: Wait 10 seconds and restart
docker-compose restart app
```

### CORS Errors?
```bash
# Make sure you access via http://localhost:8000
# NOT http://127.0.0.1:8000 (different origin)
```

### Database Issues?
```bash
# Reset database (deletes all data)
docker-compose down -v
docker-compose up -d

# Wait for backend to auto-seed
docker-compose logs -f app
```

### Port Already in Use?
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in docker-compose.yml
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Docker Compose Stack            │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │     Shidhaan App Container      │   │
│  │  Port: 8000                     │   │
│  ├─────────────────────────────────┤   │
│  │  FastAPI Backend (Python)       │   │
│  │  - API Routes (/api/*)          │   │
│  │  - Auto-seed on startup         │   │
│  │  - Static file serving          │   │
│  ├─────────────────────────────────┤   │
│  │  React Frontend (Built)         │   │
│  │  - Customer Portal              │   │
│  │  - Worker Portal                │   │
│  │  - Admin Portal                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   MongoDB Container             │   │
│  │  Port: 27017                    │   │
│  │  - Auto-init collections        │   │
│  │  - Persistent volume            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  MongoDB Express (Optional)     │   │
│  │  Port: 8081                     │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📝 What Changed from Original Code?

### **Minimal Changes:**
1. ✅ Added `StaticFiles` and `FileResponse` to serve React app
2. ✅ Added auto-seed function (~150 lines in server.py)
3. ✅ Fixed `mongo-init.js` to match backend schema
4. ✅ Updated Dockerfile for Node 22 compatibility

### **No Breaking Changes:**
- ✅ All existing API routes work unchanged
- ✅ Frontend code works as-is
- ✅ Database schema matches backend models
- ✅ Demo user script still available for manual use

---

## 🎯 Next Steps

1. **Test the Application**
   - Try logging in as customer, worker, and admin
   - Create new jobs, apply to jobs
   - Test different features

2. **Customize Demo Data**
   - Edit the `seed_demo_data()` function in `backend/server.py`
   - Add more users, jobs, or test data

3. **Production Deployment**
   - See `DOCKER_SETUP.md` for production configuration
   - Update environment variables in `docker-compose.yml`
   - Configure reverse proxy with SSL

4. **Development Workflow**
   - Backend changes: Rebuild with `docker-compose up --build`
   - Frontend changes: Rebuild (React gets recompiled)
   - Database changes: Reset with `docker-compose down -v`

---

## 💡 Pro Tips

1. **Keep Database Between Restarts:**
   ```bash
   # Use restart instead of down/up
   docker-compose restart app
   ```

2. **View Real-time Logs:**
   ```bash
   # See seed messages and API requests
   docker-compose logs -f app
   ```

3. **Access MongoDB Directly:**
   ```bash
   docker-compose exec mongodb mongosh \
     -u admin -p password123 shidhaan_marketplace
   ```

4. **Check Container Health:**
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/health
   ```

---

## 📚 Related Documentation

- `README.md` - Project overview and features
- `DOCKER_SETUP.md` - Detailed Docker configuration
- `DEPLOYMENT.md` - Production deployment guide
- `env.example` - Environment variables reference

---

**Made with ❤️ for blue-collar workers in India** 🇮🇳

