#!/bin/bash
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🧪 AXXO Builder Desktop - Verificare Finală              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

checks_passed=0
checks_total=0

# Check 1: Scripturi pornire
checks_total=$((checks_total + 1))
if [ -f "start.sh" ] && [ -f "start.bat" ] && [ -x "start.sh" ]; then
    echo -e "${GREEN}✓${NC} Scripturi pornire (start.sh, start.bat)"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Scripturi pornire lipsă sau fără permisiuni"
fi

# Check 2: Backend files
checks_total=$((checks_total + 1))
if [ -f "backend/server.py" ] && [ -f "backend/database.py" ] && [ -f "backend/serve_frontend.py" ]; then
    echo -e "${GREEN}✓${NC} Backend files (server.py, database.py, serve_frontend.py)"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Backend files lipsă"
fi

# Check 3: Frontend build
checks_total=$((checks_total + 1))
if [ -d "frontend/build" ] && [ -f "frontend/build/index.html" ]; then
    echo -e "${GREEN}✓${NC} Frontend build (frontend/build/)"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Frontend build lipsă - rulează setup.sh mai întâi"
fi

# Check 4: Frontend config
checks_total=$((checks_total + 1))
if [ -f "frontend/.env.desktop" ]; then
    echo -e "${GREEN}✓${NC} Frontend desktop config (.env.desktop)"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Frontend desktop config lipsă"
fi

# Check 5: Electron setup
checks_total=$((checks_total + 1))
if [ -f "electron/main.js" ] && [ -f "electron/package.json" ]; then
    echo -e "${GREEN}✓${NC} Electron setup (main.js, package.json)"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Electron files lipsă"
fi

# Check 6: Database module
checks_total=$((checks_total + 1))
if python3 -c "from backend.database import db" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} SQLite database module funcțional"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Database module error - verifică dependencies"
fi

# Check 7: Requirements
checks_total=$((checks_total + 1))
if [ -f "backend/requirements.txt" ]; then
    echo -e "${GREEN}✓${NC} Backend requirements.txt"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Requirements.txt lipsă"
fi

# Check 8: Documentation
checks_total=$((checks_total + 1))
if [ -f "README.md" ] && [ -f "QUICK_START.md" ] && [ -f "CHANGELOG.md" ]; then
    echo -e "${GREEN}✓${NC} Documentație completă"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${RED}✗${NC} Documentație incompletă"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e " Rezultat: ${GREEN}$checks_passed${NC}/$checks_total verificări trecute"
echo "════════════════════════════════════════════════════════════"

if [ $checks_passed -eq $checks_total ]; then
    echo -e "${GREEN}"
    echo "🎉 TOTUL ESTE GATA!"
    echo "Rulează: ./start.sh (Linux/Mac) sau start.bat (Windows)"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "⚠️  Câteva verificări au eșuat"
    echo "Rulează: ./setup.sh pentru a finaliza setup-ul"
    echo -e "${NC}"
    exit 1
fi
