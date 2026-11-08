import os
import subprocess
import psutil
import requests
from flask import Flask, render_template, jsonify, request
from git import Repo

app = Flask(__name__)

# --- CONFIGURATION ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE")
GITHUB_USER = "shanejackson485-glitch"
REPO_NAME = "juice-vaultsss" # Change to your actual repo name
BOT_SCRIPT = "bot.py" # Change to your main bot file
BOT_PROCESS = None

# --- SYSTEM STATS ---
@app.route("/api/stats")
def get_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    # Check if bot is running
    bot_running = False
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and BOT_SCRIPT in " ".join(cmdline):
                bot_running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return jsonify({
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "bot_running": bot_running
    })

# --- BOT CONTROLS ---
@app.route("/api/bot/restart", methods=["POST"])
def restart_bot():
    global BOT_PROCESS
    # Kill existing bot
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and BOT_SCRIPT in " ".join(cmdline):
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    # Start new bot
    BOT_PROCESS = subprocess.Popen(["python", BOT_SCRIPT])
    return jsonify({"message": "Bot restarted successfully!"})

@app.route("/api/bot/stop", methods=["POST"])
def stop_bot():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and BOT_SCRIPT in " ".join(cmdline):
                proc.kill()
                return jsonify({"message": "Bot stopped."})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return jsonify({"message": "Bot is not running."})

# --- GITHUB INTEGRATION ---
@app.route("/api/github/pull", methods=["POST"])
def github_pull():
    try:
        repo = Repo(os.getcwd())
        origin = repo.remotes.origin
        origin.pull()
        return jsonify({"message": "Successfully pulled code from GitHub!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route("/api/github/status")
def github_status():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}", headers=headers)
    
    if res.status_code == 200:
        return jsonify({"status": "Connected", "repo": REPO_NAME, "user": GITHUB_USER})
    else:
        return jsonify({"status": "Error", "message": "Invalid Token or Repo"})

# --- FRONTEND ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)