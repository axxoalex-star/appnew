#!/usr/bin/env python3
"""
Simple static file server for serving the React build
Used by Electron to serve the frontend
Improved with port occupation handling
"""

import http.server
import socketserver
import os
import sys
import socket
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent.parent / "frontend" / "build"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Add headers for CORS and caching
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for all routes (SPA routing)
        if not Path(str(DIRECTORY) + self.path).exists() and not self.path.startswith('/static'):
            self.path = '/index.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

def is_port_in_use(port, host='127.0.0.1'):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

if __name__ == '__main__':
    # Check if build directory exists
    if not DIRECTORY.exists():
        print(f"Error: Build directory not found at {DIRECTORY}", file=sys.stderr)
        print("Please run 'yarn build' in the frontend directory first", file=sys.stderr)
        sys.exit(1)
    
    # Check if index.html exists
    index_html = DIRECTORY / "index.html"
    if not index_html.exists():
        print(f"Error: index.html not found in {DIRECTORY}", file=sys.stderr)
        print("Frontend build may be incomplete. Please rebuild.", file=sys.stderr)
        sys.exit(1)
    
    # Check if port is already in use
    if is_port_in_use(PORT):
        print(f"Warning: Port {PORT} is already in use", file=sys.stderr)
        print(f"Assuming frontend is already running on http://localhost:{PORT}", file=sys.stderr)
        # Exit gracefully - Electron will detect the port is open
        sys.exit(0)
    
    # Use TCPServer with allow_reuse_address to avoid EADDRINUSE
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"Serving frontend on http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98 or 'Address already in use' in str(e):
            print(f"Port {PORT} became occupied during startup", file=sys.stderr)
            sys.exit(0)
        else:
            raise
    except KeyboardInterrupt:
        print("\nShutting down server")
