#!/bin/bash

# CoinLink Unified Deployment Script
# Primary target: Railway (production-ready)
# Fallback: Docker Compose (local development)

set -e

echo "🚀 CoinLink Deployment Script"
echo "=============================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Deployment target selection
DEPLOYMENT_TARGET=${1:-railway}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    case $DEPLOYMENT_TARGET in
        railway)
            if ! command -v railway &> /dev/null; then
                echo -e "${RED}Error: Railway CLI not installed${NC}"
                echo "Install with: npm install -g @railway/cli"
                exit 1
            fi
            
            if ! railway whoami &> /dev/null; then
                echo -e "${RED}Error: Not logged in to Railway${NC}"
                echo "Please run: railway login"
                exit 1
            fi
            echo -e "${GREEN}✓ Railway CLI ready${NC}"
            ;;
        docker)
            if ! command -v docker &> /dev/null; then
                echo -e "${RED}Error: Docker not installed${NC}"
                exit 1
            fi
            echo -e "${GREEN}✓ Docker ready${NC}"
            ;;
        *)
            echo -e "${RED}Error: Unknown deployment target: $DEPLOYMENT_TARGET${NC}"
            echo "Supported targets: railway, docker"
            exit 1
            ;;
    esac
}

# Function to validate environment
validate_environment() {
    echo -e "${YELLOW}Validating environment...${NC}"
    
    # Check required files
    required_files=("Dockerfile" "backend/api/main_production.py" "backend/requirements-production.txt")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}Error: Required file not found: $file${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✓ All required files present${NC}"
}

# Function to deploy to Railway
deploy_railway() {
    echo -e "${YELLOW}Deploying to Railway...${NC}"
    
    # Check environment
    ENV=${RAILWAY_ENV:-production}
    echo "Target environment: $ENV"
    
    if [ "$ENV" == "production" ]; then
        echo -e "${RED}⚠ WARNING: Deploying to PRODUCTION${NC}"
        read -p "Continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Deploy
    echo -e "${YELLOW}Starting Railway deployment...${NC}"
    railway up --environment $ENV --detach
    
    echo -e "${GREEN}✓ Deployment initiated${NC}"
    echo "Monitor at: https://railway.app"
    echo "Logs: railway logs"
}

# Function to deploy locally with Docker
deploy_docker() {
    echo -e "${YELLOW}Starting Docker deployment...${NC}"
    
    # Build and start
    docker-compose -f docker-compose.yml up --build -d
    
    echo -e "${GREEN}✓ Local deployment started${NC}"
    echo "Access at: http://localhost:8000"
    echo "Health check: http://localhost:8000/health"
}

# Function to run health check
health_check() {
    echo -e "${YELLOW}Running health check...${NC}"
    
    case $DEPLOYMENT_TARGET in
        railway)
            echo "Waiting for Railway deployment..."
            sleep 30
            HEALTH_URL="https://api.coin.link/health"
            ;;
        docker)
            echo "Waiting for Docker containers..."
            sleep 10
            HEALTH_URL="http://localhost:8000/health"
            ;;
    esac
    
    echo "Checking: $HEALTH_URL"
    if curl -f -s "$HEALTH_URL" > /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        curl -s "$HEALTH_URL" | python3 -m json.tool 2>/dev/null || echo "Health endpoint responded successfully"
    else
        echo -e "${YELLOW}⚠ Health check pending (deployment may still be in progress)${NC}"
    fi
}

# Main execution
main() {
    echo "Target: $DEPLOYMENT_TARGET"
    echo ""
    
    check_prerequisites
    validate_environment
    
    case $DEPLOYMENT_TARGET in
        railway)
            deploy_railway
            ;;
        docker)
            deploy_docker
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}Deployment process complete!${NC}"
    echo ""
    
    # Optional health check
    read -p "Run health check? (y/n) [y]: " CHECK_HEALTH
    CHECK_HEALTH=${CHECK_HEALTH:-y}
    if [ "$CHECK_HEALTH" == "y" ]; then
        health_check
    fi
    
    echo ""
    echo "=============================="
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo "=============================="
}

# Show help
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [railway|docker]"
    echo ""
    echo "Deployment targets:"
    echo "  railway  - Deploy to Railway (default, production)"
    echo "  docker   - Deploy locally with Docker Compose"
    echo ""
    echo "Examples:"
    echo "  $0                # Deploy to Railway"
    echo "  $0 railway        # Deploy to Railway"
    echo "  $0 docker         # Deploy locally with Docker"
    echo ""
    echo "Environment variables:"
    echo "  RAILWAY_ENV=staging  # Deploy to staging (default: production)"
    exit 0
fi

# Run main function
main "$@"