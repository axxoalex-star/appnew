#!/bin/bash

# AXXO Builder - Quick Setup Script
# Run this once to prepare everything

echo "================================================"
echo "  AXXO Builder - Initial Setup"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd backend
pip3 install -r requirements.txt
cd ..
echo -e "${GREEN}✓ Backend ready${NC}"

echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
yarn install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

echo -e "${YELLOW}Building optimized frontend for desktop...${NC}"
cp .env.desktop .env.production.local
GENERATE_SOURCEMAP=false yarn build
rm -f .env.production.local
cd ..
echo -e "${GREEN}✓ Frontend built${NC}"

echo -e "${YELLOW}Installing Electron...${NC}"
cd electron
yarn install
cd ..
echo -e "${GREEN}✓ Electron ready${NC}"

echo ""
echo -e "${GREEN}================================================"
echo -e "  Setup Complete!"
echo -e "================================================${NC}"
echo ""
echo "To start the application, run:"
echo "  ./start.sh        (Linux/Mac)"
echo "  start.bat         (Windows)"
echo ""
