from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
import json
import os
import pyautogui
import subprocess
import hashlib

app = Flask(__name__)

CONFIG_FILE = 'config.json'
LOCAL_IP_FILE = 'localip.json'
PASSWORD_FILE = 'password.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

def load_local_ip():
    if os.path.exists(LOCAL_IP_FILE):
        try:
            with open(LOCAL_IP_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get('server_ip', '127.0.0.1')  # Default to localhost if not found
        except json.JSONDecodeError:
            return '127.0.0.1'
    return '127.0.0.1'

def load_password_hash():
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get('password_hash', None)
        except json.JSONDecodeError:
            return None
    return None

def save_password_hash(password_hash):
    with open(PASSWORD_FILE, 'w', encoding='utf-8') as file:
        json.dump({'password_hash': password_hash}, file, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_authorization():
    password_hash = load_password_hash()
    if password_hash:
        logged_in = request.cookies.get('logged_in') == 'true'
        return logged_in
    return True

@app.route('/')
def index():
    password_hash = load_password_hash()
    if password_hash is None:
        # Redirect to password setup page if no password is set
        return redirect(url_for('setup_password'))
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/setup_password')
def setup_password():
    password_hash = load_password_hash()
    if password_hash is not None:
        # Redirect to index if password is already set
        return redirect(url_for('index'))
    return render_template('setup_password.html')
@app.route('/info')
def info():
    return render_template("info.html")
@app.route('/config')
def config_page():
    if not check_authorization():
        return redirect(url_for('index'))  # Redirect to index if not authorized
    config = load_config()
    return render_template('config.html', config=config)

@app.route('/action', methods=['POST'])
def action():
    if not check_authorization():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    action_type = request.form.get('action')
    config = load_config()
    if action_type in config:
        settings = config[action_type]
        if settings.get('type') == 'hotkey':
            if 'hotkey' in settings:
                pyautogui.hotkey(*settings['hotkey'].split('+'))
        elif settings.get('type') == 'command':
            if 'command' in settings:
                subprocess.run(settings['command'], shell=True)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'unknown action'})

@app.route('/save_config', methods=['POST'])
def save_config_route():
    if not check_authorization():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.json
    config = load_config()
    config.update(data)
    save_config(config)
    return jsonify({'status': 'saved'})

@app.route('/delete_button', methods=['POST'])
def delete_button():
    if not check_authorization():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    action_name = request.json.get('action')
    config = load_config()
    if action_name in config:
        del config[action_name]
        save_config(config)
        return jsonify({'status': 'deleted'})
    return jsonify({'status': 'not found'})

@app.route('/set_password', methods=['POST'])
def set_password():
    password = request.json.get('password')
    if password:
        password_hash = hash_password(password)
        save_password_hash(password_hash)
        response = jsonify({'status': 'success'})
        response.set_cookie('logged_in', 'true', max_age=259200)  # Cookie expires in 3 days
        return response
    return jsonify({'status': 'error', 'message': 'Password is required'}), 400

@app.route('/login', methods=['POST'])
def login():
    password = request.json.get('password')
    password_hash = load_password_hash()
    if password_hash and hash_password(password) == password_hash:
        response = jsonify({'status': 'success'})
        response.set_cookie('logged_in', 'true', max_age=259200)  # Cookie expires in 3 days
        return response
    return jsonify({'status': 'error'}), 403

@app.route('/check_login')
def check_login():
    logged_in = request.cookies.get('logged_in') == 'true'
    return jsonify({'logged_in': logged_in})

if __name__ == '__main__':
    server_ip = load_local_ip()
    app.run(host=server_ip, port=5000, debug=False)
