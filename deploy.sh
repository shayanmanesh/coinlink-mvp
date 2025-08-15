#!/bin/bash

# CoinLink MVP Deployment Script
# Deploys to Vercel (frontend) and Railway (backend)

set -e

echo "🚀 Starting CoinLink MVP Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required CLIs are installed
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v vercel &> /dev/null; then
        echo -e "${RED}❌ Vercel CLI not found${NC}"
        echo "Install with: npm install -g vercel"
        exit 1
    fi
    
    if ! command -v railway &> /dev/null; then
        echo -e "${RED}❌ Railway CLI not found${NC}"
        echo "Install with: npm install -g @railway/cli"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements met${NC}"
}

# Deploy backend to Railway
deploy_backend() {
    echo -e "\n${YELLOW}🔧 Deploying Backend to Railway...${NC}"
    cd backend
    
    # Check if railway.toml exists
    if [ ! -f "railway.toml" ]; then
        echo "Creating railway.toml..."
        cat > railway.toml << 'EOF'
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile.production"

[deploy]
startCommand = "uvicorn api.main_production:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
EOF
    fi
    
    # Deploy to Railway
    railway up
    
    # Get the deployment URL
    BACKEND_URL=$(railway status --json | grep -o '"url":"[^"]*' | grep -o '[^"]*$')
    echo -e "${GREEN}✅ Backend deployed to: https://$BACKEND_URL${NC}"
    
    cd ..
    return 0
}

# Deploy frontend to Vercel
deploy_frontend() {
    echo -e "\n${YELLOW}🎨 Deploying Frontend to Vercel...${NC}"
    cd frontend
    
    # Build the application
    echo "Building React app..."
    npm run build
    
    # Deploy to Vercel
    vercel --prod
    
    echo -e "${GREEN}✅ Frontend deployed to Vercel${NC}"
    
    cd ..
    return 0
}

# Main deployment flow
main() {
    check_requirements
    
    # Ask for deployment confirmation
    echo -e "\n${YELLOW}This will deploy:${NC}"
    echo "  • Frontend to Vercel"
    echo "  • Backend to Railway"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 1
    fi
    
    # Deploy backend first (to get URL for frontend)
    deploy_backend
    
    # Deploy frontend
    deploy_frontend
    
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Configure your domain in Vercel dashboard"
    echo "2. Update environment variables in both services"
    echo "3. Test the live application"
    echo ""
    echo "Vercel Dashboard: https://vercel.com/dashboard"
    echo "Railway Dashboard: https://railway.app/dashboard"
}

# Run main function
main