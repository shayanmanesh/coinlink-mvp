#!/bin/bash
# Emergency Backend Deployment - Get online NOW

echo "🚨 EMERGENCY BACKEND DEPLOYMENT"
echo "================================"

# Check if backend is running
if lsof -i:8000 > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "🚀 Starting backend..."
    cd /Users/shayanbozorgmanesh/Documents/Parking/coinlink-mvp
    python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
    sleep 5
fi

# Test backend health
echo "🏥 Testing backend health..."
curl -s http://localhost:8000/health | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Backend Status: {data[\"overall_status\"]}')
print(f'   Redis: {data[\"services\"][\"redis\"][\"status\"]}')
print(f'   Coinbase: {data[\"services\"][\"coinbase_api\"][\"status\"]}')
print(f'   WebSocket: {data[\"services\"][\"websocket\"][\"status\"]}')
"

echo ""
echo "🌐 Backend available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"
echo "🔌 WebSocket: ws://localhost:8000/ws"
echo ""
echo "================================"
echo "✅ Backend ready for production!"
echo "================================"