#!/bin/bash
# Complete Railway Deployment Script
# Run this AFTER completing authentication (steps 1-3)

echo "🚂 COMPLETING RAILWAY DEPLOYMENT"
echo "================================="

# Step 4: Deploy Backend
echo "📤 Deploying backend to Railway..."
railway up --environment production --detach

echo "⏳ Waiting for deployment to complete..."
sleep 30

# Step 5: Get Railway URL
echo "🔗 Getting Railway URL..."
RAILWAY_URL=$(railway status | grep -o 'https://[^[:space:]]*' | head -1)

if [ -z "$RAILWAY_URL" ]; then
    echo "❌ Could not retrieve Railway URL. Check deployment status manually."
    exit 1
fi

echo "✅ Backend deployed at: $RAILWAY_URL"

# Step 6: Update Frontend Environment
echo "🔄 Updating frontend environment variables..."
cd frontend

# Set production environment variables for Vercel
echo "Setting REACT_APP_API_URL=$RAILWAY_URL"
echo "$RAILWAY_URL" | vercel env add REACT_APP_API_URL production

WS_URL=$(echo "$RAILWAY_URL" | sed 's/https:/wss:/')/ws
echo "Setting REACT_APP_WS_URL=$WS_URL"
echo "$WS_URL" | vercel env add REACT_APP_WS_URL production

# Redeploy frontend
echo "🚀 Redeploying frontend with new backend URL..."
vercel --prod

cd ..

# Step 7: Verify Deployment
echo "🔍 Verifying deployment..."
sleep 10

echo "Testing backend health..."
curl -s "$RAILWAY_URL/health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Backend Status: {data[\"overall_status\"]}')
    print(f'✅ Redis: {data[\"services\"][\"redis\"][\"status\"]}')
    print(f'✅ API: {data[\"services\"][\"coinbase_api\"][\"status\"]}')
except:
    print('❌ Backend not responding properly')
"

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo "Frontend: https://frontend-3qc7kuq2w-shayans-projects-ede8d66b.vercel.app"
echo "Backend:  $RAILWAY_URL"
echo "Health:   $RAILWAY_URL/health"
echo "API Docs: $RAILWAY_URL/docs"
echo ""
echo "🔧 Next steps:"
echo "1. Test the frontend application"
echo "2. Configure custom domain (optional)"
echo "3. Set up monitoring and alerts"