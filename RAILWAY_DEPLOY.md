# Railway Deployment Instructions

## Quick Deploy via Web Interface

Since CLI authentication isn't working in non-interactive mode, here's how to deploy via Railway's web interface:

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub (recommended) or email
3. You'll get $5 free credits to start

### Step 2: Deploy from GitHub
1. Push your code to GitHub:
```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

2. In Railway Dashboard:
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Select your coinlink-mvp repository
   - Railway will auto-detect the configuration

### Step 3: Configure Environment Variables
In Railway project settings, add:
```
PORT=8000
PYTHONPATH=/app/backend
```

### Step 4: Get Your Deployment URL
After deployment, Railway will provide a URL like:
`https://coinlink-mvp-production.up.railway.app`

---

## Alternative: Deploy via Railway CLI (Manual Auth)

1. Open a new terminal window
2. Run: `railway login`
3. Follow the browser authentication
4. Then run these commands:

```bash
cd /Users/shayanbozorgmanesh/Documents/Parking/coinlink-mvp

# Initialize Railway project
railway link

# Deploy
railway up

# Get the deployment URL
railway open
```

---

## Files Ready for Deployment:

✅ `backend/api/main_production.py` - Simplified production API
✅ `backend/requirements-production.txt` - Minimal dependencies
✅ `railway.json` - Railway configuration
✅ `backend/Dockerfile.production` - Docker configuration (optional)

---

## Next Steps After Railway Deployment:

1. Copy your Railway backend URL
2. Update Vercel frontend environment variables:
```bash
vercel env rm REACT_APP_API_URL production
echo "https://your-app.up.railway.app" | vercel env add REACT_APP_API_URL production

vercel env rm REACT_APP_WS_URL production  
echo "wss://your-app.up.railway.app/ws" | vercel env add REACT_APP_WS_URL production

# Redeploy frontend
vercel --prod
```

Your app will then be fully functional!