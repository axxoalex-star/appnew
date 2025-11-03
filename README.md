# AXXO Builder - Desktop Application

## 🚀 Quick Start (O singură comandă!)

### Windows
```bash
start.bat
```

### Linux / Mac
```bash
./start.sh
```

## 📋 Cerințe Sistem

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)

## 🎯 Ce Face Scriptul?

Scriptul `start.sh` / `start.bat` face automat:
1. ✅ Verifică dacă Python și Node.js sunt instalate
2. ✅ Instalează toate dependențele (backend + frontend + electron)
3. ✅ Construiește aplicația frontend (prima dată)
4. ✅ Pornește backend-ul FastAPI automat
5. ✅ Deschide aplicația desktop AXXO Builder

**Timpul de încărcare:** < 10 secunde după prima pornire

## 🏗️ Structură Proiect

```
/app
├── backend/              # FastAPI server + SQLite database
├── frontend/             # React application
├── electron/             # Electron desktop wrapper
├── start.sh             # Linux/Mac startup script
└── start.bat            # Windows startup script
```

## 📦 Build pentru Distribuție

### Creează executabil pentru toate platformele:
```bash
cd electron
yarn build-all
```

### Doar pentru Windows:
```bash
cd electron
yarn build-win
```

### Doar pentru Mac:
```bash
cd electron
yarn build-mac
```

### Doar pentru Linux:
```bash
cd electron
yarn build-linux
```

Fișierele executabile vor fi create în `electron/dist/`

## 🗄️ Baza de Date

Aplicația folosește **SQLite** - o bază de date locală salvată în:
```
backend/axxo_builder.db
```

Nu este nevoie de MongoDB sau MySQL instalat!

## 🔧 Optimizări Implementate

- ✅ SQLite în loc de MongoDB (nu necesită server separat)
- ✅ Frontend pre-compilat pentru încărcare rapidă
- ✅ Electron optimizat pentru desktop
- ✅ Backend FastAPI lightweight
- ✅ Code splitting și lazy loading
- ✅ Bundle size minimizat

## 📝 Dezvoltare

Pentru a lucra la aplicație în modul dezvoltare:

```bash
# Terminal 1 - Backend
cd backend
python3 -m uvicorn server:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
yarn start

# Terminal 3 - Electron (dev mode)
cd electron
yarn dev
```

## 🐛 Troubleshooting

### Aplicația nu pornește?
1. Verifică că Python 3.8+ este instalat: `python3 --version`
2. Verifică că Node.js 16+ este instalat: `node --version`
3. Șterge folderele `node_modules` și rulează din nou scriptul

### Backend error?
1. Verifică log-urile în terminal
2. Asigură-te că portul 8001 este liber
3. Reinstalează dependențele: `cd backend && pip3 install -r requirements.txt`

### Frontend nu se încarcă?
1. Șterge `frontend/build` și `frontend/node_modules`
2. Rulează din nou `./start.sh` sau `start.bat`

## 📞 Suport

Pentru probleme sau întrebări, deschide un issue pe GitHub.

---

**Made with ❤️ by AXXO Team**

