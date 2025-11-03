const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const waitOn = require('wait-on');
const net = require('net');
const fs = require('fs');

let mainWindow;
let backendProcess;
let frontendProcess;

// Backend server configuration
const BACKEND_PORT = 8001;
const FRONTEND_PORT = 3000;

// Helper function to check if port is in use
function isPortOpen(port, host = '127.0.0.1') {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        
        socket.setTimeout(1000);
        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });
        socket.on('timeout', () => {
            socket.destroy();
            resolve(false);
        });
        socket.on('error', () => {
            resolve(false);
        });
        
        socket.connect(port, host);
    });
}

// Helper function to find Python executable (prefer venv)
function findPythonPath() {
    const rootDir = path.join(__dirname, '..');
    const venvPath = path.join(rootDir, 'backend', 'venv');
    
    if (process.platform === 'win32') {
        const venvPython = path.join(venvPath, 'Scripts', 'python.exe');
        if (fs.existsSync(venvPython)) {
            console.log(`Using venv Python: ${venvPython}`);
            return venvPython;
        }
        return 'python';
    } else {
        const venvPython = path.join(venvPath, 'bin', 'python3');
        if (fs.existsSync(venvPython)) {
            console.log(`Using venv Python: ${venvPython}`);
            return venvPython;
        }
        return 'python3';
    }
}

function startBackend() {
    return new Promise(async (resolve, reject) => {
        console.log('Checking backend port...');
        
        // Check if backend is already running
        const backendAlreadyRunning = await isPortOpen(BACKEND_PORT);
        if (backendAlreadyRunning) {
            console.log(`✓ Backend already running on port ${BACKEND_PORT}`);
            resolve();
            return;
        }
        
        console.log('Starting FastAPI backend...');
        
        const pythonPath = findPythonPath();
        const backendPath = path.join(__dirname, '..', 'backend');
        
        console.log(`Python path: ${pythonPath}`);
        console.log(`Backend path: ${backendPath}`);
        
        backendProcess = spawn(pythonPath, [
            '-m', 'uvicorn',
            'server:app',
            '--host', '0.0.0.0',
            '--port', BACKEND_PORT.toString(),
            '--log-level', 'warning'
        ], {
            cwd: backendPath,
            env: {
                ...process.env,
                CORS_ORIGINS: `http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}`,
                PYTHONUNBUFFERED: '1'
            }
        });

        backendProcess.stdout.on('data', (data) => {
            console.log(`Backend: ${data}`);
        });

        backendProcess.stderr.on('data', (data) => {
            const message = data.toString();
            console.error(`Backend stderr: ${message}`);
            
            // Handle EADDRINUSE error
            if (message.includes('address already in use') || message.includes('EADDRINUSE')) {
                console.log('Port already in use, checking if backend is accessible...');
                // Don't reject, will wait for port check below
            }
        });

        backendProcess.on('error', (error) => {
            console.error('Failed to start backend process:', error);
            reject(error);
        });

        backendProcess.on('exit', (code, signal) => {
            if (code !== 0 && code !== null) {
                console.error(`Backend process exited with code ${code}`);
            }
        });

        // Wait for backend to be ready using TCP check
        console.log('Waiting for backend to be ready...');
        setTimeout(() => {
            waitOn({
                resources: [`tcp:127.0.0.1:${BACKEND_PORT}`],
                timeout: 30000,
                interval: 500,
                verbose: true
            }).then(() => {
                console.log('✓ Backend is ready!');
                resolve();
            }).catch((err) => {
                console.error('Backend failed to start:', err);
                reject(err);
            });
        }, 2000);
    });
}

function startFrontend() {
    return new Promise(async (resolve, reject) => {
        console.log('Checking frontend port...');
        
        // Check if frontend is already running
        const frontendAlreadyRunning = await isPortOpen(FRONTEND_PORT);
        if (frontendAlreadyRunning) {
            console.log(`✓ Frontend already running on port ${FRONTEND_PORT}`);
            resolve();
            return;
        }
        
        console.log('Starting frontend server...');
        
        const pythonPath = findPythonPath();
        const backendPath = path.join(__dirname, '..', 'backend');
        const frontendBuildPath = path.join(__dirname, '..', 'frontend', 'build');
        
        // Check if frontend build exists
        const indexHtmlPath = path.join(frontendBuildPath, 'index.html');
        if (!fs.existsSync(indexHtmlPath)) {
            console.error(`Error: Frontend build not found at ${frontendBuildPath}`);
            console.error('Please run setup script first to build the frontend');
            reject(new Error('Frontend build not found'));
            return;
        }
        
        console.log(`Python path: ${pythonPath}`);
        console.log(`Frontend build path: ${frontendBuildPath}`);
        
        frontendProcess = spawn(pythonPath, [
            'serve_frontend.py'
        ], {
            cwd: backendPath,
            env: {
                ...process.env,
                PYTHONUNBUFFERED: '1'
            }
        });

        frontendProcess.stdout.on('data', (data) => {
            console.log(`Frontend: ${data}`);
        });

        frontendProcess.stderr.on('data', (data) => {
            const message = data.toString();
            console.error(`Frontend stderr: ${message}`);
            
            // Handle EADDRINUSE error
            if (message.includes('Address already in use') || message.includes('EADDRINUSE')) {
                console.log('Port already in use, checking if frontend is accessible...');
                // Don't reject, will wait for port check below
            }
        });

        frontendProcess.on('error', (error) => {
            console.error('Failed to start frontend process:', error);
            reject(error);
        });

        frontendProcess.on('exit', (code, signal) => {
            if (code !== 0 && code !== null) {
                console.error(`Frontend process exited with code ${code}`);
            }
        });

        // Wait for frontend to be ready using TCP check
        console.log('Waiting for frontend to be ready...');
        setTimeout(() => {
            waitOn({
                resources: [`tcp:127.0.0.1:${FRONTEND_PORT}`],
                timeout: 30000,
                interval: 500,
                verbose: true
            }).then(() => {
                console.log('✓ Frontend is ready!');
                resolve();
            }).catch((err) => {
                console.error('Frontend failed to start:', err);
                reject(err);
            });
        }, 1000);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 768,
        backgroundColor: '#ffffff',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            webSecurity: true
        },
        show: false,
        autoHideMenuBar: true,
        title: 'AXXO Builder'
    });

    // Load frontend using 127.0.0.1 to avoid localhost resolution issues
    const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}`;
    
    console.log(`Loading frontend from: ${frontendUrl}`);
    
    mainWindow.loadURL(frontendUrl).catch((err) => {
        console.error('Failed to load frontend:', err);
    });

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        console.log('\n========================================');
        console.log('  ✓ AXXO Builder is ready!');
        console.log('========================================\n');
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }
}

async function startApp() {
    console.log('\n========================================');
    console.log('  Starting AXXO Builder...');
    console.log('========================================\n');
    
    try {
        // Start backend first
        await startBackend();
        
        // Start frontend server
        await startFrontend();
        
        // Small delay to ensure everything is stable
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Create Electron window
        createWindow();
    } catch (error) {
        console.error('Failed to start application:', error);
        app.quit();
    }
}

app.whenReady().then(startApp);

app.on('window-all-closed', () => {
    // Kill processes only if we spawned them
    if (backendProcess && !backendProcess.killed) {
        console.log('Stopping backend...');
        backendProcess.kill();
    }
    if (frontendProcess && !frontendProcess.killed) {
        console.log('Stopping frontend...');
        frontendProcess.kill();
    }
    
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('quit', () => {
    // Ensure processes are killed
    if (backendProcess && !backendProcess.killed) {
        backendProcess.kill();
    }
    if (frontendProcess && !frontendProcess.killed) {
        frontendProcess.kill();
    }
});

// Handle errors
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (error) => {
    console.error('Unhandled rejection:', error);
});
