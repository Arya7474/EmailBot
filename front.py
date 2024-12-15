from flask import Flask, request , render_template , jsonify
import pygame
import signal
import sys
import subprocess
import os
import db
# app = Flask(__name__)
app = Flask(
    __name__,
    template_folder="/Users/scorvicsdomain/emailBot/templates",
    static_folder="/Users/scorvicsdomain/emailBot/static",
)

BACKEND_SCRIPT_PATH = "/Users/scorvicsdomain/emailBot/back.py"
PID_FILE = "/Users/scorvicsdomain/emailBot/backend_process.pid"
ERROR_FILE = "/Users/scorvicsdomain/emailBot/error_message.txt"

pygame.mixer.init()

@app.route("/", methods=["GET"])
def home():
    reports = db.fetch_reports()
    return render_template("index.html", reports=reports)

@app.route("/submit_config", methods=["POST"])
def submit_config():
    try:
        email_id = request.form.get("email")
        app_password = request.form.get("app-password")
        mail_to_check = request.form.get("manual-entry", "").strip()

        if not mail_to_check or "," not in mail_to_check:
            return render_template("failure.html", message="Invalid input! Please separate values with commas.")
        mail_to_check = mail_to_check.split(",")
        success = db.add_config(email_id, app_password, mail_to_check) 

        if success:
            return render_template("success.html", status="Configuration updated successfully!")
        else:
            return render_template("failure.html", message="Failed to update configuration in the database.")
    except Exception as e:
        return render_template("failure.html", message=f"An unexpected error occurred: {str(e)}")

@app.route("/start_backend", methods=["POST"])
def start_backend():
    """Start the backend process if not already running."""
    if os.path.exists(PID_FILE):  
        return {"status": "Backend is already running!"}, 400

    process = subprocess.Popen([sys.executable, BACKEND_SCRIPT_PATH])
    
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))

    return {"status": "Backend started!"}, 200

@app.route("/stop_backend", methods=["POST"])
def stop_backend():
    """Stop the backend process."""
    if not os.path.exists(PID_FILE): 
        return {"status": "No backend process running!"}, 400

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM) 
    except ProcessLookupError:
        pass 

    os.remove(PID_FILE)

    return {"status": "Backend stopped!"}, 200

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play(loops=-1)

@app.route("/stop", methods=["POST"])
def stop_alert():
    pygame.mixer.music.stop() 
    return {"status": "Alert stopped!"}, 200

@app.route("/trigger", methods=["POST"])
def trigger_alert():
    play_sound("/Users/scorvicsdomain/emailBot/alert.mp3")  
    return {"status": "Alert playing!"}, 200

# handle the login error from backend
def write_error_to_file(message: str) -> None:
    with open(ERROR_FILE, "w") as f:
        f.write(message)

def read_error_from_file() -> str:
    if os.path.exists(ERROR_FILE):
        with open(ERROR_FILE, "r") as f:
            error_message = f.read().strip()
        os.remove(ERROR_FILE)
        return error_message
    return None

@app.route("/error", methods=["POST", "GET"])
def handle_error():
    """Unified endpoint to handle error storage and retrieval."""
    if request.method == "POST":
        error_message = request.json.get("alert", "IGNORE")
        write_error_to_file(error_message)
        return {"status": "Error received"}, 200

    elif request.method == "GET":
        # print("Received GET request for /error")
        error_message = read_error_from_file()
        if error_message:
            return {"status": "Error available", "message": error_message}, 200
        else:
            return {"status": "No error available", "message": None}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



