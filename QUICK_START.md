# 🚀 AXXO Builder - Ghid de Pornire Rapidă

## Pentru Windows

### 1. Instalează Cerințele
- **Python 3.8+**: https://www.python.org/downloads/
  - În timpul instalării, bifează "Add Python to PATH"
- **Node.js 16+**: https://nodejs.org/

### 2. Rulează Aplicația
Dublu-click pe:
```
start.bat
```

**SAU** deschide Command Prompt în folderul aplicației și rulează:
```
start.bat
```

---

## Pentru Linux

### 1. Instalează Cerințele
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm

# Fedora
sudo dnf install python3 python3-pip nodejs npm

# Arch Linux
sudo pacman -S python python-pip nodejs npm
```

### 2. Rulează Aplicația
```bash
./start.sh
```

---

## Pentru macOS

### 1. Instalează Cerințele
```bash
# Instalează Homebrew dacă nu e instalat
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalează Python și Node.js
brew install python@3.11 node
```

### 2. Rulează Aplicația
```bash
./start.sh
```

---

## 📝 Ce se Întâmplă la Prima Pornire?

Scriptul `start.sh` / `start.bat` va:
1. Verifica dacă Python și Node.js sunt instalate ✓
2. Instala toate dependențele necesare (2-3 minute) ✓
3. Construi aplicația frontend (1-2 minute) ✓
4. Instala Electron ✓
5. Porni aplicația desktop AXXO Builder ✓

**Următoarele porniri vor dura < 10 secunde!**

---

## 🎯 Build pentru Distribuție

### Creează un executabil standalone:

#### Windows (.exe)
```bash
cd electron
yarn build-win
```
Fișierul se va crea în: `electron/dist/AXXO Builder Setup.exe`

#### macOS (.dmg)
```bash
cd electron
yarn build-mac
```
Fișierul se va crea în: `electron/dist/AXXO Builder.dmg`

#### Linux (.AppImage)
```bash
cd electron
yarn build-linux
```
Fișierul se va crea în: `electron/dist/AXXO Builder.AppImage`

#### Toate platformele
```bash
cd electron
yarn build-all
```

---

## ⚡ Optimizări

Aplicația include:
- ✅ **Încărcare rapidă** - < 10 secunde după prima pornire
- ✅ **SQLite local** - nu necesită MySQL sau MongoDB
- ✅ **Frontend optimizat** - bundle size minimizat
- ✅ **Electron optimizat** - folosește resurse minime
- ✅ **Backend lightweight** - FastAPI cu performanță mare

---

## 🐛 Probleme Comune

### Eroare: "Python not found"
**Soluție**: Instalează Python 3.8+ și asigură-te că e adăugat în PATH

### Eroare: "Node not found"
**Soluție**: Instalează Node.js 16+ de pe nodejs.org

### Aplicația se încarcă lent
**Soluție**: La prima pornire e normal să dureze 2-3 minute pentru build. Următoarele porniri vor fi rapide.

### Port 8001 sau 3000 deja folosit
**Soluție**: Închide alte aplicații care folosesc aceste porturi sau schimbă porturile în `electron/main.js`

---

## 📞 Suport

Pentru întrebări sau probleme, contactează echipa AXXO.

---

**Enjoy building with AXXO Builder! 🎨**
