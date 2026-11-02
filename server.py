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

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/')
        
        if not path or path == '':
            self.path = '/index.html'
            return super().do_GET()

        local_path = os.path.join(DIRECTORY, path.lstrip('/'))
        if os.path.exists(local_path) and not os.path.isdir(local_path):
            return super().do_GET()

        html_path = local_path + '.html'
        if os.path.exists(html_path):
            self.path = path + '.html'
            if '?' in self.path:
                self.path += '?' + self.path.split('?')[1]
            return super().do_GET()

        return super().do_GET()

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
