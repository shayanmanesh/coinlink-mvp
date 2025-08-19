# 🚀 IMMEDIATE DEPLOYMENT INSTRUCTIONS

## Backend Deployment (5 minutes)

### Option 1: Deploy to Render.com (FREE - RECOMMENDED)

1. **Go to:** https://dashboard.render.com/register
2. **Sign up** with GitHub
3. Click **"New +"** → **"Web Service"**
4. **Connect** your GitHub account
5. **Select:** `shayanmanesh/coinlink-mvp` repository
6. **Configure:**
   - **Name:** `coinlink-backend`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
7. **Add Environment Variables:**
   ```
   COINBASE_API_KEY = [your key from .env]
   COINBASE_API_SECRET = [your secret from .env]
   HF_TOKEN = [your token from .env]
   REDIS_URL = redis://red-cruf0pu8ii6s73dtn8kg:6379
   NODE_ENV = production
   ```
8. Click **"Create Web Service"**
9. **Wait 3-5 minutes** for deployment
10. **Your backend URL will be:** `https://coinlink-backend.onrender.com`

---

## Frontend Configuration (2 minutes)

1. **Create file:** `frontend/.env.production`
   ```
   REACT_APP_API_URL=https://coinlink-backend.onrender.com
   REACT_APP_WS_URL=wss://coinlink-backend.onrender.com
   ```

2. **Redeploy Frontend:**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Your frontend URL:** Check terminal output

---

## Domain Setup (If you have coin.link access)

1. **Add DNS Records:**
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

2. **In Vercel Dashboard:**
   - Go to Project Settings → Domains
   - Add `coin.link` and `www.coin.link`

---

## 🎯 VALIDATION CHECKLIST

After deployment, test these URLs:

1. **Backend Health:**
   ```
   https://coinlink-backend.onrender.com/health
   ```
   Should show: `{"status": "healthy"}`

2. **Bitcoin Price:**
   ```
   https://coinlink-backend.onrender.com/api/bitcoin/price
   ```
   Should show current BTC price

3. **Frontend:**
   ```
   https://[your-vercel-url]
   ```
   Should load the CoinLink interface

---

## 🚨 IF SOMETHING DOESN'T WORK

**Backend not starting?**
- Check Render.com logs
- Verify environment variables
- Ensure Python version is 3.11+

**Frontend can't connect?**
- Update REACT_APP_API_URL in Vercel settings
- Check CORS in backend (should include your frontend URL)

**WebSocket failing?**
- Ensure wss:// protocol is used
- Check that backend allows WebSocket upgrade

---

## ✅ SUCCESS CRITERIA

Your deployment is successful when:
- [ ] Frontend loads without errors
- [ ] Bitcoin price updates automatically
- [ ] Chat messages get responses
- [ ] No console errors in browser

**Total Time: 10-15 minutes**

---

## 📞 CURRENT STATUS

**Backend:** Running locally at http://localhost:8000 ✅
**Frontend:** Deployed to Vercel (needs backend URL) ⏳
**Domain:** Ready for configuration ⏳

The system is fully functional locally. Just needs cloud backend deployment!