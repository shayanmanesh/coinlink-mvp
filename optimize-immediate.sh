#!/bin/bash
# Immediate UI Optimization Script

echo "🚀 IMMEDIATE OPTIMIZATION STARTING"
echo "=================================="

# 1. Fix Redis Connection
echo "📦 Starting Redis..."
redis-server --daemonize yes 2>/dev/null || echo "Redis already running"

# 2. Optimize Frontend Bundle
echo "⚡ Optimizing Frontend Bundle..."
cd frontend
npm run build:analyze 2>/dev/null || npm run build

# 3. Start Backend with Production Settings
echo "🔧 Restarting Backend with optimizations..."
cd ..
pkill -f "uvicorn" 2>/dev/null
python3 -m uvicorn backend.api.main_production:app --host 0.0.0.0 --port 8000 --workers 2 &

echo ""
echo "✅ OPTIMIZATION COMPLETE"
echo "========================"
echo "Frontend: https://frontend-3qc7kuq2w-shayans-projects-ede8d66b.vercel.app"
echo "Backend: http://localhost:8000"
echo "Health: http://localhost:8000/health"