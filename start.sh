#!/bin/bash

# AXXO Builder - Improved Startup Script for Linux/Mac
# This script starts the AXXO Builder desktop application with robust checks

echo "=========================================="
echo "  Starting AXXO Builder..."
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if port is in use
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port &> /dev/null
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -an | grep ":$port " | grep -q LISTEN
        return $?
    else
        # Fallback: try to bind to port
        python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', $port)); s.close()" 2>/dev/null
        return $(( 1 - $? ))
    fi
}

# Function to get process using port
get_port_process() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port -t 2>/dev/null | head -1
    elif command -v netstat &> /dev/null; then
        netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -1
    else
        echo ""
    fi
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${BLUE}Python version: $PYTHON_VERSION${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 16 or higher"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v)
echo -e "${BLUE}Node.js version: $NODE_VERSION${NC}"

# Check if yarn is installed
if ! command -v yarn &> /dev/null; then
    echo -e "${YELLOW}Installing yarn...${NC}"
    npm install -g yarn
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Check for port conflicts
echo -e "${BLUE}Checking ports...${NC}"

BACKEND_PORT=8001
FRONTEND_PORT=3000
PORTS_OK=true

if check_port $BACKEND_PORT; then
    PID=$(get_port_process $BACKEND_PORT)
    echo -e "${YELLOW}⚠ Port $BACKEND_PORT is already in use${NC}"
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}  Process: $PID${NC}"
    fi
    echo -e "${YELLOW}  The app will try to reuse the existing backend${NC}"
else
    echo -e "${GREEN}✓ Port $BACKEND_PORT is available${NC}"
fi

if check_port $FRONTEND_PORT; then
    PID=$(get_port_process $FRONTEND_PORT)
    echo -e "${YELLOW}⚠ Port $FRONTEND_PORT is already in use${NC}"
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}  Process: $PID${NC}"
    fi
    echo -e "${YELLOW}  The app will try to reuse the existing frontend${NC}"
else
    echo -e "${GREEN}✓ Port $FRONTEND_PORT is available${NC}"
fi

echo ""

# Create and setup virtual environment for backend
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    cd backend
    python3 -m venv venv
    cd ..
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv and install backend dependencies
echo -e "${YELLOW}Checking backend dependencies...${NC}"
cd backend

# Determine venv activation script
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: Could not find venv activation script${NC}"
    exit 1
fi

# Check if uvicorn is installed in venv
if ! python -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies in venv...${NC}"
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Backend dependencies OK${NC}"
fi

# Verify fastapi is also available
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing missing FastAPI...${NC}"
    pip install fastapi --quiet
fi

deactivate
cd ..

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    yarn install --silent
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies OK${NC}"
fi

# Build frontend if build folder doesn't exist or is incomplete
if [ ! -f "frontend/build/index.html" ]; then
    echo -e "${YELLOW}Building frontend for desktop (this may take a minute)...${NC}"
    cd frontend
    
    # Copy desktop env config if it exists
    if [ -f ".env.desktop" ]; then
        cp .env.desktop .env.production.local
    fi
    
    GENERATE_SOURCEMAP=false yarn build
    
    # Cleanup
    rm -f .env.production.local
    cd ..
    
    # Verify build succeeded
    if [ ! -f "frontend/build/index.html" ]; then
        echo -e "${RED}Error: Frontend build failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Frontend built successfully${NC}"
else
    echo -e "${GREEN}✓ Frontend build OK${NC}"
fi

# Install electron dependencies if needed
if [ ! -d "electron/node_modules" ]; then
    echo -e "${YELLOW}Installing Electron...${NC}"
    cd electron
    yarn install --silent
    cd ..
    echo -e "${GREEN}✓ Electron installed${NC}"
else
    echo -e "${GREEN}✓ Electron OK${NC}"
fi

# Start the application
echo ""
echo -e "${GREEN}=========================================="
echo -e "  Launching AXXO Builder..."
echo -e "==========================================${NC}"
echo ""
echo -e "${BLUE}Note: If ports are already in use, the app will reuse them${NC}"
echo ""

cd electron
yarn start

# Cleanup on exit
echo ""
echo -e "${GREEN}AXXO Builder closed. Thank you!${NC}"
