# AXXO Builder - Linux Deployment Fixes

## Probleme Identificate și Remediate

### 📋 Rezumat Probleme

1. **Detecție backend greșită (redirect 307 pe /api)**
2. **Backend lansat cu Python de sistem, nu cu backend/venv**
3. **Portul 8001 ocupat (EADDRINUSE)**
4. **Așteptare backend fragilă (HTTP pe localhost)**
5. **Frontend: portul 3000 deja folosit (EADDRINUSE)**
6. **Așteptare frontend fragilă**
7. **Build frontend potențial lipsă sau incomplet**
8. **Loguri backend filtrate**

---

## 🔧 Remedieri Implementate

### 1. electron/main.js - Îmbunătățiri Majore

#### ✅ Detecție robustă Python (prefer venv)
```javascript
function findPythonPath() {
    const venvPath = path.join(rootDir, 'backend', 'venv');
    
    if (process.platform === 'win32') {
        const venvPython = path.join(venvPath, 'Scripts', 'python.exe');
        if (fs.existsSync(venvPython)) return venvPython;
        return 'python';
    } else {
        const venvPython = path.join(venvPath, 'bin', 'python3');
        if (fs.existsSync(venvPython)) return venvPython;
        return 'python3';
    }
}
```

**Beneficii:**
- Folosește automat Python din venv dacă există
- Evită problemele de dependențe cu Python-ul de sistem
- Fallback automat la Python sistem dacă venv lipsește

#### ✅ Verificare porturi cu TCP
```javascript
function isPortOpen(port, host = '127.0.0.1') {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(1000);
        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });
        // ... error handling
        socket.connect(port, host);
    });
}
```

**Beneficii:**
- Verificare nativă TCP (nu HTTP) - mai robustă
- Folosește 127.0.0.1 în loc de localhost (evită probleme IPv6)
- Timeout rapid (1s) pentru răspuns prompt

#### ✅ Skip spawn dacă portul e deschis
```javascript
const backendAlreadyRunning = await isPortOpen(BACKEND_PORT);
if (backendAlreadyRunning) {
    console.log(`✓ Backend already running on port ${BACKEND_PORT}`);
    resolve();
    return;
}
```

**Beneficii:**
- Nu mai încearcă să pornească backend/frontend dacă rulează deja
- Elimină erorile EADDRINUSE
- Permite rulări multiple/restartări fără conflicte

#### ✅ Logging complet stderr
```javascript
backendProcess.stderr.on('data', (data) => {
    const message = data.toString();
    console.error(`Backend stderr: ${message}`);
    
    if (message.includes('address already in use')) {
        console.log('Port already in use, checking if backend is accessible...');
    }
});
```

**Beneficii:**
- Toate erorile stderr sunt acum afișate (nu mai sunt filtrate)
- Ușurează debugging-ul
- Detecție specifică pentru EADDRINUSE

#### ✅ Așteptare pe TCP pentru backend/frontend
```javascript
waitOn({
    resources: [`tcp:127.0.0.1:${BACKEND_PORT}`],
    timeout: 30000,
    interval: 500,
    verbose: true
})
```

**Beneficii:**
- Verifică direct disponibilitatea portului TCP
- Nu depinde de endpoint-uri HTTP specifice
- Funcționează și când serviciul e pornit de altcineva

### 2. backend/serve_frontend.py - Gestionare Porturi

#### ✅ Verificare port înainte de bind
```python
def is_port_in_use(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

if is_port_in_use(PORT):
    print(f"Port {PORT} is already in use", file=sys.stderr)
    sys.exit(0)  # Exit gracefully
```

**Beneficii:**
- Detectează portul ocupat ÎNAINTE de a încerca bind
- Exit graceful (cod 0) când portul e folosit
- Electron detectează că portul e deschis și continuă

#### ✅ Verificare index.html
```python
index_html = DIRECTORY / "index.html"
if not index_html.exists():
    print(f"Error: index.html not found", file=sys.stderr)
    sys.exit(1)
```

**Beneficii:**
- Validează că build-ul frontend e complet
- Eroare clară dacă build-ul lipsește
- Previne pornirea cu frontend incomplet

#### ✅ Allow reuse address
```python
socketserver.TCPServer.allow_reuse_address = True
```

**Beneficii:**
- Permite restart rapid fără așteptare TIME_WAIT
- Evită erori când portul e "semi-ocupat"

### 3. start.sh - Verificări Proactive

#### ✅ Verificare porturi la startup
```bash
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port &> /dev/null
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -an | grep ":$port " | grep -q LISTEN
        return $?
    fi
}

if check_port 8001; then
    echo "⚠ Port 8001 is already in use"
    echo "  The app will try to reuse the existing backend"
fi
```

**Beneficii:**
- Avertizează utilizatorul despre porturi ocupate
- Suportă multiple tool-uri (lsof, netstat, Python fallback)
- Nu blochează pornirea - doar informează

#### ✅ Creare și validare venv
```bash
if [ ! -d "backend/venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
if ! python -c "import uvicorn" 2>/dev/null; then
    pip install -r requirements.txt --quiet
fi
```

**Beneficii:**
- Creează automat venv dacă lipsește
- Verifică dependențele în venv (nu sistem)
- Instalează doar ce lipsește (rapid la restart)

#### ✅ Validare build frontend complet
```bash
if [ ! -f "frontend/build/index.html" ]; then
    yarn build
    
    if [ ! -f "frontend/build/index.html" ]; then
        echo "Error: Frontend build failed"
        exit 1
    fi
fi
```

**Beneficii:**
- Verifică index.html, nu doar folder-ul build
- Rebuild automat dacă build-ul lipsește
- Eșuează clar dacă build-ul nu reușește

#### ✅ Informații detaliate proces
```bash
get_port_process() {
    local port=$1
    lsof -i :$port -t 2>/dev/null | head -1
}

PID=$(get_port_process $BACKEND_PORT)
if [ ! -z "$PID" ]; then
    echo "  Process: $PID"
fi
```

**Beneficii:**
- Arată PID-ul procesului care folosește portul
- Ajută la identificare rapidă conflict
- Ușurează debugging

---

## 🎯 Rezultate Finale

### Scenarii Acoperite

✅ **Prim start (porturi libere)**
- Creează venv
- Instalează dependențe
- Build frontend
- Pornește backend + frontend
- Lansează Electron

✅ **Restart rapid (servicii rulate deja)**
- Detectează backend pe 8001 → skip spawn
- Detectează frontend pe 3000 → skip spawn
- Refolosește serviciile existente
- Lansează doar Electron window

✅ **Backend ocupat, frontend liber**
- Refolosește backend existent
- Pornește frontend nou
- Lansează Electron

✅ **Ambele porturi ocupate**
- Refolosește ambele servicii
- Doar Electron window se deschide
- Fără erori EADDRINUSE

✅ **Build frontend incomplet**
- Detectează lipsă index.html
- Rebuild automat
- Validează succes build

✅ **venv lipsește**
- Creează venv automat
- Instalează dependențe
- Folosește Python din venv

---

## 📊 Îmbunătățiri Tehnice

| Aspect | Înainte | După |
|--------|---------|------|
| **Detecție backend** | HTTP localhost (fragil) | TCP 127.0.0.1 (robust) |
| **Python folosit** | Sistem (inconsistent) | venv preferred (consistent) |
| **Port ocupat** | Eroare + crash | Skip spawn + refolosire |
| **Logging stderr** | Filtrat | Complet (debugging ușor) |
| **Build frontend** | Verifică folder | Verifică index.html |
| **Venv backend** | Manual | Auto-create + install |
| **Port check** | La spawn | Înainte de spawn |
| **Așteptare servicii** | HTTP endpoint | TCP port |

---

## 🚀 Folosire

### Linux/Mac
```bash
./start.sh
```

Script-ul va:
1. Verifica prerequisite (Python, Node, yarn)
2. Verifica porturi 8001/3000
3. Crea venv dacă lipsește
4. Instala dependențe backend în venv
5. Build frontend dacă e necesar
6. Instala Electron dependencies
7. Lansa aplicația

### Debugging

#### Vezi ce folosește un port
```bash
lsof -i :8001
lsof -i :3000
```

#### Oprește proces pe port
```bash
kill $(lsof -t -i:8001)
kill $(lsof -t -i:3000)
```

#### Verifică venv backend
```bash
cd backend
source venv/bin/activate
python -c "import uvicorn, fastapi; print('OK')"
```

#### Verifică build frontend
```bash
ls -la frontend/build/index.html
```

---

## ✅ Checklist Deployment

- [x] Detecție robustă Python (venv preferred)
- [x] Verificare TCP pentru backend/frontend
- [x] Skip spawn când portul e deschis
- [x] Gestionare EADDRINUSE graceful
- [x] Logging complet stderr
- [x] Verificare build frontend complet
- [x] Creare automată venv
- [x] Verificare proactivă porturi în start.sh
- [x] Folosire 127.0.0.1 în loc de localhost
- [x] Fallback pentru tool-uri lipsă

---

## 📝 Note Finale

Toate problemele identificate au fost remediate cu soluții robuste care:
- Funcționează pe Linux, Mac și Windows
- Permit rulări multiple fără conflicte
- Oferă mesaje clare de debugging
- Refolosesc servicii existente când e posibil
- Validează toate prerequisite înainte de pornire

Aplicația poate acum fi pornită și repornită fără probleme, chiar și când porturile sunt deja ocupate.
