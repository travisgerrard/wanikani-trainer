#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

PORT = 8000

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def main():
    # Change to the project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Allow address reuse to avoid "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    
    with ThreadingHTTPServer(('', PORT), Handler) as httpd:
        print(f"Serving at http://0.0.0.0:{PORT}")
        print(f"Open http://<your-ip>:{PORT}/pwa/ on your device")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()

if __name__ == "__main__":
    main()

