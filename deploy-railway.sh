#!/bin/bash

# CoinLink Railway Deployment Script
# Production deployment to www.coin.link
# Created: 2025-01-16

set -e

echo "======================================"
echo "   CoinLink Railway Deployment"
echo "   Target: www.coin.link"
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Error: Railway CLI is not installed${NC}"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

# Function to check Railway login status
check_railway_auth() {
    echo -e "${YELLOW}Checking Railway authentication...${NC}"
    if ! railway whoami &> /dev/null; then
        echo -e "${RED}Error: Not logged in to Railway${NC}"
        echo "Please run: railway login"
        exit 1
    fi
    echo -e "${GREEN}✓ Railway authentication verified${NC}"
}

# Function to validate environment
validate_environment() {
    echo -e "${YELLOW}Validating deployment environment...${NC}"
    
    # Check required files
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}Error: Dockerfile not found${NC}"
        exit 1
    fi
    
    if [ ! -f "railway.json" ]; then
        echo -e "${RED}Error: railway.json not found${NC}"
        exit 1
    fi
    
    if [ ! -f "backend/api/main_production.py" ]; then
        echo -e "${RED}Error: Production API file not found${NC}"
        exit 1
    fi
    
    if [ ! -f "backend/requirements-production.txt" ]; then
        echo -e "${RED}Error: Production requirements file not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All required files present${NC}"
}

# Function to run pre-deployment tests
run_tests() {
    echo -e "${YELLOW}Running pre-deployment checks...${NC}"
    
    # Test Docker build locally (optional)
    if command -v docker &> /dev/null; then
        echo "Testing Docker build..."
        docker build -t coinlink-test . --quiet
        echo -e "${GREEN}✓ Docker build successful${NC}"
    else
        echo -e "${YELLOW}⚠ Docker not available, skipping build test${NC}"
    fi
}

# Function to deploy to Railway
deploy_to_railway() {
    echo -e "${YELLOW}Starting Railway deployment...${NC}"
    
    # Get deployment environment
    read -p "Deploy to which environment? (production/staging) [production]: " ENV
    ENV=${ENV:-production}
    
    if [ "$ENV" == "production" ]; then
        echo -e "${RED}⚠ WARNING: Deploying to PRODUCTION${NC}"
        read -p "Are you sure you want to deploy to production? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Deploy using Railway CLI
    echo -e "${YELLOW}Deploying to Railway (environment: $ENV)...${NC}"
    
    if [ "$ENV" == "production" ]; then
        railway up --environment production
    else
        railway up --environment staging
    fi
    
    echo -e "${GREEN}✓ Deployment initiated successfully${NC}"
}

# Function to monitor deployment
monitor_deployment() {
    echo -e "${YELLOW}Monitoring deployment status...${NC}"
    echo "You can monitor the deployment at: https://railway.app"
    echo ""
    echo "To view logs, run:"
    echo "  railway logs"
    echo ""
    echo "To check deployment status:"
    echo "  railway status"
}

# Function to verify deployment
verify_deployment() {
    echo -e "${YELLOW}Verifying deployment...${NC}"
    
    # Wait for deployment to be ready
    echo "Waiting for deployment to be ready (this may take a few minutes)..."
    sleep 30
    
    # Check health endpoint
    HEALTH_URL="https://coinlink-mvp-production.up.railway.app/health"
    
    echo "Checking health endpoint: $HEALTH_URL"
    if curl -f -s "$HEALTH_URL" > /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        curl -s "$HEALTH_URL" | python3 -m json.tool
    else
        echo -e "${YELLOW}⚠ Health check pending or failed${NC}"
        echo "The deployment may still be in progress. Check Railway dashboard."
    fi
}

# Function to display post-deployment instructions
post_deployment_instructions() {
    echo ""
    echo "======================================"
    echo -e "${GREEN}   Deployment Complete!${NC}"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Configure custom domain at: https://railway.app/dashboard"
    echo "2. Set environment variables in Railway dashboard"
    echo "3. Monitor application logs: railway logs --tail"
    echo "4. Access your application at the Railway-provided URL"
    echo ""
    echo "Important URLs:"
    echo "- Railway Dashboard: https://railway.app"
    echo "- Custom Domain Target: www.coin.link"
    echo "- Frontend: https://frontend-oyhz3vvwf-shayans-projects-ede8d66b.vercel.app"
    echo ""
    echo "Environment variables to configure in Railway:"
    echo "- SUPABASE_URL"
    echo "- SUPABASE_ANON_KEY"
    echo "- SUPABASE_SERVICE_KEY (if needed)"
    echo "- Any API keys for crypto data providers"
    echo ""
}

# Main deployment flow
main() {
    echo "Starting CoinLink Railway deployment process..."
    echo ""
    
    # Step 1: Check authentication
    check_railway_auth
    
    # Step 2: Validate environment
    validate_environment
    
    # Step 3: Run tests (optional)
    read -p "Run pre-deployment tests? (y/n) [y]: " RUN_TESTS
    RUN_TESTS=${RUN_TESTS:-y}
    if [ "$RUN_TESTS" == "y" ]; then
        run_tests
    fi
    
    # Step 4: Deploy
    deploy_to_railway
    
    # Step 5: Monitor
    monitor_deployment
    
    # Step 6: Verify
    read -p "Verify deployment? (y/n) [y]: " VERIFY
    VERIFY=${VERIFY:-y}
    if [ "$VERIFY" == "y" ]; then
        verify_deployment
    fi
    
    # Step 7: Post-deployment instructions
    post_deployment_instructions
}

# Run main function
main "$@"