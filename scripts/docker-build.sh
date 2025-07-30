#!/bin/bash

# Docker build script for JSON Reports Tools
# Usage: ./scripts/docker-build.sh [tag]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default tag
TAG=${1:-"latest"}

echo -e "${YELLOW}🐳 Building JSON Reports Tools Docker Image${NC}"
echo "Tag: $TAG"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}📦 Building Docker image...${NC}"
docker build -t json-reports-tools:$TAG .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    echo ""
    echo -e "${YELLOW}🚀 To run the application:${NC}"
    echo "  docker run -p 8504:8504 json-reports-tools:$TAG"
    echo ""
    echo -e "${YELLOW}🐳 Or use docker-compose:${NC}"
    echo "  docker-compose up"
    echo ""
    echo -e "${YELLOW}📊 Application will be available at:${NC}"
    echo "  http://localhost:8504"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi 