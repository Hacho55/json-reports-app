#!/bin/bash

# Docker verification script for JSON Reports Tools
# Usage: ./scripts/verify-docker.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Verifying Docker setup for JSON Reports Tools${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed and running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  docker-compose not found, but Docker Compose is included in Docker Desktop${NC}"
else
    echo -e "${GREEN}✅ docker-compose is available${NC}"
fi

# Check required files
echo ""
echo -e "${BLUE}📁 Checking required files:${NC}"

REQUIRED_FILES=("Dockerfile" "docker-compose.yml" "app.py" "Pipfile" "Pipfile.lock")

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file (missing)${NC}"
        exit 1
    fi
done

# Check if tools directory exists
if [ -d "tools" ]; then
    echo -e "${GREEN}✅ tools/ directory${NC}"
else
    echo -e "${RED}❌ tools/ directory (missing)${NC}"
    exit 1
fi

# Check if config directory exists
if [ -d "config" ]; then
    echo -e "${GREEN}✅ config/ directory${NC}"
else
    echo -e "${RED}❌ config/ directory (missing)${NC}"
    exit 1
fi

# Check Python files in tools
echo ""
echo -e "${BLUE}🐍 Checking Python modules:${NC}"
TOOLS_FILES=("tools/__init__.py" "tools/json_converter.py" "tools/metrics_validator.py" "tools/metrics_extractor.py")

for file in "${TOOLS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file (missing)${NC}"
        exit 1
    fi
done

# Check config files
echo ""
echo -e "${BLUE}⚙️  Checking configuration files:${NC}"
CONFIG_FILES=("config/wei_tr181_rules.yaml")

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${YELLOW}⚠️  $file (optional)${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 All checks passed! Ready to build Docker image.${NC}"
echo ""
echo -e "${YELLOW}🚀 Next steps:${NC}"
echo "  1. Build the image: ./scripts/docker-build.sh"
echo "  2. Run with Docker: docker run -p 8504:8504 json-reports-tools:latest"
echo "  3. Or use docker-compose: docker-compose up"
echo ""
echo -e "${BLUE}📊 Application will be available at: http://localhost:8504${NC}" 