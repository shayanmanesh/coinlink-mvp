#!/bin/bash

# OPUS-4 SWARM LAUNCHER FOR COINLINK-MVP
# Launches multiple Claude Opus instances in parallel for rapid development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/shayanbozorgmanesh/Documents/Parking/coinlink-mvp"
SWARM_STATE="$PROJECT_ROOT/swarm-state"
LOGS_DIR="$PROJECT_ROOT/swarm-logs"

# Create necessary directories
mkdir -p "$SWARM_STATE" "$LOGS_DIR"

echo -e "${BLUE}🚀 OPUS-4 SWARM LAUNCHER - COINLINK-MVP DEPLOYMENT${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to launch an agent
launch_agent() {
    local agent_id=$1
    local agent_role=$2
    local agent_task=$3
    
    echo -e "${GREEN}[SPAWNING]${NC} Agent: $agent_id - $agent_role"
    
    # Create agent-specific prompt file
    cat > "$SWARM_STATE/$agent_id.prompt" << EOF
You are Agent $agent_id, specialized in $agent_role.

PROJECT: Coinlink-MVP - Crypto monitoring and alert system
DEPLOYMENT TARGET: www.coin.link (Railway)
TIMELINE: Production deployment in next 90 minutes

YOUR SPECIFIC TASK:
$agent_task

IMPORTANT INSTRUCTIONS:
1. Focus ONLY on your assigned task
2. Write production-ready code
3. Create/modify files directly in the project
4. Test your changes if possible
5. Report completion status clearly
6. Coordinate with other agents via swarm-state files

PROJECT PATH: $PROJECT_ROOT

When complete, write a summary to: $SWARM_STATE/$agent_id.complete
EOF

    # Launch Claude in tmux session
    tmux new-session -d -s "$agent_id" -c "$PROJECT_ROOT" \
        "claude < '$SWARM_STATE/$agent_id.prompt' 2>&1 | tee '$LOGS_DIR/$agent_id.log'"
}

# Function to check agent status
check_status() {
    echo -e "\n${BLUE}📊 SWARM STATUS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    for session in $(tmux ls 2>/dev/null | cut -d: -f1 | grep "^agent-"); do
        if [ -f "$SWARM_STATE/$session.complete" ]; then
            echo -e "${GREEN}✓${NC} $session: COMPLETE"
        else
            echo -e "${YELLOW}⚡${NC} $session: IN PROGRESS"
        fi
    done
}

# Kill existing swarm sessions
echo -e "${YELLOW}Cleaning up existing swarm sessions...${NC}"
tmux ls 2>/dev/null | grep "^agent-" | cut -d: -f1 | xargs -I {} tmux kill-session -t {} 2>/dev/null || true

# DEFINE AGENT TASKS
echo -e "\n${BLUE}📋 DEFINING SWARM AGENTS${NC}"

# FRONTEND AGENTS (3)
launch_agent "agent-frontend-1" "Frontend Architecture" \
"Fix the hardcoded localhost URL in frontend/src/components/QuickAuth.jsx
Replace with environment variable: process.env.REACT_APP_API_URL
Ensure all API calls use the centralized api.js service"

launch_agent "agent-frontend-2" "Frontend Build Optimization" \
"Create production build configuration:
1. Run npm run build in frontend/
2. Optimize bundle size
3. Enable code splitting
4. Configure environment variables for production
5. Test the production build"

launch_agent "agent-frontend-3" "Frontend WebSocket" \
"Verify WebSocket connections work with environment variables:
1. Check frontend/src/services/api.js WebSocket configuration
2. Ensure reconnection logic is robust
3. Add connection status indicator
4. Test with production URLs"

# BACKEND AGENTS (3)
launch_agent "agent-backend-1" "Backend Production Config" \
"Prepare backend for production:
1. Review backend/api/main_production.py
2. Ensure all environment variables are used (no hardcoded values)
3. Add proper error handling and logging
4. Configure CORS for coin.link domain"

launch_agent "agent-backend-2" "Backend API Security" \
"Secure the API endpoints:
1. Add rate limiting to all endpoints
2. Validate all input data
3. Ensure API keys are properly loaded from environment
4. Add request logging for monitoring"

launch_agent "agent-backend-3" "Backend Performance" \
"Optimize backend performance:
1. Ensure Redis caching is properly configured
2. Add connection pooling for external APIs
3. Optimize database queries if any
4. Add health check endpoint monitoring"

# DEPLOYMENT AGENTS (2)
launch_agent "agent-deploy-1" "Railway Configuration" \
"Prepare Railway deployment:
1. Verify Dockerfile configuration
2. Update railway.json with production settings
3. Create deployment script
4. Document environment variables needed"

launch_agent "agent-deploy-2" "Environment Setup" \
"Setup production environment:
1. Create production .env.production file
2. Document all required API keys
3. Setup monitoring and logging
4. Create deployment checklist"

# TESTING AGENTS (2)
launch_agent "agent-test-1" "Integration Testing" \
"Test critical user flows:
1. Test authentication flow
2. Test WebSocket real-time updates
3. Test alert creation and notifications
4. Test API endpoints with curl commands"

launch_agent "agent-test-2" "Load Testing" \
"Performance validation:
1. Test WebSocket with multiple connections
2. Test API rate limits
3. Verify Redis caching works
4. Check memory usage under load"

echo -e "\n${GREEN}✨ SWARM LAUNCHED!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "10 Opus-4 agents now working in parallel!"
echo -e "\nMonitor agents with:"
echo -e "  ${YELLOW}tmux ls${NC}                    - List all agents"
echo -e "  ${YELLOW}tmux attach -t agent-XXX${NC}   - Watch specific agent"
echo -e "  ${YELLOW}./swarm-launcher.sh status${NC}  - Check completion status"
echo -e "\nLogs available in: ${BLUE}$LOGS_DIR${NC}"

# Handle status check command
if [ "$1" == "status" ]; then
    check_status
    exit 0
fi

# Show initial status
sleep 2
check_status

echo -e "\n${YELLOW}⏱️  Estimated completion: 15-30 minutes${NC}"
echo -e "${GREEN}💡 TIP:${NC} Run ${YELLOW}./swarm-launcher.sh status${NC} to check progress"