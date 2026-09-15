# Shidhaan Marketplace - Fly.io Deployment Guide

This guide will help you deploy the Shidhaan Blue-collar Marketplace application to Fly.io with MongoDB Atlas database.

## Prerequisites

1. **Fly.io CLI**: Install from [fly.io/docs/hands-on/install-flyctl/](https://fly.io/docs/hands-on/install-flyctl/)
2. **Docker**: Install from [docker.com/get-started](https://www.docker.com/get-started)
3. **MongoDB Atlas Account**: Sign up at [mongodb.com/atlas](https://www.mongodb.com/atlas)
4. **Razorpay Account**: Sign up at [razorpay.com](https://razorpay.com) for payment processing

## Step 1: Database Setup (MongoDB Atlas)

### 1.1 Create MongoDB Atlas Cluster
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a new project called "Shidhaan Marketplace"
3. Create a new cluster (M0 Sandbox is free)
4. Choose a region close to your users (e.g., Mumbai for India)

### 1.2 Configure Database Access
1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Create a user with username `shidhaan_user` and a strong password
4. Set privileges to "Read and write to any database"

### 1.3 Configure Network Access
1. Go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (0.0.0.0/0) for development
4. For production, add specific IP addresses

### 1.4 Get Connection String
1. Go to "Database" in the left sidebar
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string (replace `<password>` with your user password)

## Step 2: Payment Gateway Setup (Razorpay)

### 2.1 Create Razorpay Account
1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Sign up for a new account
3. Complete KYC verification

### 2.2 Get API Keys
1. Go to "Settings" → "API Keys"
2. Generate Test API Keys (for development)
3. Copy the Key ID and Key Secret

## Step 3: Local Development Setup

### 3.1 Environment Configuration
```bash
# Copy the environment template
cp env.example .env

# Edit the .env file with your actual values
nano .env
```

Update the following variables in `.env`:
```env
MONGO_URL=mongodb+srv://shidhaan_user:your_password@cluster0.xxxxx.mongodb.net/
DB_NAME=shidhaan_marketplace
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
RAZORPAY_KEY_ID=rzp_test_your_key_id_here
RAZORPAY_KEY_SECRET=your_razorpay_secret_here
REACT_APP_BACKEND_URL=http://localhost:8000
```

### 3.2 Local Development with Docker
```bash
# Start the application with database
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop the application
docker-compose down
```

### 3.3 Access Local Services
- **Application**: http://localhost:8000
- **MongoDB Express**: http://localhost:8081 (admin/admin123)
- **Admin Login**: http://localhost:8000/admin-login

## Step 4: Fly.io Deployment

### 4.1 Install and Login to Fly.io
```bash
# Install flyctl (if not already installed)
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
fly auth login
```

### 4.2 Initialize Fly.io App
```bash
# Initialize the app (this will create fly.toml)
fly launch --no-deploy

# This will prompt you to:
# - Choose an app name (or use the default)
# - Choose a region (select Mumbai 'bom' for India)
# - Choose not to deploy a database (we're using MongoDB Atlas)
```

### 4.3 Set Environment Variables
```bash
# Set MongoDB connection
fly secrets set MONGO_URL="mongodb+srv://shidhaan_user:your_password@cluster0.xxxxx.mongodb.net/"

# Set database name
fly secrets set DB_NAME="shidhaan_marketplace"

# Set JWT secret (required: without it every restart logs all users out,
# and multiple machines will reject each other's tokens)
fly secrets set JWT_SECRET="$(openssl rand -hex 32)"

# Set Razorpay credentials
fly secrets set RAZORPAY_KEY_ID="rzp_test_your_key_id_here"
fly secrets set RAZORPAY_KEY_SECRET="your_razorpay_secret_here"

# Restrict cross-origin API access to your own domain
fly secrets set CORS_ORIGINS="https://your-app-name.fly.dev"
```

> The frontend is built into the image and calls the API on the same origin, so
> `REACT_APP_BACKEND_URL` does not need to be set for Fly.io.

### 4.3.1 Uploaded Files
Job photos are written to `UPLOAD_DIR` (default `backend/uploads` inside the container).
Without persistent storage they are lost on every deploy or machine restart. Either
attach a Fly volume and point `UPLOAD_DIR` at it (the mount must be writable by the
container's `app` user), or move uploads to object storage such as Tigris/S3.

### 4.4 Deploy to Fly.io
```bash
# Deploy the application
fly deploy

# Check deployment status
fly status

# View logs
fly logs
```

### 4.5 Configure Custom Domain (Optional)
```bash
# Add a custom domain
fly certs add your-domain.com

# Check certificate status
fly certs show your-domain.com
```

## Step 5: Post-Deployment Setup

### 5.1 Create Demo Users
```bash
# SSH into the deployed app
fly ssh console

# Run the demo user creation script
python create_demo_users.py
```

### 5.2 Verify Deployment
1. Visit your app URL: `https://your-app-name.fly.dev`
2. Test the admin login: `https://your-app-name.fly.dev/admin-login`
3. Create test users and jobs
4. Test payment integration

## Step 6: Production Considerations

### 6.1 Security
- Use strong, unique passwords for all services
- Enable MongoDB Atlas IP whitelisting for production
- Use production Razorpay keys
- Set up proper CORS policies
- Enable HTTPS (automatically handled by Fly.io)

### 6.2 Monitoring
```bash
# View app metrics
fly metrics

# Monitor logs
fly logs --follow

# Check app status
fly status
```

### 6.3 Scaling
```bash
# Scale to multiple instances
fly scale count 3

# Scale memory/CPU
fly scale memory 2048
fly scale vm shared-cpu-2x
```

## Step 7: Database Management

### 7.1 MongoDB Atlas Monitoring
1. Go to your MongoDB Atlas dashboard
2. Monitor database performance
3. Set up alerts for unusual activity
4. Configure automated backups

### 7.2 Data Backup
```bash
# Create database backup (run locally with MongoDB tools)
mongodump --uri="mongodb+srv://shidhaan_user:password@cluster0.xxxxx.mongodb.net/shidhaan_marketplace" --out ./backup
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MongoDB Atlas IP whitelist
   - Verify connection string format
   - Ensure database user has correct permissions

2. **Payment Integration Issues**
   - Verify Razorpay API keys
   - Check webhook endpoints
   - Test with Razorpay test cards

3. **Frontend Not Loading**
   - Check REACT_APP_BACKEND_URL environment variable
   - Verify CORS settings in backend
   - Check browser console for errors

4. **Deployment Failures**
   - Check Dockerfile syntax
   - Verify all dependencies are listed
   - Check Fly.io logs: `fly logs`

### Useful Commands

```bash
# View app information
fly info

# SSH into running app
fly ssh console

# View environment variables
fly secrets list

# Restart the app
fly restart

# View app logs
fly logs --follow

# Scale the app
fly scale count 2

# Deploy specific version
fly deploy --image your-image:tag
```

## Support

For issues related to:
- **Fly.io**: Check [Fly.io documentation](https://fly.io/docs/)
- **MongoDB Atlas**: Check [MongoDB Atlas documentation](https://docs.atlas.mongodb.com/)
- **Razorpay**: Check [Razorpay documentation](https://razorpay.com/docs/)

## Application URLs

After successful deployment:
- **Main Application**: `https://your-app-name.fly.dev`
- **Admin Portal**: `https://your-app-name.fly.dev/admin-login`
- **API Documentation**: `https://your-app-name.fly.dev/docs`

## Default Admin Credentials

After running `create_demo_users.py` (login is by phone number):
- **Phone**: 9876543212
- **Password**: admin123

**⚠️ Important**: Change these credentials immediately after deployment!
