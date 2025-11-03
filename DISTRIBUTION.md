# 🚀 AXXO Builder Desktop - Quick Distribution Guide

## 📦 Pregătire pentru Distribuție

### Pasul 1: Copiază folderul
Copiază întreg folderul `AXXO-Builder/` pe computerul de destinație.

### Pasul 2: Instalează cerințele
- **Python 3.8+**: https://www.python.org/downloads/
- **Node.js 16+**: https://nodejs.org/

### Pasul 3: Rulează
- **Windows**: Dublu-click pe `start.bat`
- **Linux/Mac**: Terminal → `./start.sh`

## 🎯 Sau Creează un Executabil

Pentru a distribui ca executabil standalone:

```bash
cd electron
yarn build-win    # Windows .exe
yarn build-mac    # macOS .dmg  
yarn build-linux  # Linux .AppImage
```

Fișierele vor fi în `electron/dist/`

## 📋 Ce Include

✅ Backend FastAPI cu SQLite (fără servere externe)
✅ Frontend React optimizat (1.3 MB)
✅ Electron pentru aplicație desktop
✅ Toate dependențele necesare

## 💡 Notă

Prima pornire va dura 3-5 minute (instalează dependencies).
Următoarele porniri: < 10 secunde!

---

Pentru detalii complete, vezi: `README.md` și `QUICK_START.md`
