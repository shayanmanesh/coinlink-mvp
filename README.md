# CoinLink MVP 🚀

Bitcoin analysis platform with real-time chat interface and trading charts.

## 🌐 Live Production System

- **Frontend**: https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app
- **Backend API**: https://coinlink-backend.onrender.com
- **Health Check**: https://coinlink-backend.onrender.com/health

## ⚡ Features

- **Real-time Bitcoin Chat**: AI-powered analysis and responses
- **Live Trading Charts**: TradingView widget integration
- **WebSocket Communication**: Real-time updates and chat
- **Bitcoin Price Data**: Current price and market information
- **Alert System**: Proactive notifications
- **JWT Authentication**: Secure user sessions

## 🏗️ Architecture

```
Frontend (React/Vercel) ←→ Backend (FastAPI/Render) ←→ Redis (Caching)
```

### Tech Stack
- **Backend**: FastAPI, Python 3.11+, Redis
- **Frontend**: React, TailwindCSS, WebSocket
- **Deployment**: Render.com (backend), Vercel (frontend)
- **Database**: Redis for caching and sessions

## 📋 API Endpoints

### Core Endpoints
```bash
GET  /health                 # System health check
GET  /                       # API information
GET  /api/bitcoin/price      # Current BTC price
GET  /api/crypto/ticker      # Multi-crypto data
POST /api/chat               # Chat interface
GET  /api/alerts             # Active alerts
GET  /api/alerts/history     # Alert history
WS   /ws                     # WebSocket connection
```

### Example API Usage
```bash
# Check system health
curl https://coinlink-backend.onrender.com/health

# Get Bitcoin price
curl https://coinlink-backend.onrender.com/api/bitcoin/price

# Chat with the system
curl -X POST https://coinlink-backend.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Bitcoin price?"}'
```

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/shayanmanesh/coinlink-mvp.git
cd coinlink-mvp

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run backend
cd backend
pip install -r requirements-production.txt
uvicorn api.main_production:app --reload

# Access locally
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Testing Production
```bash
# Test current setup
./test-current-setup.sh

# Update frontend (after backend changes)
./update-frontend-render.sh https://coinlink-backend.onrender.com
```

## 📁 Project Structure

```
coinlink-mvp/
├── backend/
│   ├── api/
│   │   └── main_production.py    # Core FastAPI application
│   ├── auth/
│   │   └── simple_auth.py        # JWT authentication
│   ├── config/
│   │   └── settings.py           # Configuration management
│   └── requirements-production.txt
├── frontend/                     # React app (deployed to Vercel)
├── .env.example                  # Environment variables template
├── CLAUDE.md                     # Agent orchestration guide
├── render.yaml                   # Deployment configuration
├── test-current-setup.sh         # Health check script
└── update-frontend-render.sh     # Frontend update script
```

## 🔧 Configuration

### Environment Variables
```env
# Required for local development
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379
NODE_ENV=development
```

### Production Environment
- **Backend**: Auto-deployed via Render.com on git push
- **Frontend**: Auto-deployed via Vercel on git push
- **Redis**: Managed Redis instance on Render.com

## 🚀 Deployment

### Automatic Deployment
1. **Push to main branch** - Triggers auto-deployment
2. **Render.com** - Builds and deploys backend automatically
3. **Vercel** - Builds and deploys frontend automatically

### Manual Updates
```bash
# Update frontend to use new backend URL
./update-frontend-render.sh [NEW-BACKEND-URL]
```

## 📊 Performance

- **Response Time**: < 500ms for API endpoints
- **Uptime**: 99.9% availability target
- **Scaling**: Auto-scaling enabled on Render.com
- **Caching**: Redis with optimized TTL settings

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **CORS Configuration**: Restricted to allowed origins
- **Environment Variables**: Secure secret management
- **Input Validation**: All API inputs validated
- **Rate Limiting**: Protection against abuse

## 🐛 Troubleshooting

### Common Issues

1. **Backend Health Check Fails**
   ```bash
   curl https://coinlink-backend.onrender.com/health
   # Should return: {"status":"healthy"}
   ```

2. **Frontend Connection Issues**
   ```bash
   curl -I https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app
   # Should return: HTTP 401 (authentication working)
   ```

3. **WebSocket Connection Problems**
   - Check CORS configuration
   - Verify WebSocket URL format: `wss://coinlink-backend.onrender.com/ws`

### Debug Commands
```bash
# Test all endpoints
./test-current-setup.sh

# Check recent deployments
git log --oneline -5

# View production logs
# Login to Render.com dashboard → coinlink-backend → Logs
```

## 📈 Monitoring

- **Health Endpoint**: Automated monitoring via `/health`
- **Error Tracking**: Built-in FastAPI error handling
- **Performance Metrics**: Response time tracking
- **Deployment Status**: Git-triggered deployment logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test locally
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature-name`
6. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

---

**CoinLink MVP** - Production-ready Bitcoin analysis platform
🚀 Live at: https://frontend-kbkzfe7jy-shayans-projects-ede8d66b.vercel.app