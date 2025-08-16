# 🚀 CoinLink Production Deployment Checklist
## Target: www.coin.link (Railway Platform)
## Date: 2025-08-16

---

## 📋 Pre-Deployment Checklist

### 1. Environment Setup ✅
- [x] Production `.env.production` file created
- [ ] All environment variables set in Railway dashboard
- [ ] Verify all API keys are valid and have correct permissions
- [ ] Generate secure JWT_SECRET and SESSION_SECRET (32+ chars)
- [ ] Configure Redis connection string

### 2. API Keys & Services 🔑
#### Critical (Must Have)
- [ ] **Coinbase API** configured and tested
  - [ ] API Key added to Railway
  - [ ] API Secret added to Railway
  - [ ] Test connection with minimal permissions
- [ ] **Redis** provisioned
  - [ ] Railway Redis addon enabled
  - [ ] Connection string verified
  - [ ] Test read/write operations
- [ ] **JWT/Session Secrets** generated
  - [ ] Use `openssl rand -hex 32` for generation
  - [ ] Different secrets for JWT and sessions

#### Important (Recommended)
- [ ] **Hugging Face** token configured
  - [ ] Token has read access to models
  - [ ] FinBERT model accessible
- [ ] **Sentry** project created
  - [ ] DSN added to environment
  - [ ] Test error captured successfully

#### Optional (Can Add Later)
- [ ] CoinGecko API key
- [ ] Reddit API credentials
- [ ] NewsAPI key
- [ ] Messari API key

### 3. Code & Repository 📝
- [ ] Latest code pushed to main branch
- [ ] No sensitive data in repository
- [ ] `.gitignore` includes all env files
- [ ] Remove all debug/development code
- [ ] Error handling implemented for all API calls

### 4. Backend Configuration 🔧
- [ ] Health check endpoint tested (`/health`)
- [ ] CORS origins configured for production domains
- [ ] Rate limiting configured
- [ ] Logging set to appropriate level (INFO/WARNING)
- [ ] WebSocket connections configured
- [ ] Alert thresholds tuned for production

### 5. Frontend Configuration 🎨
- [ ] Production API URL configured
- [ ] WebSocket URL updated for production
- [ ] Audio files accessible
- [ ] Error boundaries implemented
- [ ] Loading states for all async operations
- [ ] Mobile responsive design tested

### 6. Infrastructure Setup 🏗️
- [ ] Railway project created
- [ ] Custom domain configured (www.coin.link)
- [ ] SSL certificate active
- [ ] GitHub repository connected
- [ ] Automatic deployments configured
- [ ] Environment variables set in Railway

### 7. Docker & Build 🐳
- [ ] Dockerfile tested locally
- [ ] All dependencies in requirements.txt
- [ ] Python version specified
- [ ] Build succeeds without warnings
- [ ] Image size optimized (<500MB preferred)

### 8. Database & Cache 💾
- [ ] Redis connection tested
- [ ] Cache TTL configured appropriately
- [ ] Connection pooling configured
- [ ] Backup strategy documented
- [ ] Data retention policies defined

### 9. Monitoring & Logging 📊
- [x] Logging configuration created
- [x] Health check endpoints implemented
- [ ] Sentry error tracking configured
- [ ] Metrics collection setup
- [ ] Alert notifications configured
- [ ] Log rotation configured

### 10. Security Review 🔒
- [ ] All secrets in environment variables
- [ ] HTTPS enforced
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (if applicable)
- [ ] XSS protection headers set

---

## 🚦 Deployment Steps

### Phase 1: Initial Setup (30 mins)
1. [ ] Login to Railway dashboard
2. [ ] Create new project
3. [ ] Connect GitHub repository
4. [ ] Add Redis database
5. [ ] Configure environment variables
6. [ ] Set custom domain

### Phase 2: First Deploy (15 mins)
7. [ ] Trigger initial deployment
8. [ ] Monitor build logs
9. [ ] Check deployment status
10. [ ] Verify health endpoint

### Phase 3: Testing (30 mins)
11. [ ] Test main page loads
12. [ ] Test WebSocket connection
13. [ ] Test authentication flow
14. [ ] Test alert system
15. [ ] Test API endpoints
16. [ ] Check error tracking

### Phase 4: DNS & SSL (15 mins)
17. [ ] Update DNS records
18. [ ] Wait for propagation
19. [ ] Verify SSL certificate
20. [ ] Test HTTPS redirect

### Phase 5: Final Verification (10 mins)
21. [ ] Full user flow test
22. [ ] Mobile responsiveness check
23. [ ] Performance baseline
24. [ ] Monitor initial traffic

---

## 🔍 Post-Deployment Verification

### Immediate (First Hour)
- [ ] Website accessible via www.coin.link
- [ ] No console errors in browser
- [ ] WebSocket connects successfully
- [ ] Real-time price updates working
- [ ] Alerts triggering correctly
- [ ] No 500 errors in logs

### First 24 Hours
- [ ] Monitor error rate (<1%)
- [ ] Check response times (<500ms p95)
- [ ] Verify cache hit rates (>80%)
- [ ] Review Sentry for any errors
- [ ] Check Redis memory usage
- [ ] Monitor API rate limits

### First Week
- [ ] Review performance metrics
- [ ] Analyze user behavior
- [ ] Optimize slow queries
- [ ] Tune alert thresholds
- [ ] Update documentation
- [ ] Plan next iteration

---

## 🚨 Rollback Plan

If critical issues arise:

1. **Immediate Rollback** (< 5 mins)
   ```bash
   # In Railway dashboard
   # Navigate to Deployments → Select previous deployment → Rollback
   ```

2. **Manual Rollback** (< 10 mins)
   ```bash
   git revert HEAD
   git push origin main
   # Railway will auto-deploy
   ```

3. **Emergency Maintenance Mode**
   - Set environment variable: `MAINTENANCE_MODE=true`
   - Redeploy to show maintenance page

---

## 📞 Emergency Contacts

- **Railway Support**: https://railway.app/help
- **Domain Issues**: Check DNS provider
- **SSL Issues**: Railway dashboard → Settings → Domain
- **Redis Issues**: Railway dashboard → Database → Logs
- **API Issues**: Check respective provider status pages

---

## 📝 Deployment Log

### Deployment #1
- **Date**: ___________
- **Time Started**: ___________
- **Time Completed**: ___________
- **Deployed By**: ___________
- **Version/Commit**: ___________
- **Issues Encountered**: ___________
- **Resolution**: ___________

---

## ✅ Sign-off

### Technical Lead
- [ ] All items reviewed
- [ ] Production ready confirmed
- Name: ___________
- Date: ___________

### DevOps/Platform
- [ ] Infrastructure verified
- [ ] Monitoring configured
- Name: ___________
- Date: ___________

### Product Owner
- [ ] Features tested
- [ ] Go-live approved
- Name: ___________
- Date: ___________

---

## 🎉 Launch Checklist

Once deployed successfully:

1. [ ] Announce on team channels
2. [ ] Update status page
3. [ ] Monitor metrics dashboard
4. [ ] Document lessons learned
5. [ ] Schedule post-mortem (if needed)
6. [ ] Plan celebration! 🥳

---

## 📚 Reference Documents

- [Railway Documentation](https://docs.railway.app)
- [API Keys Documentation](./API_KEYS_DOCUMENTATION.md)
- [Environment Variables](./.env.production)
- [Monitoring Setup](./backend/monitoring/)
- [Deployment Scripts](./deploy-production.sh)

---

**Remember**: Take it slow, verify each step, and don't deploy on Fridays! 🚀