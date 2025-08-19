# 🚀 RENDER.COM DEPLOYMENT GUIDE - COINLINK BACKEND

## ✅ PREPARATION COMPLETE
- Repository: `https://github.com/shayanmanesh/coinlink-mvp.git`
- Configuration: `render.yaml` configured and committed
- Dependencies: `backend/requirements-production.txt` ready
- Branch: `main` (latest changes pushed)

## 🚀 STEP 1: CREATE RENDER ACCOUNT & SERVICE

### 1.1 Go to Render.com
1. Visit: https://render.com
2. Sign up or log in with GitHub account
3. Connect your GitHub account

### 1.2 Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect repository: `shayanmanesh/coinlink-mvp`
3. Choose branch: `main`

## 🛠️ STEP 2: CONFIGURE SERVICE SETTINGS

### 2.1 Basic Settings
- **Name**: `coinlink-backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r backend/requirements-production.txt`
- **Start Command**: `cd backend && python -m uvicorn api.main_production:app --host 0.0.0.0 --port $PORT`

### 2.2 Environment Variables
Add these environment variables in Render dashboard:

```
NODE_ENV=production
JWT_SECRET_KEY=coinlink-mvp-production-secret-2025
CORS_ORIGINS=https://frontend-3qc7kuq2w-shayans-projects-ede8d66b.vercel.app,https://www.coin.link,https://coin.link
```

### 2.3 Health Check
- **Health Check Path**: `/health`

## 🗄️ STEP 3: ADD REDIS DATABASE

### 3.1 Create Redis Database
1. In Render dashboard, click **"New +"** → **"Redis"**
2. **Name**: `coinlink-redis`
3. **Plan**: Choose **Starter** (free tier)
4. Click **"Create Redis"**

### 3.2 Connect to Web Service
1. Go back to your web service settings
2. In Environment Variables, add:
   - **Key**: `REDIS_URL`
   - **Value**: Copy the **Internal Redis URL** from Redis service

## 🚀 STEP 4: DEPLOY

1. Click **"Create Web Service"**
2. Wait for deployment (usually 3-5 minutes)
3. Monitor build logs for any errors

## ✅ STEP 5: GET SERVICE URL

Once deployed, you'll get a URL like:
`https://coinlink-backend-xxxx.onrender.com`

## 🧪 STEP 6: TEST DEPLOYMENT

Test these endpoints:
```bash
curl https://coinlink-backend-xxxx.onrender.com/health
curl https://coinlink-backend-xxxx.onrender.com/
curl https://coinlink-backend-xxxx.onrender.com/api/alerts
```

Expected responses:
- Health endpoint should return `{"status":"healthy"}`
- Root endpoint should return service info
- Alerts endpoint should return `{"alerts":[]}`

## 🔧 TROUBLESHOOTING

### If Build Fails:
1. Check build logs in Render dashboard
2. Verify `requirements-production.txt` has correct dependencies
3. Ensure Python version compatibility

### If Health Check Fails:
1. Verify health check path is `/health`
2. Check start command is correct
3. Review application logs

### If Redis Connection Fails:
1. Verify Redis URL is correctly set
2. Check Redis service is running
3. Ensure proper network connectivity

## 📞 NEXT STEPS AFTER DEPLOYMENT

Once you have the Render URL (e.g., `https://coinlink-backend-xxxx.onrender.com`):

1. **Test the backend** thoroughly
2. **Update frontend** to use new backend URL
3. **Deploy updated frontend** to Vercel
4. **Verify full-stack** functionality

## 🎯 SUCCESS CRITERIA

✅ Backend accessible at Render URL  
✅ Health check returns "healthy"  
✅ All API endpoints responding  
✅ Redis connection established  
✅ Frontend can connect to backend  

---

**RENDER DEPLOYMENT ESTIMATED TIME: 10-15 minutes**

**BACKUP PLAN**: If Render deployment fails, we can fall back to the working local setup for immediate demo purposes.