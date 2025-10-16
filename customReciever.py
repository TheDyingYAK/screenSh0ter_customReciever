# Written by TheDyingYak 20251015
# For research purposes only
# custom_receiver.py (Python 6.13+ compatible)
#!/usr/bin/env python3
import http.server
import socketserver
import base64
import os
import re
from datetime import datetime
from io import BytesIO
from email import message_from_bytes
from urllib.parse import parse_qs

PORT = 80
UPLOAD_DIR = "screenshots"

class ScreenshotReceiver(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/upload':
            try:
                # Get content length
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_error(400, "No content")
                    return
                
                # Read raw POST data
                post_data = self.rfile.read(content_length)
                
                # Parse multipart/form-data manually
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    boundary_match = re.search(r'boundary=([A-Za-z0-9\'\(\)\,\.\-_/~]+)', content_type)
                    if boundary_match:
                        boundary = boundary_match.group(1).encode('utf-8')
                        boundary = b'--' + boundary
                        
                        # Split by boundary
                        parts = post_data.split(boundary)
                        for part in parts:
                            if b'filedata' in part and b'name="filedata"' in part:
                                # Extract base64 content between content-disposition and next boundary
                                content_start = part.find(b'\r\n\r\n') + 4
#                                content_end = part.find(b'\r\n--', content_start)
#                                if content_start > 3 and content_end > content_start:
                                content_end = part.find(b'\r\n--', content_start)
                                if content_end == -1:
                                    # fallback: use end of part or last CRLF
                                    content_end = part.rfind(b'\r\n')
                                if content_start > 3 and content_end > content_start:
                                    base64_data = part[content_start:content_end].decode('utf-8').strip()
                                    
                                    print(f"Received base64: {len(base64_data)} characters")
                                    
                                    # Decode base64
                                    image_data = base64.b64decode(base64_data)
                                    print(f"Decoded image: {len(image_data)} bytes")
                                    
                                    # Save file
                                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"screenshot_{timestamp}.bmp"
                                    filepath = os.path.join(UPLOAD_DIR, filename)
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(image_data)
                                    
                                    print(f"Saved: {filepath}")
                                    
                                    # Send success response
                                    self.send_response(200)
                                    self.send_header('Content-type', 'application/json')
                                    self.end_headers()
                                    response = f'{{"success": true, "filename": "{filename}", "size_bytes": {len(image_data)}}}'
                                    self.wfile.write(response.encode('utf-8'))
                                    return
                
                # Fallback: try as URL-encoded form (unlikely for large base64)
                charset = 'utf-8'
                if 'charset=' in content_type:
                    charset_match = re.search(r'charset=([^;\s]+)', content_type)
                    if charset_match:
                        charset = charset_match.group(1)
                
                form_data = parse_qs(post_data.decode(charset))
                if 'filedata' in form_data:
                    base64_data = form_data['filedata'][0]
                    print(f"Received base64: {len(base64_data)} characters")
                    
                    image_data = base64.b64decode(base64_data)
                    print(f"Decoded image: {len(image_data)} bytes")
                    
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.bmp"
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"Saved: {filepath}")
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = f'{{"success": true, "filename": "{filename}", "size_bytes": {len(image_data)}}}'
                    self.wfile.write(response.encode('utf-8'))
                else:
                    print("No 'filedata' field found")
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Missing filedata field"}')
                    
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"error": "{str(e)}"}}'.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print(f"Screenshot receiver running on port {PORT}")
    print(f"POST to http://localhost:{PORT}/upload with 'filedata' field")
    print(f"Screenshots saved to ./{UPLOAD_DIR}/")
    
    with socketserver.TCPServer(("", PORT), ScreenshotReceiver) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    # Check Python version
    import sys
    print(f"Python {sys.version}")
    run_server()
