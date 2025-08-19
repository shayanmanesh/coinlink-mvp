# Railway Deployment Checklist for CoinLink

## Pre-Deployment Checklist

### 1. Code Preparation ✅
- [x] Dockerfile configured and tested
- [x] railway.json with production settings
- [x] Production API endpoint ready (main_production.py)
- [x] Requirements file optimized (requirements-production.txt)
- [x] CORS settings updated for production domains

### 2. Railway Setup
- [ ] Railway CLI installed (`npm install -g @railway/cli`)
- [ ] Logged in to Railway (`railway login`)
- [ ] Project created in Railway dashboard
- [ ] Custom domain configured (www.coin.link)

### 3. Environment Variables
- [ ] SUPABASE_URL configured
- [ ] SUPABASE_ANON_KEY configured
- [ ] JWT_SECRET_KEY generated and set
- [ ] FRONTEND_URL set to production URL
- [ ] API keys for crypto data providers added

### 4. Deployment Script
- [x] deploy-railway.sh created and executable
- [ ] Script tested locally
- [ ] Railway project linked

## Deployment Steps

### Step 1: Initial Setup
```bash
# Install Railway CLI if not installed
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project (if not already linked)
railway link
```

### Step 2: Configure Environment
```bash
# Set critical environment variables
railway variables set SUPABASE_URL=your_url
railway variables set SUPABASE_ANON_KEY=your_key
railway variables set JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### Step 3: Deploy
```bash
# Run deployment script
./deploy-railway.sh

# Or deploy directly
railway up --environment production
```

### Step 4: Verify Deployment
```bash
# Check logs
railway logs --tail

# Test health endpoint
curl https://coinlink-mvp-production.up.railway.app/health

# Monitor metrics
railway status
```

### Step 5: Configure Custom Domain
1. Go to Railway dashboard
2. Select your service
3. Go to Settings → Domains
4. Add custom domain: www.coin.link
5. Update DNS records as instructed

## Post-Deployment Checklist

### Immediate Tasks
- [ ] Health check passing
- [ ] WebSocket connections working
- [ ] Frontend can connect to backend
- [ ] CORS not blocking requests
- [ ] API endpoints responding

### Within 1 Hour
- [ ] Custom domain DNS propagated
- [ ] SSL certificate active
- [ ] Rate limiting working
- [ ] Error logging functional
- [ ] Basic monitoring setup

### Within 24 Hours
- [ ] Full integration test completed
- [ ] Performance baseline established
- [ ] Backup strategy confirmed
- [ ] Scaling rules configured
- [ ] Alert notifications setup

## Quick Commands Reference

```bash
# Deploy to production
railway up --environment production

# View logs
railway logs --tail

# Check deployment status
railway status

# Open Railway dashboard
railway open

# Rollback if needed
railway down

# Connect to production shell (if needed)
railway run bash

# Set multiple variables from file
railway variables set --from-file .env.production
```

## Emergency Procedures

### If Deployment Fails
1. Check logs: `railway logs`
2. Verify environment variables
3. Check Dockerfile build locally
4. Review railway.json syntax
5. Contact Railway support if infrastructure issue

### If Site Goes Down
1. Check Railway status page
2. Review recent deployments
3. Check health endpoint directly
4. Review error logs
5. Rollback if necessary: `railway down`

### Quick Rollback
```bash
# List deployments
railway deployments

# Rollback to previous version
railway rollback [deployment-id]
```

## Contact Information

- Railway Support: https://railway.app/help
- Railway Status: https://status.railway.app
- CoinLink Team: [Your contact info]

## Final Verification URLs

After successful deployment:
- API Health: https://www.coin.link/health
- API Docs: https://www.coin.link/docs
- WebSocket Test: wss://www.coin.link/ws
- Frontend: https://www.coin.link

---

**Last Updated:** 2025-01-16
**Target Launch:** Within 90 minutes
**Production URL:** www.coin.link