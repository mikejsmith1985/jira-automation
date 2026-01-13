"""Minimal HTTP server test"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class TestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def do_GET(self):
        if self.path == '/':
            try:
                filepath = os.path.join(os.path.dirname(__file__), 'modern-ui.html')
                print(f"[TEST] Reading: {filepath}")
                with open(filepath, 'rb') as f:
                    content = f.read()
                print(f"[TEST] Read {len(content)} bytes")
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
                print(f"[TEST] Sent response")
            except Exception as e:
                print(f"[TEST] ERROR: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server_address = ('127.0.0.1', 5001)
    httpd = HTTPServer(server_address, TestHandler)
    print("Test server running on http://127.0.0.1:5001")
    httpd.serve_forever()
