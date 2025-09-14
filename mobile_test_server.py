#!/usr/bin/env python3
"""
🦭 Mobile Test Server for Line Walrus
====================================

Simple HTTP server to serve mobile test files for debugging touch interactions.
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class MobileTestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for mobile testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    PORT = 8080
    
    print("🦭 Mobile Test Server for Line Walrus")
    print("=" * 50)
    print(f"Starting server on port {PORT}...")
    
    with socketserver.TCPServer(("", PORT), MobileTestHandler) as httpd:
        print(f"✅ Server running at http://localhost:{PORT}")
        print(f"✅ Server running at http://0.0.0.0:{PORT}")
        print()
        print("📱 Mobile Test Files:")
        print(f"  • Touch Debugger: http://localhost:{PORT}/mobile_touch_debugger.html")
        print(f"  • Mobile Fix Test: http://localhost:{PORT}/mobile_fix.html")
        print(f"  • Debug Helper: http://localhost:{PORT}/mobile_debug_helper.html")
        print()
        print("🏒 Line Walrus App:")
        print(f"  • Main App: http://localhost:5001")
        print()
        print("📋 Testing Instructions:")
        print("1. Open the mobile test files on your iPhone")
        print("2. Test touch interactions")
        print("3. Check console logs for debugging info")
        print("4. Compare with the main Line Walrus app")
        print()
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🦭 Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
