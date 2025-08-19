# 🚀 Render.com Deployment Guide

## ⚡ Quick Deployment

**Current Status**: ✅ Production system running at https://coinlink-backend.onrender.com

### One-Command Deployment
```bash
# Test current deployment
curl -s https://coinlink-backend.onrender.com/health

# Update frontend after backend changes
./update-frontend-render.sh https://coinlink-backend.onrender.com
```

## 🔧 Manual Deployment Setup

### 1. Create Render Service
1. Go to [Render.com](https://render.com) → Sign in with GitHub
2. **New +** → **Web Service**
3. Connect repository: `shayanmanesh/coinlink-mvp`
4. Branch: `main`

### 2. Configure Service
```yaml
Name: coinlink-backend
Runtime: Python 3
Build Command: pip install -r backend/requirements-production.txt
Start Command: cd backend && python -m uvicorn api.main_production:app --host 0.0.0.0 --port $PORT
Health Check: /health
```

### 3. Environment Variables
```bash
NODE_ENV=production
JWT_SECRET_KEY=coinlink-mvp-production-secret-2025
CORS_ORIGINS=https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app,https://www.coin.link,https://coin.link
```

### 4. Add Redis Database
1. **New +** → **Key Value** (Redis)
2. Name: `coinlink-redis`
3. Plan: **Starter** (free)
4. Add to web service environment: `REDIS_URL=[auto-generated]`

## 🧪 Deployment Testing

### Essential Tests
```bash
# 1. Health check
curl https://coinlink-backend.onrender.com/health
# Expected: {"status":"healthy"}

# 2. API endpoints
curl https://coinlink-backend.onrender.com/api/bitcoin/price
curl https://coinlink-backend.onrender.com/api/alerts

# 3. Frontend connectivity
curl -I https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app
# Expected: HTTP 401 (auth working)
```

### Automated Testing
```bash
# Run comprehensive test
./test-current-setup.sh
```

## 🔄 Update Workflow

### Backend Updates
1. **Edit Code**: Modify `backend/api/main_production.py`
2. **Commit**: `git add . && git commit -m "Update: description"`
3. **Deploy**: `git push` (auto-deploys to Render)
4. **Verify**: Test endpoints after 2-3 minutes

### Frontend Updates
```bash
# After backend URL changes
./update-frontend-render.sh [NEW-RENDER-URL]
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Build Failures
```bash
# Check build logs in Render dashboard
# Verify: backend/requirements-production.txt exists
# Check: Python version compatibility
```

#### Health Check Failures
```bash
# Verify start command
# Check: /health endpoint exists
# Review: application logs in dashboard
```

#### Redis Connection Issues
```bash
# Verify REDIS_URL environment variable
# Check: Redis service status
# Ensure: Proper network connectivity
```

### Debug Commands
```bash
# Check deployment status
git log --oneline -3

# Test specific endpoints
curl -s https://coinlink-backend.onrender.com/health | jq
curl -s https://coinlink-backend.onrender.com/api/connections

# View logs: Render Dashboard → Service → Logs
```

## 📊 Performance Monitoring

### Key Metrics
- **Build Time**: ~2-3 minutes
- **Health Check**: < 200ms response
- **API Response**: < 500ms average
- **Uptime**: 99.9% target

### Monitoring Commands
```bash
# Check response times
time curl -s https://coinlink-backend.onrender.com/health

# Monitor connections
curl -s https://coinlink-backend.onrender.com/api/connections
```

## 🔐 Production Configuration

### Current Setup
```yaml
Service URL: https://coinlink-backend.onrender.com
Frontend URL: https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app
Redis: coinlink-redis (Starter plan)
Auto-deploy: Enabled on main branch
```

### Security Settings
- **CORS**: Restricted to frontend domains
- **JWT**: Persistent secret key
- **Environment**: Production variables secured
- **Health Check**: Public endpoint for monitoring

## 🎯 Success Checklist

- ✅ Backend accessible at Render URL
- ✅ Health endpoint returns `{"status":"healthy"}`
- ✅ All API endpoints responding correctly
- ✅ Redis connection established
- ✅ Frontend connects to backend successfully
- ✅ WebSocket connections working
- ✅ Auto-deployment triggered on git push

## 📞 Quick Reference

```bash
# Production URLs
Backend: https://coinlink-backend.onrender.com
Frontend: https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app

# Essential Commands
curl -s https://coinlink-backend.onrender.com/health    # Health check
./test-current-setup.sh                                 # Full test
./update-frontend-render.sh [URL]                       # Update frontend

# Deployment
git push                                                 # Auto-deploy
# Wait 2-3 minutes → Test endpoints
```

---

**Deployment Time**: 15 minutes (setup) | 3 minutes (updates)
**Success Rate**: 99% (Render.com is highly reliable for Python apps)