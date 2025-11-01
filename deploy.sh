#!/bin/bash
# Deployment script for Goal Tracker Backend

set -e

echo "🚀 Starting Goal Tracker Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/goal-tracker/backend"
SERVICE_NAME="goal-tracker-backend"
USER="www-data"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}Error: Project directory not found: $PROJECT_DIR${NC}"
    exit 1
}

echo -e "${YELLOW}📦 Installing dependencies...${NC}"
export PATH="$HOME/.local/bin:$PATH"
# Poetry 2.x uses --without dev, fallback to --no-dev for older versions
poetry install --without dev 2>/dev/null || poetry install --no-dev 2>/dev/null || poetry install || {
    echo -e "${RED}Error: Failed to install dependencies${NC}"
    exit 1
}

echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
poetry run alembic upgrade head || {
    echo -e "${RED}Error: Database migration failed${NC}"
    exit 1
}

echo -e "${YELLOW}🔄 Restarting service...${NC}"
systemctl restart "$SERVICE_NAME" || {
    echo -e "${RED}Error: Failed to restart service${NC}"
    exit 1
}

# Wait a moment for service to start
sleep 2

# Check service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service failed to start. Check logs with: journalctl -u $SERVICE_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${YELLOW}View logs with: journalctl -u $SERVICE_NAME -f${NC}"

