# CoinLink MVP - Agent Orchestration Guide

## 🎯 System Overview

**Production System**: Bitcoin analysis platform with real-time chat and trading charts
- **Backend**: https://coinlink-backend.onrender.com (FastAPI + Redis)
- **Frontend**: https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app (React)
- **Deployment**: Auto-deploy on git push to main branch via Render.com

## 🤖 Agent Task Patterns

### 1. Health Check Pattern
**Always start tasks with system verification**:
```bash
curl -s https://coinlink-backend.onrender.com/health
```
Expected response: `{"status":"healthy"}`

### 2. Parallel Execution Strategy
**For independent operations, use parallel tool calls**:
- Read multiple files simultaneously
- Test multiple endpoints concurrently
- Deploy and test in parallel workflows

### 3. Error Recovery Protocol
**If production issues detected**:
1. Check recent commits: `git log --oneline -5`
2. Test specific endpoints: `/health`, `/api/alerts`, `/api/bitcoin/price`
3. Verify frontend connectivity: HTTP status should be 401 (auth working)

## 🔄 Core Workflows

### Deployment Workflow
1. **Code Changes**: Modify `backend/api/main_production.py`
2. **Commit**: Use conventional commit messages
3. **Auto-Deploy**: Render.com deploys automatically on push
4. **Verify**: Test health endpoint after 2-3 minutes

### Frontend Update Workflow
1. **Get Render URL**: Current is `https://coinlink-backend.onrender.com`
2. **Update Frontend**: `./update-frontend-render.sh [RENDER-URL]`
3. **Verify**: Frontend should connect to new backend

### Testing Workflow
1. **Health Check**: `curl backend/health`
2. **API Endpoints**: Test `/api/alerts`, `/api/bitcoin/price`
3. **Frontend**: Check HTTP status (401 = auth working)

## 📁 Key Files & Their Purposes

### Core Production Files
- `backend/api/main_production.py` - Main API with all endpoints
- `backend/auth/simple_auth.py` - JWT authentication system
- `backend/config/settings.py` - Environment configuration
- `render.yaml` - Deployment configuration

### Scripts
- `test-current-setup.sh` - Verify system health
- `update-frontend-render.sh` - Update frontend backend URL

### Configuration
- `.env.example` - Environment variables template
- `backend/requirements-production.txt` - Python dependencies

## 🛠️ Agent Instructions

### When Making API Changes
1. **Edit**: `backend/api/main_production.py`
2. **Test Locally**: Verify endpoints work
3. **Commit**: Push changes trigger auto-deploy
4. **Verify**: Test production endpoints

### When Debugging Issues
1. **Check Health**: Production health endpoint first
2. **Review Logs**: Check Render.com dashboard logs
3. **Test Endpoints**: Use curl to verify specific endpoints
4. **Verify Frontend**: Check frontend can reach backend

### When Deploying Updates
**Never modify these files** (production-critical):
- `render.yaml` (unless deployment config changes needed)
- `backend/requirements-production.txt` (unless new dependencies)
- Environment variables in Render dashboard

**Always modify through git workflow**:
- Make changes → commit → push → auto-deploy → verify

## 🚨 Critical Production Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /` - API info and status
- `GET /api/connections` - WebSocket connection count

### Bitcoin Data
- `GET /api/bitcoin/price` - Current BTC price (mock data)
- `GET /api/crypto/ticker` - Multi-crypto ticker

### Chat & Alerts
- `POST /api/chat` - Chat endpoint (REST fallback)
- `GET /api/alerts` - Active alerts
- `GET /api/alerts/history` - Alert history

### WebSocket
- `WS /ws` - Real-time chat and updates

## 📊 Performance Standards

### Response Time Targets
- Health endpoint: < 200ms
- API endpoints: < 500ms
- WebSocket connection: < 1s

### System Requirements
- Backend: Python 3.11+, FastAPI, Redis connection
- Frontend: React, WebSocket support
- Deployment: Render.com auto-scaling

## 🔧 Quick Commands Reference

```bash
# Check production health
curl -s https://coinlink-backend.onrender.com/health

# Test all endpoints
./test-current-setup.sh

# Update frontend after backend changes
./update-frontend-render.sh https://coinlink-backend.onrender.com

# Local development
cd backend && uvicorn api.main_production:app --reload
```

## 🎯 Agent Success Criteria

1. **Always verify production health before major changes**
2. **Use parallel execution for independent operations**
3. **Test endpoints after any deployment**
4. **Follow git workflow for all production changes**
5. **Maintain clean, focused commit messages**

---

**Production MVP Focus**: Keep all agent tasks focused on the live production system. Avoid experimental features or complex architectures not reflected in the current production deployment.