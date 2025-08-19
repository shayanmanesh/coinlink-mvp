# CoinLink MVP - Vercel Deployment Guide
## Cost-Optimized Setup for Product-Market Fit Testing

### 🎯 Architecture Overview
- **Frontend**: Vercel (Free tier: 100GB bandwidth/month)
- **Backend**: Railway/Render (Hobby tier: $5-20/month)
- **Database**: Supabase (Free tier: 500MB, 50K monthly active users)
- **Cache**: Upstash Redis (Free tier: 10K commands/day)
- **Total Cost**: $0-25/month for MVP testing

---

## Phase 1: Database Setup with Supabase (30 minutes)

### 1. Create Supabase Project
```bash
# Visit https://supabase.com and create new project
# Save these credentials:
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Database Schema
```sql
-- Run in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (integrates with Supabase Auth)
CREATE TABLE users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    subscription_tier TEXT DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat history
CREATE TABLE chat_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    message TEXT NOT NULL,
    response TEXT,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rate limiting
CREATE TABLE rate_limits (
    user_identifier TEXT PRIMARY KEY, -- email or IP
    prompt_count INTEGER DEFAULT 0,
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_authenticated BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts history
CREATE TABLE alerts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX idx_rate_limits_reset_at ON rate_limits(reset_at);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);

-- Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own chat history" ON chat_history
    FOR SELECT USING (auth.uid() = user_id);
```

---

## Phase 2: Upstash Redis Setup (15 minutes)

### 1. Create Upstash Account
```bash
# Visit https://upstash.com
# Create Redis database (Free tier)
# Get credentials:
UPSTASH_REDIS_REST_URL=https://xxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AX_xxxxxxxxx
```

### 2. Redis Usage Pattern
```python
# backend/cache/upstash_client.py
import httpx
import json
from typing import Optional, Any

class UpstashRedis:
    def __init__(self, url: str, token: str):
        self.url = url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def get(self, key: str) -> Optional[Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/get/{key}",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                return json.loads(data.get("result")) if data.get("result") else None
            return None
    
    async def set(self, key: str, value: Any, ex: int = None):
        payload = {"value": json.dumps(value)}
        if ex:
            payload["ex"] = ex
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.url}/set/{key}",
                headers=self.headers,
                json=payload
            )
    
    async def incr(self, key: str) -> int:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/incr/{key}",
                headers=self.headers
            )
            return response.json().get("result", 0)
```

---

## Phase 3: Backend Optimization for Railway/Render (1 hour)

### 1. Update Backend Dependencies
```txt
# backend/requirements-production.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
supabase==2.0.0
httpx==0.25.2
pydantic[email]==2.5.0
python-jose[cryptography]==3.3.0
websockets==12.0
slowapi==0.1.9
# Remove heavy ML dependencies for MVP
# Add them back when needed
```

### 2. Supabase Integration
```python
# backend/database/supabase_client.py
from supabase import create_client, Client
from typing import Optional
import os

class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        self.client: Client = create_client(url, key)
    
    async def get_user(self, email: str) -> Optional[dict]:
        response = self.client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    
    async def create_user(self, email: str, user_id: str) -> dict:
        response = self.client.table("users").insert({
            "id": user_id,
            "email": email
        }).execute()
        return response.data[0]
    
    async def save_chat(self, user_id: str, message: str, response: str, context: dict):
        self.client.table("chat_history").insert({
            "user_id": user_id,
            "message": message,
            "response": response,
            "context": context
        }).execute()
    
    async def check_rate_limit(self, identifier: str, is_authenticated: bool = False):
        # Implementation for rate limiting with Supabase
        pass
```

### 3. Simplified API Structure
```python
# backend/api/main_production.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database.supabase_client import SupabaseDB
from cache.upstash_client import UpstashRedis

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.db = SupabaseDB()
    app.state.cache = UpstashRedis(
        os.getenv("UPSTASH_REDIS_REST_URL"),
        os.getenv("UPSTASH_REDIS_REST_TOKEN")
    )
    yield
    # Shutdown
    pass

app = FastAPI(
    title="CoinLink API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://coin.link",
        "https://www.coin.link",
        "https://*.vercel.app",  # For preview deployments
        "http://localhost:3000"  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "coinlink-api"}

@app.post("/api/chat")
async def chat(request: dict):
    # Simplified chat endpoint
    # Focus on core functionality for MVP
    pass
```

---

## Phase 4: Frontend Optimization (30 minutes)

### 1. Environment Configuration
```javascript
// frontend/.env.production
REACT_APP_API_URL=https://coinlink-backend.up.railway.app
REACT_APP_WS_URL=wss://coinlink-backend.up.railway.app
REACT_APP_SUPABASE_URL=https://xxxx.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGc...
```

### 2. Optimize Build
```json
// frontend/package.json
{
  "scripts": {
    "build": "GENERATE_SOURCEMAP=false react-scripts build",
    "build:analyze": "npm run build && npx source-map-explorer 'build/static/js/*.js'"
  }
}
```

### 3. Lazy Loading
```javascript
// frontend/src/App.jsx
import React, { lazy, Suspense } from 'react';

const TradingViewWidget = lazy(() => import('./components/TradingViewWidget'));
const Chat = lazy(() => import('./components/Chat'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      {/* Components */}
    </Suspense>
  );
}
```

---

## Phase 5: Deployment Process (1 hour)

### 1. Railway Backend Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and create project
railway login
railway init

# Set environment variables
railway variables set SUPABASE_URL="https://xxxx.supabase.co"
railway variables set SUPABASE_SERVICE_KEY="eyJhbGc..."
railway variables set UPSTASH_REDIS_REST_URL="https://xxxx.upstash.io"
railway variables set UPSTASH_REDIS_REST_TOKEN="AX_xxx"

# Deploy
railway up
```

### 2. Railway Configuration
```toml
# backend/railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile.production"

[deploy]
startCommand = "uvicorn api.main_production:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30

[environment]
PORT = "8000"
```

### 3. Vercel Frontend Deployment
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
cd frontend
vercel

# Set environment variables
vercel env add REACT_APP_API_URL
vercel env add REACT_APP_WS_URL
vercel env add REACT_APP_SUPABASE_URL
vercel env add REACT_APP_SUPABASE_ANON_KEY

# Deploy to production
vercel --prod
```

---

## Phase 6: Domain Configuration (30 minutes)

### 1. Vercel Domain Setup
```bash
# Add custom domain in Vercel dashboard
vercel domains add coin.link
vercel domains add www.coin.link

# DNS Records (add to your domain registrar)
A     coin.link     76.76.21.21
CNAME www          cname.vercel-dns.com
```

### 2. SSL Configuration
```bash
# Automatic SSL with Vercel
# No action needed - Vercel handles Let's Encrypt certificates
```

---

## Cost Breakdown for MVP

| Service | Free Tier | Paid Tier | MVP Recommendation |
|---------|-----------|-----------|-------------------|
| **Vercel** | 100GB bandwidth/mo | $20/mo Pro | Start Free |
| **Railway** | $5 credit/mo | $5/mo Hobby | Hobby ($5) |
| **Supabase** | 500MB, 50K MAU | $25/mo Pro | Start Free |
| **Upstash** | 10K commands/day | $0.2/100K | Start Free |
| **Domain** | - | $12/year | Required |
| **Total** | **$5-17/mo** | **$62/mo** | **~$17/mo** |

---

## Monitoring & Analytics (Free Tier)

### 1. Vercel Analytics
```javascript
// Automatic with Vercel - no setup needed
// View at: https://vercel.com/[your-project]/analytics
```

### 2. Supabase Dashboard
```bash
# Built-in monitoring at:
https://app.supabase.com/project/[project-id]/editor
```

### 3. Error Tracking with Sentry (Free)
```javascript
// frontend/src/index.js
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1, // 10% sampling for free tier
});
```

---

## Quick Start Commands

```bash
# 1. Clone and prepare
git clone [repo]
cd coinlink-mvp

# 2. Setup Supabase (manual - use web dashboard)
# 3. Setup Upstash (manual - use web dashboard)

# 4. Deploy Backend to Railway
cd backend
railway init
railway up

# 5. Deploy Frontend to Vercel
cd ../frontend
vercel

# 6. Configure domain
vercel domains add coin.link

# Done! Visit https://coin.link
```

---

## MVP Feature Prioritization

### Phase 1 (Week 1) - Core Features Only
- ✅ Real-time Bitcoin price display
- ✅ Basic chat interface
- ✅ Simple authentication
- ✅ Rate limiting (5 free, 50 authenticated)

### Phase 2 (Week 2) - If PMF Validated
- Add TradingView charts
- Implement WebSocket for real-time updates
- Add more crypto tickers

### Phase 3 (Week 3+) - Scale Features
- ML sentiment analysis
- Advanced alerts
- Premium tiers

---

## Rollback Strategy

```bash
# Vercel instant rollback
vercel rollback

# Railway rollback
railway rollback

# Database rollback (Supabase)
# Use point-in-time recovery in dashboard
```

This setup gets you live in under 2 hours with minimal cost while maintaining professional quality and scalability options.