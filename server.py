#!/usr/bin/env python3
"""
Clipeus Virtutis - High-Performance Multi-Threaded Local Server with HTTP Range Support
Serves static assets with intelligent caching, HTTP Range (206 Partial Content) for videos/audio,
and routes clean URLs seamlessly.
"""
import http.server
import socketserver
import os
import sys
import json
import base64
import urllib.parse

# Import unified database layer
import database

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class RangeFileWrapper:
    def __init__(self, f, length):
        self.f = f
        self.remaining = length

    def read(self, size=-1):
        if self.remaining <= 0:
            return b""
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self.f.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        self.f.close()

class HighPerformanceCleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        path = self.path.split('?')[0].lower()
        # In local development, never cache HTML, CSS, or JS so changes update immediately
        if any(path.endswith(ext) for ext in ('.html', '.css', '.js')) or path == '/' or path == '':
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        elif any(path.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.mp4', '.m4a', '.woff2', '.ttf')):
            self.send_header('Cache-Control', 'public, max-age=3600')
        else:
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
        
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            return super().send_head()
        
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        total_len = fs[6]
        
        range_header = self.headers.get('Range')
        if range_header and range_header.startswith('bytes='):
            try:
                ranges = range_header[6:].split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if ranges[1] else total_len - 1
                if start >= total_len:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    f.close()
                    return None
                if end >= total_len:
                    end = total_len - 1
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Range", f"bytes {start}-{end}/{total_len}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                
                f.seek(start)
                return RangeFileWrapper(f, length)
            except Exception:
                pass

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(total_len))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return f

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.end_headers()
        self.wfile.write(body)

    def parse_json(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                raw_data = self.rfile.read(content_length).decode('utf-8')
                return json.loads(raw_data)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
        return {}

    def get_auth_token(self):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:].strip()
        # Fallback check in query string
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if 'token' in params:
            return params['token'][0]
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        query_params = urllib.parse.parse_qs(parsed.query)

        # -------------------------------------------------------------
        # API Routes (GET)
        # -------------------------------------------------------------
        if path == '/api/admin/dashboard':
            token = self.get_auth_token()
            session = database.db.verify_token(token)
            if not session:
                return self.send_json({"success": False, "error": "Unauthorized. Please login."}, 401)
            metrics = database.db.get_dashboard_metrics()
            return self.send_json({"success": True, **metrics})

        elif path == '/api/admin/enquiries':
            token = self.get_auth_token()
            session = database.db.verify_token(token)
            if not session:
                return self.send_json({"success": False, "error": "Unauthorized. Please login."}, 401)
            period = query_params.get('period', ['all'])[0]
            search = query_params.get('search', [''])[0]
            limit = query_params.get('limit', [100])[0]
            enquiries = database.db.get_enquiries(limit=limit, period=period, search=search)
            return self.send_json({"success": True, "enquiries": enquiries})

        elif path == '/api/admin/verify':
            token = self.get_auth_token()
            session = database.db.verify_token(token)
            if session:
                return self.send_json({"success": True, "valid": True, "username": session["username"]})
            return self.send_json({"success": False, "valid": False})

        elif path == '/api/products':
            products = database.db.get_products()
            return self.send_json({"success": True, "products": products})

        elif path == '/admin':
            self.path = '/admin.html'
            return super().do_GET()

        # -------------------------------------------------------------
        # Static & Clean URL Handling
        # -------------------------------------------------------------
        if not path or path == '':
            self.path = '/index.html'
            return super().do_GET()

        local_path = os.path.join(DIRECTORY, path.lstrip('/'))
        if os.path.exists(local_path) and not os.path.isdir(local_path):
            return super().do_GET()

        html_path = local_path + '.html'
        if os.path.exists(html_path):
            self.path = path + '.html'
            if parsed.query:
                self.path += '?' + parsed.query
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')

        # -------------------------------------------------------------
        # API Routes (POST)
        # -------------------------------------------------------------
        if path == '/api/admin/login':
            data = self.parse_json()
            username = data.get('username', '')
            password = data.get('password', '')
            auth = database.db.authenticate(username, password)
            if auth:
                return self.send_json({"success": True, **auth})
            return self.send_json({"success": False, "error": "Invalid laboratory credentials. Please check your username and password."}, 401)

        elif path == '/api/admin/logout':
            data = self.parse_json()
            token = data.get('token') or self.get_auth_token()
            if token:
                database.db.logout(token)
            return self.send_json({"success": True})

        elif path == '/api/enquiries':
            data = self.parse_json()
            enquiry = database.db.create_enquiry(data)
            return self.send_json({
                "success": True,
                "reference_no": enquiry["reference_no"],
                "enquiry": enquiry
            })

        elif path == '/api/admin/enquiries/status':
            token = self.get_auth_token()
            session = database.db.verify_token(token)
            if not session:
                return self.send_json({"success": False, "error": "Unauthorized."}, 401)
            data = self.parse_json()
            enquiry_id = data.get('id') or data.get('reference_no')
            new_status = data.get('status')
            if enquiry_id and new_status:
                database.db.update_enquiry_status(enquiry_id, new_status)
                return self.send_json({"success": True, "id": enquiry_id, "status": new_status})
            return self.send_json({"success": False, "error": "Missing parameters"}, 400)

        elif path == '/api/admin/products':
            token = self.get_auth_token()
            session = database.db.verify_token(token)
            if not session:
                return self.send_json({"success": False, "error": "Unauthorized."}, 401)
            data = self.parse_json()
            
            # Handle uploaded image base64 if present
            image_data = data.get('image_data')
            image_name = data.get('image_name', 'product.png')
            if image_data and ',' in image_data:
                try:
                    header, b64_str = image_data.split(',', 1)
                    ext = '.png'
                    if 'jpeg' in header or 'jpg' in header:
                        ext = '.jpg'
                    elif 'webp' in header:
                        ext = '.webp'
                    
                    safe_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(image_name)}"
                    if not safe_name.endswith(ext):
                        safe_name += ext
                    
                    prod_dir = os.path.join(DIRECTORY, 'assets', 'products')
                    os.makedirs(prod_dir, exist_ok=True)
                    save_path = os.path.join(prod_dir, safe_name)
                    
                    with open(save_path, 'wb') as img_f:
                        img_f.write(base64.b64decode(b64_str))
                    
                    data['image_url'] = f"assets/products/{safe_name}"
                except Exception as img_err:
                    print(f"Error saving image: {img_err}")

            product = database.db.create_product(data)
            return self.send_json({"success": True, "product": product})

        elif path == '/api/admin/products/delete':
            token = self.get_auth_token()
            session = database.db.verify_token(token)
            if not session:
                return self.send_json({"success": False, "error": "Unauthorized."}, 401)
            data = self.parse_json()
            prod_id = data.get('id')
            if prod_id:
                database.db.delete_product(prod_id)
                return self.send_json({"success": True, "id": prod_id})
            return self.send_json({"success": False, "error": "Missing product id"}, 400)

        self.send_error(404, "Endpoint not found")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    with ThreadedTCPServer(("", PORT), HighPerformanceCleanURLHandler) as httpd:
        print(f"🚀 High-Performance Clipeus Virtutis server running on http://localhost:{PORT}")
        sys.stdout.flush()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
