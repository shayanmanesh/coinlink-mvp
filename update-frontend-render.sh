#!/bin/bash
# Update frontend to use Render.com backend URL
# Usage: ./update-frontend-render.sh https://your-render-url.onrender.com

if [ -z "$1" ]; then
    echo "❌ Error: Please provide the Render backend URL"
    echo "Usage: ./update-frontend-render.sh https://coinlink-backend-xxxx.onrender.com"
    exit 1
fi

RENDER_URL=$1
echo "🔄 Updating frontend to use Render backend: $RENDER_URL"

# Update vercel.json to use Render backend
cd frontend

# Update environment variables for Vercel
echo "📝 Setting Vercel environment variables..."

# Set production API URL
echo "$RENDER_URL" | vercel env add REACT_APP_API_URL production --yes

# Set WebSocket URL (convert https to wss)
WS_URL=$(echo "$RENDER_URL" | sed 's/https:/wss:/')/ws
echo "$WS_URL" | vercel env add REACT_APP_WS_URL production --yes

# Redeploy frontend with new backend URL
echo "🚀 Redeploying frontend with Render backend..."
vercel --prod --yes

cd ..

echo ""
echo "✅ Frontend updated and redeployed!"
echo "🌐 Frontend: https://frontend-3qc7kuq2w-shayans-projects-ede8d66b.vercel.app"
echo "🔗 Backend: $RENDER_URL"
echo ""
echo "🧪 Test the full stack:"
echo "1. Visit the frontend URL"
echo "2. Check if Bitcoin data loads"
echo "3. Test chat functionality"
echo "4. Verify WebSocket connection"