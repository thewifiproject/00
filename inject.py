import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

if len(sys.argv) != 3:
    print("Usage: python3 injector_proxy.py <url to inject the js file> <js file to inject>")
    sys.exit(1)

TARGET_URL = sys.argv[1]
JS_FILE_PATH = sys.argv[2]

try:
    with open(JS_FILE_PATH, "r", encoding="utf-8") as f:
        OVERLAY_JS = f.read()
except Exception as e:
    print(f"Failed to read JS file '{JS_FILE_PATH}': {e}")
    sys.exit(1)

INJECT_SNIPPET = f"<script>{OVERLAY_JS}</script>"

class InjectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == TARGET_URL or self.path == TARGET_URL.replace("http://", "").replace("https://", ""):
            # Fetch the real content
            try:
                resp = requests.get(TARGET_URL)
                content_type = resp.headers.get("content-type", "")
                content = resp.text
                if "text/html" in content_type:
                    if "</body>" in content:
                        content = content.replace("</body>", f"{INJECT_SNIPPET}</body>")
                    else:
                        content += INJECT_SNIPPET
                    self.send_response(resp.status_code)
                    self.send_header("Content-type", content_type)
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                else:
                    self.send_response(resp.status_code)
                    for k, v in resp.headers.items():
                        self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(resp.content)
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(f"Proxy error: {e}".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run(server_class=HTTPServer, handler_class=InjectHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving proxy on http://127.0.0.1:{port}/ (injecting into {TARGET_URL})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    run()
